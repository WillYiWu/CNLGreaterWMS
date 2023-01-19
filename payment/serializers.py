from rest_framework import serializers
from .models import TransportationFeeListModel, FinanceListModel
from utils import datasolve

class FreightGetSerializer(serializers.ModelSerializer):
    send_city = serializers.CharField(read_only=True, required=False)
    receiver_city = serializers.CharField(read_only=True, required=False)
    weight_fee = serializers.FloatField(read_only=True, required=False)
    volume_fee = serializers.FloatField(read_only=True, required=False)
    transportation_supplier = serializers.CharField(read_only=True, required=False)
    creater = serializers.CharField(read_only=True, required=False)
    create_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    update_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = TransportationFeeListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id']

class FinanceGetSerializer(serializers.ModelSerializer):
    dn_code = serializers.CharField(read_only=True, required=False)
    orderitem_id = serializers.CharField(read_only=True, required=False)
    goods_code = serializers.CharField(read_only=True, required=False)
    goods_desc = serializers.CharField(read_only=True, required=False)
    shipped_qty = serializers.IntegerField(read_only=True, required=False)
    selling_price = serializers.DecimalField(read_only=True, required=False, max_digits=10, decimal_places=2)
    btw_cost = serializers.DecimalField(read_only=True, required=False, max_digits=10, decimal_places=2)
    bol_commission = serializers.DecimalField(read_only=True, required=False, max_digits=10, decimal_places=2)
    logistic_cost = serializers.DecimalField(read_only=True, required=False, max_digits=10, decimal_places=2)
    product_cost = serializers.DecimalField(read_only=True, required=False,max_digits=10, decimal_places=2)
    selling_date = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    create_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    class Meta:
        model = FinanceListModel
        exclude = ['is_delete', ]
        read_only_fields = ['id']

class FreightPostSerializer(serializers.ModelSerializer):
    openid = serializers.CharField(read_only=False, required=False, validators=[datasolve.openid_validate])
    send_city = serializers.CharField(read_only=False,  required=True, validators=[datasolve.data_validate])
    receiver_city = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    weight_fee = serializers.FloatField(read_only=False, required=True, validators=[datasolve.data_validate])
    volume_fee = serializers.FloatField(read_only=False, required=True, validators=[datasolve.data_validate])
    transportation_supplier = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    creater = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    class Meta:
        model = TransportationFeeListModel
        exclude = ['is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', ]

class FreightUpdateSerializer(serializers.ModelSerializer):
    send_city = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    receiver_city = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    weight_fee = serializers.FloatField(read_only=False, required=True, validators=[datasolve.data_validate])
    volume_fee = serializers.FloatField(read_only=False, required=True, validators=[datasolve.data_validate])
    transportation_supplier = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    creater = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    class Meta:
        model = TransportationFeeListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', ]

class FreightPartialUpdateSerializer(serializers.ModelSerializer):
    send_city = serializers.CharField(read_only=False, required=False, validators=[datasolve.data_validate])
    receiver_city = serializers.CharField(read_only=False, required=False, validators=[datasolve.data_validate])
    weight_fee = serializers.FloatField(read_only=False, required=False, validators=[datasolve.data_validate])
    volume_fee = serializers.FloatField(read_only=False, required=False, validators=[datasolve.data_validate])
    transportation_supplier = serializers.CharField(read_only=False, required=False, validators=[datasolve.data_validate])
    creater = serializers.CharField(read_only=False, required=False, validators=[datasolve.data_validate])
    class Meta:
        model = TransportationFeeListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', ]

class FreightfileRenderSerializer(serializers.ModelSerializer):
    send_city = serializers.CharField(read_only=True, required=False)
    receiver_city = serializers.CharField(read_only=True, required=False)
    weight_fee = serializers.FloatField(read_only=True, required=False)
    volume_fee = serializers.FloatField(read_only=True, required=False)
    transportation_supplier = serializers.CharField(read_only=True, required=False)
    creater = serializers.CharField(read_only=True, required=False)
    create_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    update_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    class Meta:
        model = TransportationFeeListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id']
