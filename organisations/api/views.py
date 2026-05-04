from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from drf_spectacular.utils import extend_schema

from organisations.models import Organisation, Membership
from .serializers import OrganisationSerializer, CreateOrganisationSerializer


class MyOrganisationsView(APIView):
    """ GET /api/organisations/ & POST /api/organisations/ """
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="List My Organisations", responses=OrganisationSerializer(many=True))
    def get(self, request):
        organisations = Organisation.objects.filter(
            members__user=request.user,
            members__is_active=True
        ).distinct()

        serializer = OrganisationSerializer(organisations, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(summary="Create Organisation", request=CreateOrganisationSerializer, responses={201: OrganisationSerializer})
    def post(self, request):
        serializer = CreateOrganisationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            # 1. Create the organisation
            organisation = Organisation.objects.create(
                name=serializer.validated_data['name']
            )

            # 2. Immediately make the creator the OWNER
            Membership.objects.create(
                user=request.user,
                organisation=organisation,
                role=Membership.OWNER
            )

        # Return the newly created org (pass the request context so 'my_role' resolves correctly)
        return Response(
            OrganisationSerializer(organisation, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )