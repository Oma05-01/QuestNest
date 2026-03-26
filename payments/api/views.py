from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from core.api.permissions import IsTenant
from payments.services.payment_service import pay_rent
from .serializers import PayRentSerializer

class PayRentView(APIView):
    """
    POST /api/payments/pay-rent/
    """
    permission_classes = [IsAuthenticated, IsTenant]

    def post(self, request):
        # 1. Validate incoming data (Serializer)
        serializer = PayRentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # 2. Execute business logic (Service Layer)
        payment = pay_rent(
            tenant=request.user,
            tenancy=serializer.validated_data['tenancy'],
            amount=serializer.validated_data['amount']
        )

        # 3. Return response (Thin View)
        return Response(
            {
                "message": "Payment initiated successfully.", 
                "payment_reference": payment.reference,
                "status": payment.status
            },
            status=status.HTTP_201_CREATED
        )