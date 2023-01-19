from dn.models import DnDetailModel as dndetaillist
from .models import TransportationFeeListModel, FinanceListModel
import requests
import json
import base64
import os
from goods.models import ListModel as goods
from staff.models import AccountListModel as account

def obtain_access_token(account_name):
    account_info = account.objects.filter(account_name=account_name, is_delete=False).first()
    credential = account_info.client_id + ":" + account_info.client_secret
    credential_encoded = base64.b64encode(credential.encode())
    oauth_header = {
        "Authorization": f"Basic {credential_encoded.decode()}",
        "Accept": "application/json"
    }
    access_token = requests.post("https://login.bol.com/token?grant_type=client_credentials", headers=oauth_header)
    return access_token.json()["access_token"]

def ObtainfinanceData():
    dnorder_url = "https://api.bol.com/retailer-demo/orders/"
    dndetail_list = dndetaillist.objects.filter(dn_status=4, is_delete=False, revenue_counted=False).order_by('dn_code')
    for i in range(len(dndetail_list)):
        dn_code = dndetail_list[i].dn_code
        headers = {
            "Authorization": "Bearer " + obtain_access_token(dndetail_list[i].account_name),
            "Accept": "application/vnd.retailer.v8+json"
        }
        response_list = requests.get(dnorder_url+dn_code, headers=headers).json()
        if response_list is not None:
            for j in range(len(response_list['orderItems'])):
                country = response_list['shipmentDetails']['countryCode']
                orderitem = response_list['orderItems'][j]
                transport_list = TransportationFeeListModel.objects.filter(receiver_city=country).first()
                goods_list = goods.objects.filter(goods_code=orderitem['product']['ean']).first()

                orderitem_id = orderitem['orderItemId']
                account_name = dndetail_list[i+j].account_name
                goods_code = dndetail_list[i+j].goods_code
                goods_desc = dndetail_list[i+j].goods_desc
                shipped_qty = dndetail_list[i+j].goods_qty
                selling_price = orderitem['unitPrice']
                btw_cost = float(selling_price) - float(selling_price)/1.21
                bol_commission = orderitem['commission']
                logistic_cost = transport_list.min_payment
                product_cost = goods_list.goods_cost
                selling_date = dndetail_list[i+j].update_time

                if not FinanceListModel.objects.filter(orderitem_id=orderitem_id).exists():
                    FinanceListModel.objects.create(dn_code=dn_code,
                                                orderitem_id=orderitem_id,
                                                account_name=account_name,
                                                shipped_qty=shipped_qty,
                                                goods_code=goods_code,
                                                goods_desc=goods_desc,
                                                selling_price=selling_price,
                                                btw_cost=btw_cost,
                                                bol_commission=bol_commission,
                                                logistic_cost=logistic_cost,
                                                product_cost=product_cost,
                                                selling_date=selling_date)
                    dndetail_list[i+j].revenue_counted = True
                    dndetail_list[i+j].save()

            i = i + len(response_list['orderItems'])
