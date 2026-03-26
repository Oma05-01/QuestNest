from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404

from organisations.models import Organisation
from assets.models import Assets
from core.api.permissions import IsLandlordOrAdmin  # Assuming only landlords/admins verify things
from verification.services.verification_service import (
    submit_organisation_verification,
    submit_property_verification
)
from .serializers import SubmitVerificationSerializer


class SubmitVerificationView(APIView):
    """ POST /api/verification/submit/ """
    permission_classes = [IsAuthenticated, IsLandlordOrAdmin]

    # CRITICAL: These parsers tell Django to accept file uploads (form-data) instead of JSON
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = SubmitVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_type = serializer.validated_data['target_type']
        target_id = serializer.validated_data['target_id']
        documents = serializer.validated_data['documents']

        if target_type == 'organisation':
            org = get_object_or_404(Organisation, id=target_id, members__user=request.user)
            submit_organisation_verification(
                organisation=org,
                document_file=documents[0],  # Org verification only takes 1 file in your model
                submitter=request.user
            )
            return Response({"message": "Organisation documents submitted for review."})

        elif target_type == 'property':
            asset = get_object_or_404(Assets, id=target_id, owner=request.user)
            submit_property_verification(
                asset=asset,
                document_files=documents,  # Property verification takes multiple files
                submitter=request.user
            )
            return Response({"message": "Property documents submitted for review."})