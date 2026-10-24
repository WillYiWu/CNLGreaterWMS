import os
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from django.test import RequestFactory, TestCase

from .models import DnDetailModel, PickingListModel
from .views import ShippinglabelViewSet, find_shipping_label_record


class ShippingLabelLookupTests(TestCase):
    def create_record(self, model=DnDetailModel, **overrides):
        values = dict(openid='tenant-a', account_name='CNLSight',
                      dn_code='C000JFJT06', orderitem_id='item-a', label_id='label-a')
        values.update(overrides)
        return model.objects.create(**values)

    def test_prefixed_detail_older_than_200_records(self):
        expected = self.create_record()
        DnDetailModel.objects.bulk_create([
            DnDetailModel(orderitem_id=str(i), dn_code=str(i), label_id='other')
            for i in range(201)
        ])
        self.assertEqual(find_shipping_label_record('CNLSightC000JFJT06', 'tenant-a'), expected)

    def test_prefixed_picking_record_older_than_200_records(self):
        expected = self.create_record(PickingListModel)
        PickingListModel.objects.bulk_create([
            PickingListModel(dn_code=str(i), label_id='other') for i in range(201)
        ])
        self.assertEqual(find_shipping_label_record('CNLSightC000JFJT06'), expected)

    def test_bare_order_and_orderitem_remain_supported(self):
        expected = self.create_record()
        for code in ('C000JFJT06', 'item-a'):
            self.assertEqual(find_shipping_label_record(code, 'tenant-a'), expected)

    def test_other_tenant_and_deleted_records_are_excluded(self):
        self.create_record(openid='tenant-b')
        self.create_record(orderitem_id='deleted', is_delete=True)
        self.assertIsNone(find_shipping_label_record('CNLSightC000JFJT06', 'tenant-a'))

    def test_detail_without_label_falls_back_to_picking(self):
        self.create_record(label_id='')
        expected = self.create_record(PickingListModel)
        self.assertEqual(find_shipping_label_record('CNLSightC000JFJT06', 'tenant-a'), expected)

    @patch('dn.views.obtain_access_token', return_value='mock-token')
    @patch('dn.views.requests.get')
    def test_download_fetches_and_caches_pdf(self, get, token):
        self.create_record()
        get.return_value = Mock(status_code=200, content=b'%PDF-test', headers={
            'content-type': 'application/vnd.retailer.v10+pdf'
        })
        request = RequestFactory().get('/dn/shippinglabel/CNLSightC000JFJT06/', HTTP_TOKEN='tenant-a')
        previous = os.getcwd()
        with TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                for code in ('CNLSightC000JFJT06', 'CNLSightC000JFJT06.pdf'):
                    response = ShippinglabelViewSet.as_view()(request, dn_code=code)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(b''.join(response.streaming_content), b'%PDF-test')
                    response.close()
                get.assert_called_once()
                token.assert_called_once_with('CNLSight', 'tenant-a')
            finally:
                os.chdir(previous)
