from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.api.permissions import IsTenant
from rentals.models import Tenancy
from .serializers import TenancySerializer

class MyTenanciesView(APIView):
    """
    GET /api/tenancies/me/
    """
    permission_classes = [IsAuthenticated, IsTenant]

    def get(self, request):
        # Only fetch tenancies belonging to the logged-in tenant
        tenancies = Tenancy.objects.filter(tenant=request.user).select_related('unit', 'unit__asset')
        serializer = TenancySerializer(tenancies, many=True)
        return Response(serializer.data)