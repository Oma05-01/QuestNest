import requests
from django.conf import settings


class PaystackService:
    BASE_URL = "https://api.paystack.co"
    SECRET_KEY = settings.PAYSTACK_SECRET_KEY

    @classmethod
    def _get_headers(cls):
        return {
            "Authorization": f"Bearer {cls.SECRET_KEY}",
            "Content-Type": "application/json",
        }

    @classmethod
    def initialize_payment(cls, email, amount_naira, reference, metadata=None):
        url = f"{cls.BASE_URL}/transaction/initialize"

        # 🟢 Use settings for the frontend URL so it works locally and in prod!
        frontend_base = getattr(settings, 'FRONTEND_URL', 'https://questnest.com')

        payload = {
            "email": email,
            "amount": int(amount_naira * 100),
            "reference": reference,
            "metadata": metadata or {},
            "callback_url": f"{frontend_base}/dashboard/payment-success/",
        }

        response = requests.post(url, json=payload, headers=cls._get_headers())
        return response.json()

    @classmethod
    def verify_payment(cls, reference):
        url = f"{cls.BASE_URL}/transaction/verify/{reference}"
        response = requests.get(url, headers=cls._get_headers())
        return response.json()