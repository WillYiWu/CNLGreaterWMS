from decimal import Decimal
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from goods.models import ListModel as GoodsListModel
from payment.models import FinanceListModel
from staff.models import AccountListModel

from .views import FillInReturnData, get_sku_by_ean


class FillInReturnDataTests(TestCase):
    def setUp(self):
        self.account = AccountListModel.objects.create(
            account_name="Store A",
            openid="tenant-a",
            client_id="client-id",
            client_secret="client-secret",
        )

    def create_goods(self, ean="8712345678901", sku_code="SKU-001", openid="tenant-a"):
        return GoodsListModel.objects.create(
            goods_code=ean,
            sku_code=sku_code,
            goods_desc="Test product",
            goods_supplier="Test supplier",
            goods_weight=1,
            goods_w=1,
            goods_d=1,
            goods_h=1,
            unit_volume=1,
            goods_unit="pcs",
            goods_class="test",
            goods_brand="test",
            goods_color="test",
            goods_shape="test",
            goods_specs="test",
            goods_origin="test",
            safety_stock=0,
            goods_cost=10,
            goods_price=20,
            creater="test",
            bar_code=ean,
            openid=openid,
        )

    def create_finance(self, **overrides):
        values = {
            "dn_code": "ORDER-001",
            "orderitem_id": "ITEM-001",
            "account_name": self.account.account_name,
            "goods_code": "SKU-001",
            "goods_desc": "Test product",
            "shipped_qty": 1,
            "selling_price": Decimal("100.00"),
            "btw_cost": Decimal("17.36"),
            "bol_commission": Decimal("10.00"),
            "logistic_cost": Decimal("5.00"),
            "product_cost": Decimal("40.00"),
            "profit": Decimal("27.64"),
            "openid": self.account.openid,
        }
        values.update(overrides)
        return FinanceListModel.objects.create(**values)

    def return_response(self, ean="8712345678901", order_id="ORDER-001"):
        processing_time = timezone.now().isoformat()
        return Mock(json=Mock(return_value={
            "returns": [{
                "returnItems": [{
                    "orderId": order_id,
                    "ean": ean,
                    "expectedQuantity": 1,
                    "processingResults": [{"processingDateTime": processing_time}],
                }],
            }],
        }))

    @patch("dn.views.obtain_access_token", return_value="token")
    @patch("dn.views.requests.get")
    def test_maps_return_ean_to_finance_sku(self, mock_get, _mock_token):
        self.create_goods()
        original = self.create_finance()
        mock_get.return_value = self.return_response()

        FillInReturnData()

        original.refresh_from_db()
        self.assertTrue(original.returned)
        returned = FinanceListModel.objects.get(orderitem_id="ITEM-0010")
        self.assertEqual(returned.goods_code, "SKU-001")
        self.assertEqual(returned.selling_price, Decimal("-100.00"))
        self.assertTrue(returned.returned)

    @patch("dn.views.obtain_access_token", return_value="token")
    @patch("dn.views.requests.get")
    def test_supports_legacy_finance_rows_that_store_ean(self, mock_get, _mock_token):
        ean = "8712345678901"
        original = self.create_finance(goods_code=ean)
        mock_get.return_value = self.return_response(ean=ean)

        FillInReturnData()

        original.refresh_from_db()
        self.assertTrue(original.returned)
        self.assertTrue(FinanceListModel.objects.filter(orderitem_id="ITEM-0010").exists())

    @patch("dn.views.obtain_access_token", return_value="token")
    @patch("dn.views.requests.get")
    def test_does_not_match_another_account(self, mock_get, _mock_token):
        self.create_goods()
        other = self.create_finance(
            orderitem_id="ITEM-OTHER",
            account_name="Store B",
            openid="tenant-b",
        )
        mock_get.return_value = self.return_response()

        FillInReturnData()

        other.refresh_from_db()
        self.assertFalse(other.returned)
        self.assertEqual(FinanceListModel.objects.count(), 1)

    @patch("dn.views.obtain_access_token", return_value="token")
    @patch("dn.views.requests.get")
    def test_repeated_return_fetch_is_idempotent(self, mock_get, _mock_token):
        self.create_goods()
        original = self.create_finance()
        mock_get.return_value = self.return_response()

        FillInReturnData()
        FillInReturnData()

        original.refresh_from_db()
        self.assertTrue(original.returned)
        self.assertEqual(FinanceListModel.objects.filter(dn_code="ORDER-001").count(), 2)

    @patch("dn.views.obtain_access_token", return_value="token")
    @patch("dn.views.requests.get")
    def test_login_openid_does_not_affect_return_matching(self, mock_get, _mock_token):
        self.create_goods(openid="goods-user")
        original = self.create_finance(openid="order-user")
        mock_get.return_value = self.return_response()

        FillInReturnData()

        original.refresh_from_db()
        self.assertTrue(original.returned)
        returned = FinanceListModel.objects.get(orderitem_id="ITEM-0010")
        self.assertEqual(returned.openid, "order-user")
