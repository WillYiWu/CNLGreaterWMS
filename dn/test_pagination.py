from urllib.parse import parse_qs, urlparse

from django.test import SimpleTestCase
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from .page import OutboundPagination, MyPageNumberPaginationDNList


class OutboundPaginationTests(SimpleTestCase):
    def test_default_and_requested_page_sizes_never_exceed_120(self):
        for paginator_class in (OutboundPagination, MyPageNumberPaginationDNList):
            for query, expected in (('', 120), ('?max_page=1000', 120),
                                    ('?max_page=0', 120), ('?max_page=50', 50)):
                with self.subTest(paginator=paginator_class.__name__, query=query):
                    request = Request(APIRequestFactory().get('/dn/list/' + query))
                    page = paginator_class().paginate_queryset(list(range(241)), request)
                    self.assertEqual(len(page), expected)

    def test_next_pages_retain_all_rows_without_gaps(self):
        for paginator_class in (OutboundPagination, MyPageNumberPaginationDNList):
            seen = []
            url = '/dn/list/'
            while url:
                request = Request(APIRequestFactory().get(url, HTTP_ORIGIN='http://testserver'))
                paginator = paginator_class()
                seen.extend(paginator.paginate_queryset(list(range(241)), request))
                url = paginator.get_next_link()
                if url:
                    self.assertIn('page', parse_qs(urlparse(url).query))
            self.assertEqual(seen, list(range(241)))
