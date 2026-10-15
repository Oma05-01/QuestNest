from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.db import transaction
from workspaces.models import Workspace, Membership # 🟢 Added to handle auto-workspace creation

User = get_user_model()

class QuestNestTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # 🟢 CHANGED: The token is strictly for Human Identity now!
        # No more roles or org_ids here. The Workspace Middleware handles that.
        token['email'] = user.email
        token['name'] = user.name

        return token


class CheckEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # 🟢 CHANGED: Removed 'role' since it no longer exists on the User model
        fields = ['id', 'email', 'name', 'is_verified']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        # 🟢 CHANGED: Removed 'role' from fields
        fields = ['email', 'name', 'password']

    def create(self, validated_data):
        # 🟢 ADDED: We use an atomic transaction so if one part fails, it all rolls back
        with transaction.atomic():
            # 1. Create the Human Identity
            user = User.objects.create_user(
                email=validated_data['email'],
                password=validated_data['password'],
                name=validated_data['name']
            )

            # 2. Automatically generate their Personal Workspace
            workspace = Workspace.objects.create(
                name=f"{user.name.split()[0]}'s Personal Workspace", # e.g., "John's Personal Workspace"
                workspace_type=Workspace.PERSONAL
            )

            # 3. Make them the Owner of their new Personal Workspace
            Membership.objects.create(
                user=user,
                workspace=workspace,
                role=Membership.OWNER
            )

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'email']


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()