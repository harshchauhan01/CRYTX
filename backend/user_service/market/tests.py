from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APITestCase

from .models import Asset, AssetCategory, Portfolio

@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
class TransactionPriceReactionTests(APITestCase):
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
            total_supply=Decimal("1000.00"),
            available_supply=Decimal("1000.00"),
            buy_volume=Decimal("1000.00"),
            sell_volume=Decimal("1000.00"),
            volatility=0.10,
            is_active=True,
        )

    def test_buy_order_increases_price_and_records_execution_price(self):
        pre_trade_price = self.asset.current_price

        response = self.client.post(
            "/api/market/transactions/",
            {"asset_id": self.asset.id, "quantity": "10", "side": "buy"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.asset.refresh_from_db()
        self.assertGreater(self.asset.current_price, pre_trade_price)
        
        # calculate expected slippage: 1 + (10/1000) = 1.01
        expected_execution_price = pre_trade_price * Decimal("1.01")
        self.assertEqual(Decimal(str(response.data["price"])), expected_execution_price)

    def test_sell_order_decreases_price(self):
        # Simulate more selling pressure
        self.asset.buy_volume = Decimal("800.00")
        self.asset.sell_volume = Decimal("1200.00")
        self.asset.save(update_fields=["buy_volume", "sell_volume"])

        Portfolio.objects.create(
            user=self.user,
            asset=self.asset,
            quantity=Decimal("50.0000"),
            avg_buy_price=self.asset.current_price,
        )

        pre_trade_price = self.asset.current_price

        sell_response = self.client.post(
            "/api/market/transactions/",
            {"asset_id": self.asset.id, "quantity": "10", "side": "sell"},
            format="json",
        )
        self.assertEqual(sell_response.status_code, status.HTTP_201_CREATED)

        self.asset.refresh_from_db()
        self.assertLessEqual(self.asset.current_price, pre_trade_price)
