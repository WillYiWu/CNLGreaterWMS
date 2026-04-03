from django_filters import FilterSet
from .models import ListModel, SkuModel

class Filter(FilterSet):
    class Meta:
        model = ListModel
        fields = {
            "id": ['exact', 'iexact', 'gt', 'gte', 'lt', 'lte', 'isnull', 'in', 'range'],
            "goods_code": ['exact', 'iexact', 'contains', 'icontains'],
            "goods_desc": ['exact', 'iexact', 'contains', 'icontains'],
            "goods_supplier": ['exact', 'iexact', 'contains', 'icontains'],
            "goods_weight": ['exact', 'iexact', 'gt', 'gte', 'lt', 'lte', 'isnull', 'in', 'range'],
            "goods_w": ['exact', 'iexact', 'gt', 'gte', 'lt', 'lte', 'isnull', 'in', 'range'],
            "goods_d": ['exact', 'iexact', 'gt', 'gte', 'lt', 'lte', 'isnull', 'in', 'range'],
            "goods_h": ['exact', 'iexact', 'gt', 'gte', 'lt', 'lte', 'isnull', 'in', 'range'],
            "unit_volume": ['exact', 'iexact', 'gt', 'gte', 'lt', 'lte', 'isnull', 'in', 'range'],
            "goods_unit": ['exact', 'iexact', 'contains', 'icontains'],
            "goods_class": ['exact', 'iexact', 'contains', 'icontains'],
            "goods_brand": ['exact', 'iexact', 'contains', 'icontains'],
            "goods_color": ['exact', 'iexact', 'contains', 'icontains'],
            "goods_shape": ['exact', 'iexact', 'contains', 'icontains'],
            "goods_specs": ['exact', 'iexact', 'contains', 'icontains'],
            "goods_origin": ['exact', 'iexact', 'contains', 'icontains'],
            "safety_stock": ['exact', 'iexact', 'gt', 'gte', 'lt', 'lte', 'isnull', 'in', 'range'],
            "goods_cost": ['exact', 'iexact', 'gt', 'gte', 'lt', 'lte', 'isnull', 'in', 'range'],
            "goods_price": ['exact', 'iexact', 'gt', 'gte', 'lt', 'lte', 'isnull', 'in', 'range'],
            "creater": ['exact', 'iexact', 'contains', 'icontains'],
            "is_delete": ['exact', 'iexact'],
            "create_time": ['year', 'month', 'day', 'week_day', 'gt', 'gte', 'lt', 'lte', 'range'],
            "update_time": ['year', 'month', 'day', 'week_day', 'gt', 'gte', 'lt', 'lte', 'range']
        }

class SkuFilter(FilterSet):
    class Meta:
        model = SkuModel
        fields = {
            "id": ['exact', 'iexact', 'gt', 'gte', 'lt', 'lte', 'isnull', 'in', 'range'],
            "sku_code": ['exact', 'iexact', 'contains', 'icontains'],
            "sku_desc": ['exact', 'iexact', 'contains', 'icontains'],
            "sku_cost": ['exact', 'iexact', 'gt', 'gte', 'lt', 'lte', 'isnull', 'in', 'range'],
            "creater": ['exact', 'iexact', 'contains', 'icontains'],
            "is_delete": ['exact', 'iexact'],
            "create_time": ['year', 'month', 'day', 'week_day', 'gt', 'gte', 'lt', 'lte', 'range'],
            "update_time": ['year', 'month', 'day', 'week_day', 'gt', 'gte', 'lt', 'lte', 'range']
        }
