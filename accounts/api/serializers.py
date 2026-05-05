# serializers.py for accounts api
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

class QuestNestTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # 🟢 Add custom claims for the QuestNest engine
        token['role'] = user.role # e.g., 'tenant', 'landlord'
        token['org_id'] = str(user.organisation.id) if user.organisation else None
        token['email'] = user.email

        return token


User = get_user_model()

class CheckEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'is_verified']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ['email', 'name', 'password', 'role']

    def create(self, validated_data):
        # 🟢 6. Safely extract the role, defaulting to 'tenant' if not provided
        role = validated_data.pop('role', 'tenant')

        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name'],
            role=role  # 🟢 7. Pass the role to the user manager
        )
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'email']

class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()