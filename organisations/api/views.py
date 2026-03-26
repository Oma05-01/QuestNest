from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from organisations.models import Organisation
from .serializers import OrganisationSerializer


class MyOrganisationsView(APIView):
    """ GET /api/organisations/ """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch all organisations where this user has an active membership
        organisations = Organisation.objects.filter(
            members__user=request.user,
            members__is_active=True
        ).distinct()

        serializer = OrganisationSerializer(organisations, many=True, context={'request': request})
        return Response(serializer.data)