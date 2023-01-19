from django_filters import FilterSet
from .models import TransportationFeeListModel, FinanceListModel

class TransportationFeeListFilter(FilterSet):
    class Meta:
        model = TransportationFeeListModel
        fields = {
            "id": ['exact', 'iexact', 'gt', 'gte', 'lt', 'lte', 'isnull', 'in', 'range'],
            "send_city": ['exact', 'iexact', 'contains', 'icontains'],
            "receiver_city": ['exact', 'iexact', 'contains', 'icontains'],
            "weight_fee": ['exact', 'iexact', 'contains', 'icontains', 'gt', 'gte', 'lt', 'lte', 'range'],
            "volume_fee": ['exact', 'iexact', 'contains', 'icontains', 'gt', 'gte', 'lt', 'lte', 'range'],
            "min_payment": ['exact', 'iexact', 'contains', 'icontains', 'gt', 'gte', 'lt', 'lte', 'range'],
            "transportation_supplier": ['exact', 'iexact', 'contains', 'icontains'],
            "creater": ['exact', 'iexact', 'contains', 'icontains'],
            "is_delete": ['exact', 'iexact'],
            "create_time": ['year', 'month', 'day', 'week_day', 'gt', 'gte', 'lt', 'lte', 'range'],
            "update_time": ['year', 'month', 'day', 'week_day', 'gt', 'gte', 'lt', 'lte', 'range']
        }

class FinanceListFilter(FilterSet):
    class Meta:
        model = FinanceListModel
        fields = {
            "dn_code": ['exact', 'iexact', 'gt', 'gte', 'lt', 'lte', 'isnull', 'in', 'range'],
            "orderitem_id": ['exact', 'iexact', 'gt', 'gte', 'lt', 'lte', 'isnull', 'in', 'range'],
            "goods_code": ['exact', 'iexact', 'gt', 'gte', 'lt', 'lte', 'isnull', 'in', 'range'],
            "goods_desc": ['exact', 'iexact', 'contains', 'icontains'],
            "shipped_qty": ['exact', 'iexact', 'contains', 'icontains', 'gt', 'gte', 'lt', 'lte', 'range'],
            "selling_price": ['exact', 'iexact', 'contains', 'icontains', 'gt', 'gte', 'lt', 'lte', 'range'],
            "btw_cost": ['exact', 'iexact', 'contains', 'icontains', 'gt', 'gte', 'lt', 'lte', 'range'],
            "bol_commission": ['exact', 'iexact', 'contains', 'icontains', 'gt', 'gte', 'lt', 'lte', 'range'],
            "logistic_cost": ['exact', 'iexact', 'contains', 'icontains', 'gt', 'gte', 'lt', 'lte', 'range'],
            "product_cost": ['exact', 'iexact', 'contains', 'icontains', 'gt', 'gte', 'lt', 'lte', 'range'],
            "selling_date": ['year', 'month', 'day', 'week_day', 'gt', 'gte', 'lt', 'lte', 'range'],
            "create_time": ['year', 'month', 'day', 'week_day', 'gt', 'gte', 'lt', 'lte', 'range'],
            "is_delete": ['exact', 'iexact']
        }
