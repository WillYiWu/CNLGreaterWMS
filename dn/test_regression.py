"""Deterministic shipping-label regression data; no real orders or credentials."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import requests
from django.test import RequestFactory, TestCase
from .models import DnDetailModel, PickingListModel
from .views import ShippinglabelViewSet, find_shipping_label_record

DATA = json.loads((Path(__file__).resolve().parents[1] /
                   'tests/fixtures/shipping_labels.json').read_text())


class ShippingRegressionTests(TestCase):
    def setUp(self):
        self.values = DATA['primary'].copy()
        self.code = self.values['account_name'] + self.values['dn_code']
        self.record = DnDetailModel.objects.create(**self.values)
        self.previous = os.getcwd()
        self.directory = TemporaryDirectory()
        os.chdir(self.directory.name)
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(os.chdir, self.previous)

    def download(self, query=None, **headers):
        request = RequestFactory().get('/dn/shippinglabel/' + self.code + '/', query or {}, **headers)
        return ShippinglabelViewSet.as_view()(request, dn_code=self.code)

    def test_exact_account_prefix_required(self):
        for code in ('OtherStore' + self.values['dn_code'], self.code + 'X', self.code[:-1]):
            self.assertIsNone(find_shipping_label_record(code))

    def test_detail_precedes_picking(self):
        PickingListModel.objects.create(**self.values)
        self.assertEqual(find_shipping_label_record(self.code), self.record)

    def test_deleted_detail_falls_back_to_active_picking(self):
        self.record.is_delete = True
        self.record.save()
        expected = PickingListModel.objects.create(**self.values)
        self.assertEqual(find_shipping_label_record(self.code), expected)

    def test_old_order_fixture_survives_recent_record_limit(self):
        DnDetailModel.objects.bulk_create([
            DnDetailModel(dn_code='REG-NEW-' + str(i), orderitem_id='new-' + str(i), label_id='new')
            for i in range(DATA['newer_record_count'])])
        self.assertEqual(find_shipping_label_record(self.code), self.record)

    @patch('dn.views.requests.get')
    @patch('dn.views.obtain_access_token')
    def test_query_openid_excludes_other_tenant(self, token, get):
        self.assertEqual(self.download({'openid': DATA['other_tenant']}).status_code, 404)
        token.assert_not_called()
        get.assert_not_called()

    @patch('dn.views.requests.get')
    @patch('dn.views.obtain_access_token')
    def test_header_takes_precedence_over_query(self, token, get):
        response = self.download({'openid': self.values['openid']}, HTTP_TOKEN=DATA['other_tenant'])
        self.assertEqual(response.status_code, 404)
        token.assert_not_called()

    @patch('dn.views.obtain_access_token', return_value='fake-token')
    @patch('dn.views.requests.get')
    def test_upstream_errors_do_not_create_cache(self, get, token):
        for status in DATA['upstream_errors']:
            with self.subTest(status=status):
                get.return_value = Mock(status_code=status, content=b'error', headers={})
                self.assertEqual(self.download().status_code, 404)
                self.assertFalse(Path(self.code + '.pdf').exists())

    @patch('dn.views.obtain_access_token', return_value='fake-token')
    @patch('dn.views.requests.get')
    def test_non_pdf_response_is_not_cached(self, get, token):
        get.return_value = Mock(status_code=200, content=b'{}', headers={'content-type': 'application/json'})
        self.assertEqual(self.download().status_code, 404)
        self.assertFalse(Path(self.code + '.pdf').exists())

    @patch('dn.views.obtain_access_token', return_value='fake-token')
    @patch('dn.views.requests.get', side_effect=requests.Timeout('simulated'))
    def test_timeout_returns_404_without_cache(self, get, token):
        self.assertEqual(self.download().status_code, 404)
        self.assertFalse(Path(self.code + '.pdf').exists())

    @patch('dn.views.obtain_access_token', side_effect=RuntimeError('simulated'))
    @patch('dn.views.requests.get')
    def test_token_failure_does_not_download(self, get, token):
        self.assertEqual(self.download().status_code, 404)
        get.assert_not_called()
