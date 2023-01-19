from django.db import models

class TransportationFeeListModel(models.Model):
    send_city = models.CharField(max_length=255, verbose_name="Send City")
    receiver_city = models.CharField(max_length=255, verbose_name="Receiver City")
    weight_fee = models.FloatField(default=0, verbose_name="Weight Fee")
    volume_fee = models.FloatField(default=0, verbose_name="Volume Fee")
    min_payment = models.FloatField(default=0, verbose_name="Min Payment")
    transportation_supplier = models.CharField(max_length=255, verbose_name="Transportation Supplier")
    creater = models.CharField(max_length=255, verbose_name="Who Created")
    openid = models.CharField(max_length=255, verbose_name="Openid")
    is_delete = models.BooleanField(default=False, verbose_name='Delete Label')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="Create Time")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="Update Time")

    class Meta:
        db_table = 'transportationfee'
        verbose_name = 'Transportation Fee'
        verbose_name_plural = "Transportation Fee"
        ordering = ['-id']

class FinanceListModel(models.Model):
    dn_code = models.CharField(max_length=255, verbose_name="DN Code")
    orderitem_id = models.CharField(max_length=255, default='', verbose_name="OrderItem ID")
    account_name = models.CharField(max_length=255, default='', verbose_name="Account Name")
    goods_code = models.CharField(max_length=255, verbose_name="Goods Code")
    goods_desc = models.CharField(max_length=255, default='', verbose_name="Goods Code")
    shipped_qty = models.BigIntegerField(default=0, verbose_name="Shipped QTY")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Selling price")
    btw_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="BTW Cost")
    bol_commission = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Bol Commission")
    logistic_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Logistic Cost")
    product_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Product Cost")
    is_delete = models.BooleanField(default=False, verbose_name='Delete Label')
    selling_date = models.DateTimeField(auto_now_add=True, verbose_name="Selling Date")
    create_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="Update Time")

    class Meta:
        db_table = 'financetable'
        verbose_name = 'Finance Table'
        verbose_name_plural = 'Finance Table'
        ordering = ['-id']