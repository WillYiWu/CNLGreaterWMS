from rest_framework import viewsets
from asn.models import AsnDetailModel
from dn.models import DnDetailModel
from payment.models import FinanceListModel
from asn import serializers as asnserializers
from dn import serializers as dnserializers
from utils.page import MyPageNumberPagination
from utils.datasolve import sumOfList
from utils.fbmsg import FBMsg
from utils.md5 import Md5
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from asn.filter import AsnDetailFilter
from dn.filter import DnDetailFilter
from payment.filter import FinanceListFilter
from rest_framework.exceptions import APIException
from django.shortcuts import render
from dateutil.relativedelta import relativedelta
from django.db.models.functions import TruncMonth,TruncYear,ExtractDay,ExtractMonth,ExtractYear
from django.db.models import Count
from django.db import connection
from django.db.models import Q
from django.db.models import Sum
import re
from django.utils import timezone

class ReceiptsViewSet(viewsets.ModelViewSet):
    """
        list:
            Response a data list（all）
    """
    pagination_class = None
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = AsnDetailFilter

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_queryset(self):
        id = self.get_project()
        if self.request.user:
            if id is None:
                return AsnDetailModel.objects.filter(openid=self.request.auth.openid, asn_status__gte=4,
                                                     create_time__gte=timezone.now().date() - relativedelta(days=14),
                                                     is_delete=False)
            else:
                return AsnDetailModel.objects.filter(openid=self.request.auth.openid, asn_status__gte=4,
                                                     create_time__gte=timezone.now().date() - relativedelta(days=14),
                                                     id=id, is_delete=False)
        else:
            return AsnDetailModel.objects.none()

    def get_serializer_class(self):
        if self.action in ['list']:
            return asnserializers.ASNDetailGetSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def notice_lang(self):
        lang = self.request.META.get('HTTP_LANGUAGE')
        return lang

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        context = {}
        dataset = {}
        dimensions = ['product']
        source = []
        series = []
        bar_charts = {
            "type": 'bar',
            "barWidth": '4%',
            "barGap": '60%',
            "barCategoryGap": '10%',
            "itemStyle": {
              "normal": {
                "label": {
                  "show": "true",
                  "position": "top"
                }
              }
            }
          }
        receipt_res = qs.annotate(month=ExtractMonth('create_time'), day=ExtractDay('create_time')) \
            .values('month', 'day').order_by('month', 'day').annotate(number=Sum('goods_cost'))
        # qty_res = qs.values('goods_code').order_by('goods_code').annotate(number=Sum('goods_qty'))
        # rank_res = qs.values('goods_code').order_by('goods_code').annotate(number=Sum('goods_cost'))
        receipt_res_dict = {
        }
        # qty_res_dict = {
        # }
        # rank_res_dict = {
        # }
        for i in receipt_res:
            series.append(bar_charts)
            dimensions.append("%s-%s" % (i['month'], i['day']))
            receipt_res_dict.update({"%s-%s" % (i['month'], i['day']): round(i['number'], 2)})
        # for i in qty_res:
        #     qty_res_dict.update({i['goods_code']: i['number']})
        # for i in rank_res:
        #     rank_res_dict.update({i['goods_code']: i['number']})
        source.append(receipt_res_dict)
        # data_list.append(qty_res_dict)
        # data_list.append(rank_res_dict)
        dataset['source'] = source
        dataset['dimensions'] = dimensions
        context['dataset'] = dataset
        context['series'] = series
        return Response(context)

class SalesViewSet(viewsets.ModelViewSet):
    """
        list:
            Response a data list（all）
    """
    pagination_class = None
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = FinanceListFilter

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_queryset(self):
        #id = self.get_project()
        type = self.kwargs.get('type', None)
        if self.request.user:
            if type == "Monthly":
                return FinanceListModel.objects.filter(selling_date__gte=timezone.now().date() - relativedelta(days=365),
                                                    is_delete=False)
            else:
                return FinanceListModel.objects.filter(selling_date__gte=timezone.now().date() - relativedelta(days=12),
                                                    is_delete=False)
        else:
            return FinanceListModel.objects.none()

    def get_serializer_class(self):
        if self.action in ['list']:
            return dnserializers.DNDetailGetSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def notice_lang(self):
        lang = self.request.META.get('HTTP_LANGUAGE')
        return lang

    def list(self, request, *args, **kwargs):
        type = self.kwargs.get('type', None)
        qs = self.get_queryset()
        context = {}
        dataset = {}
        dimensions = ['product']
        source = []
        series = []
        bar_charts = {
            "type": 'bar',
            "barWidth": '4%',
            "barGap": '60%',
            "barCategoryGap": '10%',
            "itemStyle": {
              "normal": {
                "label": {
                  "show": "true",
                  "position": "top"
                }
              }
            }
          }
        if type == "Monthly":
            receipt_res = qs.annotate(year=ExtractYear('selling_date'), month=ExtractMonth('selling_date')) \
            .values('year', 'month').order_by('year', 'month').annotate(product_cost=Sum('product_cost'),
                                                                        logistic_cost=Sum('logistic_cost'),
                                                                        bol_commission=Sum('bol_commission'),
                                                                        btw_cost=Sum('btw_cost'),
                                                                        profit=Sum('profit'))
        else:
            receipt_res = qs.annotate(year=ExtractYear('selling_date'),
                                      month=ExtractMonth('selling_date'),
                                      day=ExtractDay('selling_date')) \
            .values('year', 'month', 'day').order_by('year', 'month', 'day').annotate(product_cost=Sum('product_cost'),
                                                                        logistic_cost=Sum('logistic_cost'),
                                                                        bol_commission=Sum('bol_commission'),
                                                                        btw_cost=Sum('btw_cost'),
                                                                        profit=Sum('profit'))
        first_column = ''
        second_column = ''
        if type == "Monthly":
            first_column = 'year'
            second_column = 'month'
        else:
            first_column = 'month'
            second_column = 'day'
        data = {
            'yAxis': [str(dat[first_column])+'.'+str(dat[second_column]) for dat in receipt_res],
            'series':[
                {
                    "name": '产品成本',
                    "type": 'bar',
                    "stack": 'total',
                    "label": {
                        "show": "true"
                    },
                    "emphasis": {
                        "focus": 'series'
                    },
                    "data": [round(dat['product_cost'],2) for dat in receipt_res]
                },
                {
                    "name": '物流成本',
                    "type": 'bar',
                    "stack": 'total',
                    "label": {
                        "show": "true"
                    },
                    "emphasis": {
                        "focus": 'series'
                    },
                    "data": [round(dat['logistic_cost'],2) for dat in receipt_res]
                },
                {
                    "name": 'BOL费用',
                    "type": 'bar',
                    "stack": 'total',
                    "label": {
                        "show": "true"
                    },
                    "emphasis": {
                        "focus": 'series'
                    },
                    "data": [round(dat['bol_commission'],2) for dat in receipt_res]
                },
                {
                    "name": '增值税',
                    "type": 'bar',
                    "stack": 'total',
                    "label": {
                        "show": "true"
                    },
                    "emphasis": {
                        "focus": 'series'
                    },
                    "data": [round(dat['btw_cost'],2) for dat in receipt_res]
                },
                {
                    "name": '毛利',
                    "type": 'bar',
                    "stack": 'total',
                    "label": {
                        "show": "true"
                    },
                    "emphasis": {
                        "focus": 'series'
                    },
                    "data": [round(dat['profit'],2) for dat in receipt_res]
                }
            ]
        }


        return Response(data)
