from rest_framework_csv.renderers import CSVStreamingRenderer

def file_headers():
    return [
        'send_city',
        'receiver_city',
        'weight_fee',
        'volume_fee',
        'min_payment',
        'transportation_supplier',
        'creater',
        'create_time',
        'update_time'
    ]

def cn_data_header():
    return dict([
        ('send_city', u'始发城市'),
        ('receiver_city', u'到货城市'),
        ('weight_fee', u'单公斤运费'),
        ('volume_fee', u'每立方米运费'),
        ('min_payment', u'最小运费'),
        ('transportation_supplier', u'承运商'),
        ('creater', u'创建人'),
        ('create_time', u'创建时间'),
        ('update_time', u'更新时间')
    ])

def en_data_header():
    return dict([
        ('send_city', u'Send City'),
        ('receiver_city', u'Receiver City'),
        ('weight_fee', u'Weight Fee'),
        ('volume_fee', u'Volume Fee'),
        ('min_payment', u'Min Payment'),
        ('transportation_supplier', u'Transportation Supplier'),
        ('creater', u'Creater'),
        ('create_time', u'Create Time'),
        ('update_time', u'Update Time')
    ])

def file_headers_finance():
    return [
        'account_name',
        'dn_code',
        'goods_code',
        'goods_desc',
        'shipped_qty',
        'selling_price',
        'btw_cost',
        'bol_commission',
        'logistic_cost',
        'product_cost',
        'profit',
        'returned',
        'selling_date'
    ]

def cn_data_header_finance():
    return dict([
        ('account_name', u'账户名'),
        ('dn_code', u'订单号'),
        ('goods_code', u'订单物品号'),
        ('goods_desc', u'商品描述'),
        ('shipped_qty', u'订单数量'),
        ('selling_price', u'销售金额'),
        ('btw_cost', u'增值税'),
        ('bol_commission', u'BOL费用'),
        ('logistic_cost', u'物流成本'),
        ('product_cost', u'产品成本'),
        ('profit', u'销售毛利'),
        ('returned', u'退货'),
        ('selling_date', u'发货日期')
    ])

def en_data_header_finance():
    return dict([
        ('account_name', u'Account Name'),
        ('dn_code', u'DN Order'),
        ('goods_code', u'EAN'),
        ('goods_desc', u'Goods Desc'),
        ('shipped_qty', u'Goods Quantity'),
        ('selling_price', u'Selling Revenue'),
        ('btw_cost', u'BTW'),
        ('bol_commission', u'BOL Cost'),
        ('logistic_cost', u'Logistic Cost'),
        ('product_cost', u'Product Cost'),
        ('profit', u'Gross Profit'),
        ('returned', u'Returned'),
        ('selling_date', u'Sending Date')
    ])

class FinanceListRenderCN(CSVStreamingRenderer):
    header = file_headers_finance()
    labels = cn_data_header_finance()

class FinanceListRenderEN(CSVStreamingRenderer):
    header = file_headers_finance()
    labels = en_data_header_finance()
class FreightfileRenderCN(CSVStreamingRenderer):
    header = file_headers()
    labels = cn_data_header()

class FreightfileRenderEN(CSVStreamingRenderer):
    header = file_headers()
    labels = en_data_header()
