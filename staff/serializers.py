from rest_framework import serializers
from .models import ListModel, TypeListModel, AccountListModel
from utils import datasolve

class StaffGetSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(read_only=True, required=False)
    staff_type = serializers.CharField(read_only=True, required=False)
    check_code = serializers.IntegerField(read_only=True, required=False)
    create_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    update_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = ListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', ]

class StaffPostSerializer(serializers.ModelSerializer):
    openid = serializers.CharField(read_only=False, required=False, validators=[datasolve.openid_validate])
    staff_name = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    staff_type = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    check_code = serializers.IntegerField(read_only=False, required=True, validators=[datasolve.data_validate])
    class Meta:
        model = ListModel
        exclude = ['is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', ]

class StaffUpdateSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    staff_type = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    class Meta:
        model = ListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', ]

class StaffPartialUpdateSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(read_only=False, required=False, validators=[datasolve.data_validate])
    staff_type = serializers.CharField(read_only=False, required=False, validators=[datasolve.data_validate])
    class Meta:
        model = ListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', ]

class FileRenderSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(read_only=False, required=False)
    staff_type = serializers.CharField(read_only=False, required=False)
    create_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    update_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = ListModel
        ref_name = 'StaffFileRenderSerializer'
        exclude = ['openid', 'is_delete', ]

class StaffTypeGetSerializer(serializers.ModelSerializer):
    staff_type = serializers.CharField(read_only=True, required=False)
    creater = serializers.CharField(read_only=True, required=False)
    create_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    update_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    class Meta:
        model = TypeListModel
        exclude = ['openid']
        read_only_fields = ['id', ]

class AccountGetSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(read_only=True, required=False)
    client_id = serializers.CharField(read_only=True, required=False)
    client_secret = serializers.CharField(read_only=True, required=False)
    create_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    update_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = AccountListModel
        exclude = ['openid', 'is_delete', ]
        read_only_fields = ['id', ]

class AccountPostSerializer(serializers.ModelSerializer):
    openid = serializers.CharField(read_only=False, required=False, validators=[datasolve.openid_validate])
    account_name = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    client_id = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    client_secret = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    class Meta:
        model = AccountListModel
        exclude = ['is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', ]

class AccountUpdateSerializer(serializers.ModelSerializer):
    openid = serializers.CharField(read_only=False, required=False, validators=[datasolve.openid_validate])
    account_name = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    client_id = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    client_secret = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    class Meta:
        model = AccountListModel
        exclude = ['is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', ]

class AccountPartialPostSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    client_id = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    client_secret = serializers.CharField(read_only=False, required=True, validators=[datasolve.data_validate])
    class Meta:
        model = AccountListModel
        exclude = ['is_delete', ]
        read_only_fields = ['id', 'create_time', 'update_time', ]
