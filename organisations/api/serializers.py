from rest_framework import serializers
from organisations.models import Organisation, Membership


class OrganisationSerializer(serializers.ModelSerializer):
    # We use a SerializerMethodField to inject the user's specific role into the response
    my_role = serializers.SerializerMethodField()

    class Meta:
        model = Organisation
        fields = ['id', 'name', 'is_verified', 'verified', 'my_role']

    def get_my_role(self, obj):
        # The view will pass the request context so we can check the logged-in user
        user = self.context['request'].user
        membership = obj.members.filter(user=user, is_active=True).first()
        return membership.role if membership else None


class CreateOrganisationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)