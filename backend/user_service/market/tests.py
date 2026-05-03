from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APITestCase

from .models import Asset, AssetCategory, Holding


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
class OrderPriceReactionTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="price_tester",
            email="price_tester@example.com",
            password="Pass1234!",
            balance=Decimal("50000.00"),
        )

        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        self.category = AssetCategory.objects.create(name="Test Category")
        self.asset = Asset.objects.create(
            name="Test Asset",
            category=self.category,
            base_price=Decimal("100.00"),
            current_price=Decimal("100.00"),
            supply=1000,
            demand=1000,
            volatility=0.10,
            is_active=True,
        )

    def test_buy_order_increases_price_and_records_execution_price(self):
        pre_trade_price = self.asset.current_price

        response = self.client.post(
            "/api/market/orders/",
            {"asset_id": self.asset.id, "quantity": "10", "side": "buy"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.asset.refresh_from_db()
        self.assertGreater(self.asset.current_price, pre_trade_price)
        self.assertEqual(Decimal(str(response.data["price"])), pre_trade_price)

    def test_sell_order_decreases_price(self):
        # Put the market into an oversupply state, then sell more.
        self.asset.supply = 1200
        self.asset.demand = 800
        self.asset.save(update_fields=["supply", "demand"])

        Holding.objects.create(
            user=self.user,
            asset=self.asset,
            quantity=Decimal("50.0000"),
            avg_price=self.asset.current_price,
        )

        pre_trade_price = self.asset.current_price

        sell_response = self.client.post(
            "/api/market/orders/",
            {"asset_id": self.asset.id, "quantity": "10", "side": "sell"},
            format="json",
        )
        self.assertEqual(sell_response.status_code, status.HTTP_201_CREATED)

        self.asset.refresh_from_db()
        self.assertLess(self.asset.current_price, pre_trade_price)
