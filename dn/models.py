from django.db import models

class DnListModel(models.Model):
    dn_code = models.CharField(max_length=255, verbose_name="DN Code")
    #[Will] 1:created/imported; 2:pickup list generated; 3:cancelled; 4: delivered
    dn_status = models.BigIntegerField(default=1, verbose_name="DN Status")
    #[Will] Add a new field to indicate total number of items in an order
    total_orderquantity = models.IntegerField(default=1, verbose_name="Total Ordervolume")
    # 2:sufficient stock; 1:insufficient stock; 0:Unmatched EAN
    dn_complete = models.IntegerField(default=2, verbose_name="DN Incomplete")
    total_weight = models.FloatField(default=0, verbose_name="Total Weight")
    total_volume = models.FloatField(default=0, verbose_name="Total Volume")
    total_cost = models.FloatField(default=0, verbose_name="Total Cost")
    customer = models.CharField(max_length=255, verbose_name="DN Customer")
    creater = models.CharField(max_length=255, verbose_name="Who Created")
    bar_code = models.CharField(max_length=255, verbose_name="Bar Code")
    back_order_label = models.BooleanField(default=False, verbose_name='Back Order Label')
    openid = models.CharField(max_length=255, verbose_name="Openid")
    transportation_fee = models.JSONField(default=dict, verbose_name="Transportation Fee")
    is_delete = models.BooleanField(default=False, verbose_name='Delete Label')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="Create Time")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="Update Time")

    class Meta:
        db_table = 'dnlist'
        verbose_name = 'DN List'
        verbose_name_plural = "DN List"
        ordering = ['-id']

class DnDetailModel(models.Model):
    dn_code = models.CharField(max_length=255, verbose_name="DN Code")
    dn_status = models.BigIntegerField(default=1, verbose_name="DN Status")
    # 3:cancelled by customer; 2:sufficient stock; 1:insufficient stock; 0:Unmatched EAN
    dn_complete = models.IntegerField(default=2, verbose_name="DN Incomplete")
    orderitem_id = models.CharField(max_length=255, default='', verbose_name="OrderItem ID")
    customer = models.CharField(max_length=255, verbose_name="DN Customer")
    goods_code = models.CharField(max_length=255, verbose_name="Goods Code")
    goods_desc = models.CharField(max_length=255, verbose_name="Goods Description")
    goods_qty = models.BigIntegerField(default=0, verbose_name="Goods QTY")
    #[Will] Adds stock quantity to show how many short in back order
    stock_qty = models.BigIntegerField(default=0, verbose_name="Stock QTY")
    pick_qty = models.BigIntegerField(default=0, verbose_name="Goods Pre Pick QTY")
    picked_qty = models.BigIntegerField(default=0, verbose_name="Goods Picked QTY")
    intransit_qty = models.BigIntegerField(default=0, verbose_name="Intransit QTY")
    delivery_actual_qty = models.BigIntegerField(default=0, verbose_name="Delivery Actual QTY")
    delivery_shortage_qty = models.BigIntegerField(default=0, verbose_name="Delivery Shortage QTY")
    delivery_more_qty = models.BigIntegerField(default=0, verbose_name="Delivery More QTY")
    delivery_damage_qty = models.BigIntegerField(default=0, verbose_name="Delivery More QTY")
    goods_weight = models.FloatField(default=0, verbose_name="Goods Weight")
    goods_volume = models.FloatField(default=0, verbose_name="Goods Volume")
    goods_cost = models.FloatField(default=0, verbose_name="Goods Cost")
    creater = models.CharField(max_length=255, verbose_name="Who Created")
    back_order_label = models.BooleanField(default=False, verbose_name='Back Order Label')
    openid = models.CharField(max_length=255, verbose_name="Openid")
    is_delete = models.BooleanField(default=False, verbose_name='Delete Label')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="Create Time")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="Update Time")

    class Meta:
        db_table = 'dndetail'
        verbose_name = 'DN Detail'
        verbose_name_plural = "DN Detail"
        ordering = ['-id']

class PickingListModel(models.Model):
    dn_code = models.CharField(max_length=255, verbose_name="DN Code")
    bin_name = models.CharField(max_length=255, verbose_name="Bin Name")
    goods_code = models.CharField(max_length=255, verbose_name="Goods Code")
    #[Will] Add goods description and customer name and orderitem_id
    goods_desc = models.CharField(max_length=255, default='', verbose_name="Goods Code")
    orderitem_id = models.CharField(max_length=255, default='', verbose_name="OrderItem ID")
    is_delete = models.BooleanField(default=False, verbose_name='Delete Label')
    customer = models.CharField(max_length=255, default='', verbose_name="DN Customer")
    picking_status = models.SmallIntegerField(default=0, verbose_name="Picking Status")
    pick_qty = models.BigIntegerField(default=0, verbose_name="Goods Pre Pick QTY")
    picked_qty = models.BigIntegerField(default=0, verbose_name="Picked QTY")
    creater = models.CharField(max_length=255, verbose_name="Who Created")
    t_code = models.CharField(max_length=255, verbose_name="Transaction Code")
    openid = models.CharField(max_length=255, verbose_name="Openid")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="Create Time")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="Update Time")

    class Meta:
        db_table = 'pickinglist'
        verbose_name = 'Picking List'
        verbose_name_plural = "Picking List"
        ordering = ['-id']
