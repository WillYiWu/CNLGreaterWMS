from datetime import datetime, timezone
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from goods.models import ListModel as GoodsListModel
from userprofile.models import Users

from .models import DnDetailModel
from .serializers import DNDetailGetSerializer


class DNDetailGoodsIsolationTests(TestCase):
    ean = "9331774394226"

    def create_goods(self, openid="tenant-a", sku_code="SKU-A", **overrides):
        values = dict(
            openid=openid,
            goods_code=self.ean,
            sku_code=sku_code,
            goods_desc="Description " + sku_code,
        )
        values.update(overrides)
        return GoodsListModel.objects.create(**values)

    def serialize(self, openid="tenant-a"):
        detail = DnDetailModel(
            openid=openid, goods_code=self.ean, dn_code="ORDER-001"
        )
        return DNDetailGetSerializer(detail).data

    def assert_goods(self, data, sku_code, description):
        self.assertEqual(data["sku_code"], sku_code)
        self.assertEqual(data["sku_desc"], description)

    def test_same_ean_in_two_tenants_returns_each_tenants_goods(self):
        self.create_goods()
        self.create_goods(openid="tenant-b", sku_code="SKU-B")

        self.assert_goods(self.serialize(), "SKU-A", "Description SKU-A")
        self.assert_goods(self.serialize("tenant-b"), "SKU-B", "Description SKU-B")

    def test_other_tenants_goods_are_not_used_as_fallback(self):
        self.create_goods(openid="tenant-b", sku_code="SKU-B")

        self.assert_goods(self.serialize(), "", "")

    def test_missing_goods_returns_empty_fields(self):
        self.assert_goods(self.serialize(), "", "")

    def test_deleted_goods_are_ignored(self):
        self.create_goods(is_delete=True)

        self.assert_goods(self.serialize(), "", "")

    def test_deleted_duplicate_does_not_override_active_goods(self):
        self.create_goods()
        self.create_goods(sku_code="DELETED", is_delete=True)

        self.assert_goods(self.serialize(), "SKU-A", "Description SKU-A")

    def test_legacy_duplicates_use_latest_active_goods_in_same_tenant(self):
        self.create_goods(sku_code="OLD")
        self.create_goods(sku_code="LATEST")
        self.create_goods(openid="tenant-b", sku_code="OTHER")

        self.assert_goods(self.serialize(), "LATEST", "Description LATEST")

    def test_list_serialization_keeps_tenants_separate(self):
        self.create_goods()
        self.create_goods(openid="tenant-b", sku_code="SKU-B")
        details = [
            DnDetailModel(openid=tenant, goods_code=self.ean)
            for tenant in ("tenant-a", "tenant-b", "tenant-a")
        ]

        data = DNDetailGetSerializer(details, many=True).data

        self.assertEqual([row["sku_code"] for row in data], ["SKU-A", "SKU-B", "SKU-A"])
        self.assertEqual(
            [row["sku_desc"] for row in data],
            ["Description SKU-A", "Description SKU-B", "Description SKU-A"],
        )

    @patch("dn.views.current_ship_date", "2026-09-28")
    def test_order_detail_endpoint_returns_200_with_shared_ean(self):
        for tenant, sku_code in (("tenant-a", "SKU-A"), ("tenant-b", "SKU-B")):
            Users.objects.create(name=tenant, openid=tenant)
            self.create_goods(openid=tenant, sku_code=sku_code)
            DnDetailModel.objects.create(
                openid=tenant,
                dn_code="ORDER-001",
                orderitem_id=tenant,
                goods_code=self.ean,
                sending_date=datetime(2026, 9, 27, tzinfo=timezone.utc),
            )

        client = APIClient()
        for tenant, sku_code in (("tenant-a", "SKU-A"), ("tenant-b", "SKU-B")):
            response = client.get(
                "/dn/detail/ORDER-001/",
                {"dn_complete": 2, "dn_status": 1},
                HTTP_TOKEN=tenant,
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["count"], 1)
            self.assert_goods(response.data["results"][0], sku_code, "Description " + sku_code)
