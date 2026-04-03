from django.db import models
from django.db.models import Manager

class StockManager(Manager):
    def _translate_kwargs(self, kwargs):
        if 'goods_code' in kwargs:
            ean = kwargs.pop('goods_code')
            openid = kwargs.get('openid')
            if openid:
                from goods.models import ListModel as GoodsListModel
                g = GoodsListModel.objects.filter(openid=openid, goods_code=ean).first()
                if g and getattr(g, 'sku_code', None):
                    kwargs['sku_code'] = g.sku_code
                else:
                    kwargs['sku_code'] = ean
            else:
                kwargs['sku_code'] = ean
        if 'goods_desc' in kwargs:
            kwargs['sku_desc'] = kwargs.pop('goods_desc')
        return kwargs

    def filter(self, *args, **kwargs):
        kwargs = self._translate_kwargs(kwargs)
        return super().filter(*args, **kwargs)

    def create(self, **kwargs):
        kwargs = self._translate_kwargs(kwargs)
        return super().create(**kwargs)

    def get(self, *args, **kwargs):
        kwargs = self._translate_kwargs(kwargs)
        return super().get(*args, **kwargs)

    def get_or_create(self, defaults=None, **kwargs):
        kwargs = self._translate_kwargs(kwargs)
        if defaults:
            defaults = self._translate_kwargs(defaults)
        return super().get_or_create(defaults=defaults, **kwargs)

    def update_or_create(self, defaults=None, **kwargs):
        kwargs = self._translate_kwargs(kwargs)
        if defaults:
            defaults = self._translate_kwargs(defaults)
        return super().update_or_create(defaults=defaults, **kwargs)

class StockListModel(models.Model):
    sku_code = models.CharField(max_length=255, verbose_name="SKU Code")
    sku_desc = models.CharField(max_length=255, verbose_name="SKU Description")
    goods_qty = models.BigIntegerField(default=0, verbose_name="Total Qty")
    onhand_stock = models.BigIntegerField(default=0, verbose_name='On Hand Stock')
    can_order_stock = models.BigIntegerField(default=0, verbose_name='Can Order Stock')
    ordered_stock = models.BigIntegerField(default=0, verbose_name='Ordered Stock')
    inspect_stock = models.BigIntegerField(default=0, verbose_name='Inspect Stock')
    hold_stock = models.BigIntegerField(default=0, verbose_name='Holding Stock')
    damage_stock = models.BigIntegerField(default=0, verbose_name='Damage Stock')
    asn_stock = models.BigIntegerField(default=0, verbose_name='ASN Stock')
    dn_stock = models.BigIntegerField(default=0, verbose_name='DN Stock')
    pre_load_stock = models.BigIntegerField(default=0, verbose_name='Pre Load Stock')
    pre_sort_stock = models.BigIntegerField(default=0, verbose_name='Pre Sort Stock')
    sorted_stock = models.BigIntegerField(default=0, verbose_name='Sorted Stock')
    pick_stock = models.BigIntegerField(default=0, verbose_name='Pick Stock')
    picked_stock = models.BigIntegerField(default=0, verbose_name='Picked Stock')
    back_order_stock = models.BigIntegerField(default=0, verbose_name='Back Order Stock')
    supplier = models.CharField(default='', max_length=255, verbose_name='Goods Supplier')
    openid = models.CharField(max_length=255, verbose_name="Openid")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="Create Time")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="Update Time")

    objects = StockManager()

    class Meta:
        db_table = 'stocklist'
        verbose_name = 'Stock List'
        verbose_name_plural = "Stock List"
        ordering = ['-id']

class StockBinModel(models.Model):
    bin_name = models.CharField(max_length=255, verbose_name="Bin Name")
    sku_code = models.CharField(max_length=255, verbose_name="SKU Code")
    sku_desc = models.CharField(max_length=255, verbose_name="SKU Description")
    goods_qty = models.BigIntegerField(default=0, verbose_name="Binstock Qty")
    goods_cost = models.FloatField(default=0, verbose_name="Goods Cost")
    pick_qty = models.BigIntegerField(default=0, verbose_name="BinPick Qty")
    picked_qty = models.BigIntegerField(default=0, verbose_name="BinPicked Qty")
    bin_size = models.CharField(max_length=255, verbose_name="Bin size")
    bin_property = models.CharField(max_length=255, verbose_name="Bin Property")
    t_code = models.CharField(max_length=255, verbose_name="Transaction Code")
    openid = models.CharField(max_length=255, verbose_name="Openid")
    create_time = models.DateTimeField(auto_now_add=False, verbose_name="Create Time")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="Update Time")

    objects = StockManager()

    class Meta:
        db_table = 'stockbin'
        verbose_name = 'Stock Bin'
        verbose_name_plural = "Stock Bin"
        ordering = ['-id']

class StockDashboardModel(models.Model):
    stock_quantity = models.BigIntegerField(default=0, verbose_name="Stock Qty")
    stock_value = models.FloatField(default=0, verbose_name="Stock Value")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="Create Time")

    class Meta:
        db_table = 'stockdashboard'
        verbose_name = 'Stock Dashboard'
        verbose_name_plural = "Stock Dashboard"
        ordering = ['-id']