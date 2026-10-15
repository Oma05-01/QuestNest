from django.conf import settings
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import (
    CheckEmailSerializer, LoginSerializer, RegisterSerializer,
    UserSerializer, UserUpdateSerializer, QuestNestTokenSerializer, ResendVerificationSerializer
)
from operations.services.event_service import log_event
from operations.constants import EventType
from django.contrib.auth import get_user_model

User = get_user_model()


class CheckEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Check if Email Exists",
        request=CheckEmailSerializer,
        responses={200: inline_serializer(name='EmailCheckResponse', fields={'exists': serializers.BooleanField()})}
    )
    def post(self, request):
        serializer = CheckEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].lower()

        exists = User.objects.filter(email=email).exists()
        return Response({"exists": exists})


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="User Login",
        request=LoginSerializer,
        responses={
            200: inline_serializer(
                name='LoginResponse',
                fields={
                    'access': serializers.CharField(),
                    'refresh': serializers.CharField(),
                    'user': UserSerializer()
                }
            )
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            email=serializer.validated_data['email'].lower(),
            password=serializer.validated_data['password']
        )

        if not user:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_verified:
            return Response(
                {"detail": "Please verify your email address before logging in."},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh = QuestNestTokenSerializer.get_token(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data
        })


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Register New User",
        request=RegisterSerializer,
        responses={201: inline_serializer(name='RegisterResponse', fields={'message': serializers.CharField()})}
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save() # 🟢 This now auto-creates the Personal Workspace!

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        verification_link = f"{frontend_url}/verify/{uid}/{token}"

        send_mail(
            subject="Verify your QuestNest account",
            message=f"Welcome to QuestNest! Click the link below to verify your email:\n\n{verification_link}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
        )

        return Response({"message": "Account created. Please verify your email."}, status=status.HTTP_201_CREATED)


class UserUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Update User Profile",
        request=UserUpdateSerializer,
        responses={200: UserSerializer}
    )
    def patch(self, request):
        user = request.user
        old_values = {"name": user.name, "email": user.email}

        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()

        changes = {
            field: {"old": old_val, "new": getattr(updated_user, field)}
            for field, old_val in old_values.items()
            if old_val != getattr(updated_user, field)
        }

        if changes:
            log_event(
                # 🟢 CHANGED: Replaced organisation with workspace
                workspace=getattr(request, 'workspace', None),
                actor=request.user,
                event_type=EventType.USER_UPDATED,
                object_type="User",
                object_id=str(updated_user.id),
                metadata={"changes": changes}
            )

        return Response(UserSerializer(updated_user).data)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Verify Email Address",
        responses={
            200: inline_serializer(name='VerifySuccess', fields={'message': serializers.CharField()}),
            400: inline_serializer(name='VerifyError', fields={'detail': serializers.CharField()})
        }
    )
    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = get_object_or_404(User, pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            user.is_verified = True
            user.save()
            return Response({"message": "Email successfully verified."}, status=status.HTTP_200_OK)

        return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Resend Verification Email",
        request=ResendVerificationSerializer,
        responses={
            200: inline_serializer(name='ResendResponse', fields={'message': serializers.CharField()}),
            400: inline_serializer(name='ResendError', fields={'detail': serializers.CharField()})
        }
    )
    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].lower()

        user = User.objects.filter(email=email).first()

        if not user:
            return Response(
                {"message": "If an account with that email exists, a verification link has been sent."},
                status=status.HTTP_200_OK
            )

        if user.is_verified:
            return Response(
                {"detail": "This account is already verified. Please log in."},
                status=status.HTTP_400_BAD_REQUEST
            )

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        verification_link = f"{frontend_url}/verify/{uid}/{token}"

        send_mail(
            subject="Verify your QuestNest account",
            message=f"Welcome to QuestNest! Click the link below to verify your email:\n\n{verification_link}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
        )

        return Response(
            {"message": "If an account with that email exists, a verification link has been sent."},
            status=status.HTTP_200_OK
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="User Logout",
        description="Invalidates and blacklists the provided JWT refresh token.",
        request=inline_serializer(
            name='LogoutRequest',
            fields={
                'refresh': serializers.CharField(help_text="The refresh token to blacklist")
            }
        ),
        responses={
            200: inline_serializer(
                name='LogoutSuccess',
                fields={'message': serializers.CharField()}
            ),
            400: inline_serializer(
                name='LogoutError',
                fields={'detail': serializers.CharField()}
            )
        }
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"message": "Successfully logged out."},
                status=status.HTTP_200_OK
            )
        except TokenError:
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST
            )