from dateutil.relativedelta import relativedelta
from rest_framework import viewsets
from .models import DnListModel, DnDetailModel, PickingListModel
from . import serializers
from .page import MyPageNumberPaginationDNList
from utils.page import MyPageNumberPagination
from utils.datasolve import sumOfList, transportation_calculate
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from .filter import DnListFilter, DnDetailFilter, DnPickingListFilter
from rest_framework.exceptions import APIException
from customer.models import ListModel as customer
from warehouse.models import ListModel as warehouse
from binset.models import ListModel as binset
from goods.models import ListModel as goods
from payment.models import TransportationFeeListModel as transportation
from stock.models import StockListModel as stocklist
from stock.models import StockBinModel as stockbin
from driver.models import ListModel as driverlist
from driver.models import DispatchListModel as driverdispatch
from scanner.models import ListModel as scanner
from cyclecount.models import QTYRecorder as qtychangerecorder
from cyclecount.models import CyclecountModeDayModel as cyclecount
from django.db.models import Q
from django.db.models import Sum
from utils.md5 import Md5
import re
from .serializers import FileListRenderSerializer, FileDetailRenderSerializer
from django.http import StreamingHttpResponse
from django.utils import timezone
from .files import FileListRenderCN, FileListRenderEN, FileDetailRenderCN, FileDetailRenderEN
from rest_framework.settings import api_settings
from staff.models import ListModel as staff
#[Will] Add library requests in order to obtain data from BOL Restful API
import requests
import json
import base64
import os
from staff.models import AccountListModel as account
from stock.models import StockDashboardModel as stockdashboard
from payment.models import FinanceListModel
import PyPDF2
from django.http import FileResponse
from datetime import datetime, timedelta
import pandas as pd
import base64
from django.views import View
import time
from rest_framework.decorators import action

# [Will]
dnlist_url = "https://api.bol.com/retailer/orders?fulfilment-method=FBR&state=OPEN"
dnorder_url = "https://api.bol.com/retailer/orders/"
cancelorder_url = "https://api.bol.com/retailer/orders/cancellation"
shipment_url = "https://api.bol.com/retailer/orders/shipment"
createlabel_url = "https://api.bol.com/retailer/shipping-labels"
deliveryoption_url = "https://api.bol.com/retailer/shipping-labels/delivery-options"
getlabel_url = "https://api.bol.com/retailer/shipping-labels/"
getlabelid_url = "https://api.bol.com/shared/process-status/"
getreturn_url = "https://api.bol.com/retailer/returns?handled=true&fulfilment-method=FBR"


def merge_pdfs(pdf_files, output_file):
    # Creating PDF object using the first pdf file
    pdf_merger = PyPDF2.PdfMerger()
    for filename in pdf_files:
        with open(filename, 'rb') as file:
            pdf_merger.append(file)

    # Writing all the data into the output file
    with open(output_file, 'wb') as file:
        pdf_merger.write(file)


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
    FillInStockDashboardData()
    FillInReturnData()
    dndetail_list = DnDetailModel.objects.filter(dn_status=4, is_delete=False, revenue_counted=False).order_by('dn_code')
    for i in range(len(dndetail_list)):
        if dndetail_list[i].account_name == "Offline":
            continue
        dn_code = dndetail_list[i].dn_code
        headers = {
            "Authorization": "Bearer " + obtain_access_token(dndetail_list[i].account_name),
            "Accept": "application/vnd.retailer.v8+json"
        }
        response_list = requests.get(dnorder_url+dn_code, headers=headers).json()
        if response_list is not None:
            for j in range(len(response_list['orderItems'])):
                orderitem = response_list['orderItems'][j]
                if orderitem['orderItemId'] == dndetail_list[i].orderitem_id:
                    country = response_list['shipmentDetails']['countryCode']
                    transport_list = transportation.objects.filter(receiver_city=country).first()
                    goods_list = goods.objects.filter(goods_code=orderitem['product']['ean']).first()

                    orderitem_id = orderitem['orderItemId']
                    account_name = dndetail_list[i].account_name
                    goods_code = dndetail_list[i].goods_code
                    goods_desc = dndetail_list[i].goods_desc
                    shipped_qty = dndetail_list[i].goods_qty
                    selling_price = float(orderitem['unitPrice']) * float(shipped_qty)
                    btw_cost = float(selling_price) - float(selling_price)/1.21
                    bol_commission_inc_tax = float(orderitem['commission'])
                    bol_commision_vat = bol_commission_inc_tax - bol_commission_inc_tax/ 1.21
                    bol_commission = bol_commission_inc_tax - bol_commision_vat
                    product_cost = float(shipped_qty) * float(dndetail_list[i].goods_cost)
                    selling_date = dndetail_list[i].update_time
                    openid = dndetail_list[i].openid

                    if FinanceListModel.objects.filter(dn_code=dn_code,account_name=account_name).exists():
                        logistic_cost = 0
                    else:
                        logistic_cost = transport_list.min_payment

                    profit = selling_price - btw_cost - bol_commission - logistic_cost - product_cost

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
                                                        profit = profit,
                                                        selling_date=selling_date,
                                                        openid=openid)
                        dndetail_list[i].revenue_counted = True
                        dndetail_list[i].save()

def FillInStockDashboardData():
    stockbin_list = stockbin.objects.filter()
    stock_quantity = 0
    stock_value = 0

    for stock in stockbin_list:
        stock_quantity = stock_quantity + stock.goods_qty
        stock_value = stock_value + float(stock.goods_qty*stock.goods_cost)

    if stockdashboard.objects.filter(create_time__date=timezone.now().date()).exists():
        stock_dasboard = stockdashboard.objects.filter(create_time__date=timezone.now().date())
        stock_dasboard.update(stock_quantity=stock_quantity, stock_value=stock_value)
    else:
        stockdashboard.objects.create(stock_quantity=stock_quantity, stock_value=stock_value)

    return



def FillInReturnData():
    account_list = account.objects.filter(is_delete=False)
    for accounts in account_list:
        account_name = accounts.account_name
        headers = {
            "Authorization": "Bearer " + obtain_access_token(account_name),
            "Accept": "application/vnd.retailer.v8+json"
        }
        return_list = requests.get(getreturn_url, headers=headers)
        json_return_list = return_list.json()["returns"]
        for return_iterate in json_return_list:
            for return_item in return_iterate["returnItems"]:
                if pd.to_datetime(return_item["processingResults"][0]["processingDateTime"]) <= timezone.now().date() - relativedelta(days=35):
                    continue
                dn_code = return_item["orderId"]
                goods_code = return_item["ean"]
                quantity = return_item["expectedQuantity"]
                if not FinanceListModel.objects.filter(dn_code=dn_code, goods_code=goods_code).exists():
                    continue
                else:
                    finance_record = FinanceListModel.objects.filter(dn_code=dn_code, goods_code=goods_code).first()
                    if finance_record.returned == False:
                        finance_record.returned = True
                        finance_record.selling_price = finance_record.selling_price * (finance_record.shipped_qty - quantity)/finance_record.shipped_qty
                        finance_record.btw_cost = finance_record.btw_cost * (finance_record.shipped_qty - quantity)/finance_record.shipped_qty
                        finance_record.bol_commission = finance_record.bol_commission * (finance_record.shipped_qty - quantity)/finance_record.shipped_qty
                        finance_record.product_cost = finance_record.product_cost * (finance_record.shipped_qty - quantity)/finance_record.shipped_qty
                        if float(finance_record.logistic_cost) == 4.98:
                            finance_record.logistic_cost = float(finance_record.logistic_cost) + 2.66
                        elif float(finance_record.logistic_cost) == 5.25:
                            finance_record.logistic_cost = float(finance_record.logistic_cost) + 2.93
                        else:
                            finance_record.logistic_cost = 2.66
                        finance_record.shipped_qty = finance_record.shipped_qty - quantity
                        finance_record.profit = float(finance_record.selling_price) - float(finance_record.btw_cost) - \
                                                   float(finance_record.bol_commission) - float(finance_record.product_cost) - \
                                                    float(finance_record.logistic_cost)
                        finance_record.save()

class ShippinglabelViewSet(View):
    def get(self, request, dn_code, *args, **kwargs):
        if dn_code == "ALL":
            file_name = "merged.pdf"
        else:
            file_name = dn_code + ".pdf"

        file = open(file_name, 'rb')
        response = FileResponse(file)
        response['Content-Type'] = 'application/pdf'
        response['Content-Disposition'] = 'attachment; filename=' + file_name
        return response

#[Will] Add new model class to handle request fetching data from BOL
class BolListViewSet(viewsets.ModelViewSet):
    """
        retrieve:
            Response a data list（get）

        list:
            Response a data list（all）

        create:
            Create a data line（post）

        delete:
            Delete a data line（delete)

    """
    pagination_class = MyPageNumberPaginationDNList
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnListFilter

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve', 'destroy']:
            return serializers.DNListGetSerializer
        elif self.action in ['create']:
            return serializers.DNListPostSerializer
        elif self.action in ['update']:
            return serializers.DNListUpdateSerializer
        elif self.action in ['partial_update']:
            return serializers.DNListPartialUpdateSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    #[Will]New function to pull order data from BOL and store to DNList and DNDetailList
    def create(self, request, *args, **kwargs):
        FillInStockDashboardData()
        data = self.request.data
        account_name = data['account_name']
        headers = {
            "Authorization": "Bearer " + obtain_access_token(account_name),
            "Accept": "application/vnd.retailer.v8+json"
        }
        headers_deliveryoption = {
            "Authorization": "Bearer " + obtain_access_token(account_name),
            "Accept": "application/vnd.retailer.v8+json",
            "Content-Type": "application/vnd.retailer.v8+json"
        }
        headers_label = {
            "Authorization": "Bearer " + obtain_access_token(account_name),
            "Accept": "application/vnd.retailer.v8+pdf",
            "Content-Type": "application/vnd.retailer.v8+json"
        }
        response_list = requests.get(dnlist_url, headers=headers)
        json_obj_list = response_list.json()
        if len(json_obj_list) == 0:
            return Response({"detail": "没有新订单"}, status=200)
        staff_name = staff.objects.filter(openid=self.request.auth.openid,
                                          id=self.request.META.get('HTTP_OPERATOR')).first().staff_name
        #A loop to extract all orders, and generate DN per order, and count orderitem number for each order
        for order in json_obj_list["orders"]:
            orderitem_quantity = 0
            dn_complete = 2
            response_detail = requests.get(dnorder_url+order["orderId"], headers=headers)
            json_obj_detail = response_detail.json()
            for orderitem in order["orderItems"]:
                orderitem_quantity=orderitem["quantity"]+orderitem_quantity
                ean = orderitem["ean"]
                goods_desc = ''
                sending_date = ''
                can_order_stock = 0

                order_item = []
                order_item.append({'orderItemId': orderitem["orderItemId"]})
                deliveryoption_data = {"orderItems": order_item}

                #Fetch handover date and shippingLabelOfferId from BOL, handover date equals to sending date
                deliveryoption_result = requests.post(deliveryoption_url, json.dumps(deliveryoption_data), headers=headers_deliveryoption)
                if deliveryoption_result.status_code == 200:
                    deliveryoption_json = deliveryoption_result.json()
                    for option in deliveryoption_json["deliveryOptions"]:
                        if option["recommended"] == True:
                            sending_date = pd.to_datetime(option["handoverDetails"]["latestHandoverDateTime"])
                            if sending_date.weekday() == 0:
                                sending_date = sending_date - pd.Timedelta(days=2)
                            labeloffer_id = option["shippingLabelOfferId"]
                            break
                else:
                    print(orderitem["orderItemId"] + 'deliveryoption fetch fail')


                if not goods.objects.filter(goods_code=ean, is_delete=False).exists():
                    dn_complete = 0
                else:
                    if dn_complete != 0:
                        if not stocklist.objects.filter(goods_code=ean).exists():
                            dn_complete = 1
                        else:
                            stock_list = stocklist.objects.filter(goods_code=ean).first()
                            if stock_list.can_order_stock < orderitem["quantity"]:
                                dn_complete = 1
                            else:
                                if dn_complete != 1:
                                    dn_complete = 2

                    if orderitem["cancellationRequest"] != False:
                        dn_complete = 3

                    goods_desc = goods.objects.filter(goods_code=ean, is_delete=False).first().goods_desc

                data = {
                    "openid": self.request.auth.openid,
                    "dn_code": order["orderId"],
                    "dn_status": 1,
                    "goods_desc": goods_desc,
                    "account_name": account_name,
                    "stock_qty": can_order_stock,
                    "orderitem_id": orderitem["orderItemId"],
                    "dn_complete": dn_complete,
                    "customer": json_obj_detail["shipmentDetails"]["firstName"],
                    "goods_code": ean,
                    "goods_qty": orderitem["quantity"],
                    "sending_date": sending_date,
                    "labeloffer_id": labeloffer_id,
                    "creater": str(staff_name)
                }
                obj, created = DnDetailModel.objects.get_or_create(
                    orderitem_id=orderitem["orderItemId"],
                    is_delete=False,
                    defaults=data
                )
                if not created:
                    obj.goods_desc = goods_desc
                    obj.save()
                time.sleep(0.1)
                """
                if not DnDetailModel.objects.filter(orderitem_id=orderitem["orderItemId"], is_delete=False).exists():
                    DnDetailModel.objects.create(openid=self.request.auth.openid,
                                              dn_code=order["orderId"],
                                              dn_status=1,
                                              goods_desc=goods_desc,
                                              account_name=account_name,
                                              stock_qty=can_order_stock,
                                              orderitem_id=orderitem["orderItemId"],
                                              dn_complete=dn_complete,
                                              customer=json_obj_detail["shipmentDetails"]["firstName"],
                                              goods_code=ean,
                                              goods_qty=orderitem["quantity"],
                                              sending_date=sending_date,
                                              labeloffer_id=labeloffer_id,
                                              creater=str(staff_name))
                else:
                    dndetail_list = DnDetailModel.objects.filter(orderitem_id=orderitem["orderItemId"], is_delete=False).first()
                    dndetail_list.goods_desc = goods_desc
                    dndetail_list.save()
                 """
            dndetail_list = DnDetailModel.objects.filter(dn_code=order["orderId"], is_delete=False)
            for i in range(len(dndetail_list)):
                dndetail_list[i].dn_complete = dn_complete
                dndetail_list[i].save()

            data_dn = {
                "openid": self.request.auth.openid,
                "dn_code": order["orderId"],
                "dn_status": 1,
                "account_name": account_name,
                "total_orderquantity": orderitem_quantity,
                "dn_complete": dn_complete,
                "customer": json_obj_detail["shipmentDetails"]["firstName"],
                "sending_date": sending_date,
                "create_time": order["orderPlacedDateTime"],
                "creater": str(staff_name)
            }

            obj_dn, created = DnListModel.objects.get_or_create(
                dn_code=order["orderId"],
                account_name=account_name,
                is_delete=False,
                defaults=data_dn
            )
            if not created:
                obj_dn.dn_complete = dn_complete
                obj_dn.save()

            """
            if not DnListModel.objects.filter(dn_code=order["orderId"],account_name=account_name,is_delete=False).exists():
                DnListModel.objects.create(openid=self.request.auth.openid,
                                           dn_code=order["orderId"],
                                           dn_status=1,
                                           account_name=account_name,
                                           total_orderquantity=orderitem_quantity,
                                           dn_complete=dn_complete,
                                           customer=json_obj_detail["shipmentDetails"]["firstName"],
                                           sending_date=sending_date,
                                           create_time=order["orderPlacedDateTime"],
                                           creater=str(staff_name))
            else:
                dn_list = DnListModel.objects.filter(dn_code=order["orderId"], is_delete=False).first()
                dn_list.dn_complete = dn_complete
                dn_list.save()
            """

        #Create shipping label for all detailed orders with dn_complete = 2
        dndetail_list = DnDetailModel.objects.filter(dn_complete=2, dn_status__lte=2, is_delete=False)
        for order in dndetail_list:
            labeloffer_id = order.labeloffer_id
            order_item = []
            order_item.append({'orderItemId': order.orderitem_id})
            createlabel_data = {"orderItems": order_item, "shippingLabelOfferId": labeloffer_id}
            createlabel_result = requests.post(createlabel_url, json.dumps(createlabel_data),headers=headers_deliveryoption)
            labelprocess_id = createlabel_result.json()["processStatusId"]
            order.labelprocess_id = labelprocess_id
            order.save()

        time.sleep(1)

        dndetail_list = DnDetailModel.objects.filter(dn_complete=2, dn_status__lte=2, is_delete=False)
        label_id_empty = False
        for order in dndetail_list:
            labelprocess_id = order.labelprocess_id
            process_result = requests.get(getlabelid_url+labelprocess_id,headers=headers)
            if process_result.status_code == 200:
                status = process_result.json()["status"]
                if status == 'SUCCESS':
                    print(order.dn_code + 'success')
                    label_id = process_result.json()["entityId"]
                    if label_id == '':
                        label_id_empty = True
                    order.label_id = label_id
                    order.save()
                else:
                    label_id_empty = True
            else:
                print(f'Error: Failed to download the PDF file. Status code: {process_result.status_code}')

        if label_id_empty == True:
            time.sleep(3)
            label_id_empty = False
            for order in dndetail_list:
                if order.label_id == '':
                    process_result = requests.get(getlabelid_url + order.labelprocess_id, headers=headers)
                    if process_result.status_code == 200:
                        status = process_result.json()["status"]
                        if status == 'SUCCESS':
                            print(order.dn_code + 'success')
                            label_id = process_result.json()["entityId"]
                            if label_id == '':
                                label_id_empty = True
                            order.label_id = label_id
                            order.save()
                        else:
                            label_id_empty = True


        for order in dndetail_list:
            # Retrieve pdf label file from BOL, name is by orderitem_id, store them locally
            response = requests.get(getlabel_url + order.label_id, headers=headers_label)
            if response.status_code == 200:
                if 'application/vnd.retailer.v8+pdf' in response.headers['content-type']:
                    with open(order.account_name + order.dn_code + '.pdf', 'wb') as file:
                        file.write(response.content)
                    print(order.dn_code + 'PDF file saved successfully')
                else:
                    print('Error: The response is not a PDF file')

        if label_id_empty == True:
            return Response({"detail": "面单未取全"}, status=200)
        else:
            return Response({"detail": "success"}, status=200)

    #[Will] When EAN is not matching or stock is insufficient, cancel order and inform BOL
    def destroy(self, request, *args, **kwargs):
        dn_code = self.kwargs.get('dn_code', None)
        account_name = ''
        orderItems = []
        if dn_code == 'undefined':
            detail_list = DnDetailModel.objects.filter(openid=self.request.auth.openid,
                                            is_delete=False)
        else:
            detail_list = DnDetailModel.objects.filter(openid=self.request.auth.openid,
                                            is_delete=False,
                                            dn_code=dn_code)
        if detail_list.exists():
            for i in range(len(detail_list)):
                if detail_list[i].dn_complete == 3:
                    orderItems.append({'orderItemId': detail_list[i].orderitem_id,
                                  'reasonCode': "REQUESTED_BY_CUSTOMER"})
                else:
                    orderItems.append({'orderItemId': detail_list[i].orderitem_id,
                                  'reasonCode': "OUT_OF_STOCK"})
                cancel_data = {"orderItems": orderItems}
                dn_code = detail_list[i].dn_code
                detail_list[i].is_delete = True
                detail_list[i].dn_status = 3
                account_name = detail_list[i].account_name
                detail_list[i].save()

                stock_list = stocklist.objects.filter(goods_code=detail_list[i].goods_code).first()

                if DnListModel.objects.filter(dn_code=dn_code, is_delete=False).exists():
                    dn_list = DnListModel.objects.filter(dn_code=dn_code, is_delete=False).first()
                    dn_list.is_delete = True
                    dn_list.dn_status = 3
                    dn_list.save()


                if PickingListModel.objects.filter(dn_code=dn_code, is_delete=False).exists():
                    dn_picking_list = PickingListModel.objects.filter(dn_code=dn_code, is_delete=False)
                    for i in range(len(dn_picking_list)):
                        dn_picking_list[i].is_delete = True
                        dn_picking_list[i].save()

                if FinanceListModel.objects.filter(dn_code=dn_code, is_delete=False).exists():
                    finance_list = FinanceListModel.objects.filter(dn_code=dn_code, is_delete=False)
                    for i in range(len(finance_list)):
                        finance_list[i].is_delete = True
                        finance_list[i].save()

            headers = {
                "Authorization": "Bearer " + obtain_access_token(account_name),
                "Accept": "application/vnd.retailer.v8+json",
                "Content-Type": "application/vnd.retailer.v8+json"
            }
            response = requests.put(cancelorder_url, json.dumps(cancel_data), headers=headers)
            return Response({"detail": "success"}, status=200)
        else:
            return Response({"detail": "nothing to delete"}, status=200)



class DnListViewSet(viewsets.ModelViewSet):
    """
        retrieve:
            Response a data list（get）

        list:
            Response a data list（all）

        create:
            Create a data line（post）

        delete:
            Delete a data line（delete)

    """
    pagination_class = MyPageNumberPaginationDNList
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnListFilter

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_queryset(self):
        id = self.get_project()
        if self.request.user:
            empty_qs = DnListModel.objects.filter(
                Q(openid=self.request.auth.openid, dn_status=1, is_delete=False) & Q(customer=''))
            cur_date = timezone.now()
            date_check = relativedelta(day=1)
            if len(empty_qs) > 0:
                for i in range(len(empty_qs)):
                    if empty_qs[i].create_time <= cur_date - date_check:
                        empty_qs[i].delete()
            if id is None:
                return DnListModel.objects.filter(
                    Q(openid=self.request.auth.openid, dn_status__lte=2, is_delete=False, sending_date__lte=datetime.today().replace(hour=23,minute=59,second=59)) & ~Q(customer='')).order_by('account_name','dn_complete', 'dn_code')
            else:
                return DnListModel.objects.filter(
                    Q(openid=self.request.auth.openid, id=id, is_delete=False, sending_date__lte=datetime.today().replace(hour=23,minute=59,second=59)) & ~Q(customer=''))
        else:
            return DnListModel.objects.none()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve', 'destroy']:
            return serializers.DNListGetSerializer
        elif self.action in ['create']:
            return serializers.DNListPostSerializer
        elif self.action in ['update']:
            return serializers.DNListUpdateSerializer
        elif self.action in ['partial_update']:
            return serializers.DNListPartialUpdateSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def create(self, request, *args, **kwargs):
        data = self.request.data
        data['openid'] = self.request.auth.openid
        custom_dn = self.request.GET.get('custom_dn', '')
        if custom_dn:
            data['dn_code'] = custom_dn
        else:
            qs_set = DnListModel.objects.filter(openid=self.request.auth.openid, is_delete=False)
            order_day =str(timezone.now().strftime('%Y%m%d'))
            if len(qs_set) > 0:
                dn_last_code = qs_set.order_by('-id').first().dn_code
                if dn_last_code[2:10] == order_day:
                    order_create_no = str(int(dn_last_code[10:]) + 1)
                    data['dn_code'] = 'DN' + order_day + order_create_no
                else:
                    data['dn_code'] = 'DN' + order_day + '1'
            else:
                data['dn_code'] = 'DN' + order_day + '1'
        data['bar_code'] = Md5.md5(str(data['dn_code']))
        data['dn_status'] = 4
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        scanner.objects.create(openid=self.request.auth.openid, mode="DN", code=data['dn_code'],
                               bar_code=data['bar_code'])
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=200, headers=headers)

    def destroy(self, request, pk):
        qs = self.get_object()
        if qs.openid != self.request.auth.openid:
            raise APIException({"detail": "Cannot delete data which not yours"})
        else:
            if qs.dn_status == 1:
                qs.is_delete = True
                dn_detail_list = DnDetailModel.objects.filter(openid=self.request.auth.openid, dn_code=qs.dn_code,
                                              dn_status=1, is_delete=False)
                for i in range(len(dn_detail_list)):
                    goods_qty_change = stocklist.objects.filter(openid=self.request.auth.openid,
                                                                goods_code=str(dn_detail_list[i].goods_code)).first()
                    goods_qty_change.dn_stock = goods_qty_change.dn_stock - int(dn_detail_list[i].goods_qty)
                    goods_qty_change.save()
                dn_detail_list.update(is_delete=True)
                qs.save()
                return Response({"detail": "success"}, status=200)
            else:
                raise APIException({"detail": "This order has Confirmed or Deliveried"})

class DnDetailViewSet(viewsets.ModelViewSet):
    """
        retrieve:
            Response a data list（get）

        list:
            Response a data list（all）

        create:
            Create a data line（post）

        update:
            Update a data（put：update）
    """
    pagination_class = MyPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnDetailFilter

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_queryset(self):
        #[Will] Show DNDetailList either by all or by dn_code
        dn_code = self.kwargs.get('dn_code', None)
        dn_complete = int(self.request.query_params.get('dn_complete', None))
        dn_status = int(self.request.query_params.get('dn_status', None))
        if dn_status == 4:
            result = DnDetailModel.objects.filter(openid=self.request.auth.openid, is_delete=False,
                                                dn_complete=dn_complete, dn_status=dn_status).order_by('-sending_date')
            return result

        if dn_code != 'undefined':
            result = DnDetailModel.objects.filter(openid=self.request.auth.openid, is_delete=False,
                                                dn_complete=dn_complete, dn_status=dn_status, dn_code=dn_code, sending_date__lte=datetime.today().replace(hour=23,minute=59,second=59)).order_by('account_name','dn_code')
        else:
            result = DnDetailModel.objects.filter(openid=self.request.auth.openid, is_delete=False,
                                                dn_complete=dn_complete, dn_status=dn_status, sending_date__lte=datetime.today().replace(hour=23,minute=59,second=59)).order_by('account_name','dn_code')
        return result

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve', 'destroy']:
            return serializers.DNDetailGetSerializer
        elif self.action in ['create']:
            return serializers.DNDetailPostSerializer
        elif self.action in ['update']:
            return serializers.DNDetailUpdateSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def create(self, request, *args, **kwargs):
        data = self.request.data
        if DnListModel.objects.filter(openid=self.request.auth.openid, dn_code=str(data['dn_code']), is_delete=False).exists():
            if customer.objects.filter(openid=self.request.auth.openid, customer_name=str(data['customer']), is_delete=False).exists():
                staff_name = staff.objects.filter(openid=self.request.auth.openid,
                                                  id=self.request.META.get('HTTP_OPERATOR')).first().staff_name
                for i in range(len(data['goods_code'])):
                    if goods.objects.filter(openid=self.request.auth.openid,
                                                        goods_code=str(data['goods_code'][i]),
                                                        is_delete=False).exists():
                        check_data = {
                            'openid': self.request.auth.openid,
                            'dn_code': str(data['dn_code']),
                            'account_name': 'Offline',
                            'customer': str(data['customer']),
                            'goods_code': str(data['goods_code'][i]),
                            'goods_qty': int(data['goods_qty'][i]),
                            'goods_price': float(data['goods_price'][i]),
                            'dn_status': 4,
                            'creater': str(staff_name)
                        }
                        serializer = self.get_serializer(data=check_data)
                        serializer.is_valid(raise_exception=True)
                    else:
                        raise APIException({"detail": str(data['goods_code'][i]) + " does not exists"})
                post_data_list = []
                post_finance_list = []
                weight_list = []
                volume_list = []
                cost_list = []
                for j in range(len(data['goods_code'])):
                    goods_detail = goods.objects.filter(openid=self.request.auth.openid,
                                                        goods_code=str(data['goods_code'][j]),
                                                        is_delete=False).first()
                    goods_weight = round(goods_detail.goods_weight * int(data['goods_qty'][j]) / 1000, 4)
                    goods_volume = round(goods_detail.unit_volume * int(data['goods_qty'][j]), 4)
                    goods_cost = round(goods_detail.goods_cost * int(data['goods_qty'][j]), 2)

                    goods_qty = int(data['goods_qty'][j])
                    tobe_picked = goods_qty
                    stockbin_list = stockbin.objects.filter(goods_code=str(data['goods_code'][j]),bin_property='Normal')
                    stocklist_list = stocklist.objects.filter(openid=self.request.auth.openid, goods_code=str(data['goods_code'][j])).first()

                    if stocklist_list.can_order_stock >= goods_qty:
                        for stockbin_each in stockbin_list:
                            db_qty = stockbin_each.goods_qty
                            if tobe_picked > db_qty:
                                tobe_picked = tobe_picked - db_qty
                                db_qty = 0
                                stockbin_each.goods_qty = db_qty
                                stockbin_each.save()
                            else:
                                db_qty = db_qty - tobe_picked
                                stockbin_each.goods_qty = db_qty
                                stockbin_each.save()
                                break
                        stocklist_list.can_order_stock = stocklist_list.can_order_stock - goods_qty
                        stocklist_list.onhand_stock = stocklist_list.onhand_stock - goods_qty
                        stocklist_list.save()
                    else:
                        raise APIException({"detail": "Insufficient Stock"})


                    post_data = DnDetailModel(openid=self.request.auth.openid,
                                              dn_code=str(data['dn_code']),
                                              customer=str(data['customer']),
                                              account_name='Offline',
                                              dn_status=4,
                                              goods_code=str(data['goods_code'][j]),
                                              goods_desc=str(goods_detail.goods_desc),
                                              goods_qty=int(data['goods_qty'][j]),
                                              goods_weight=goods_weight,
                                              goods_volume=goods_volume,
                                              goods_cost=goods_cost,
                                              revenue_counted=True,
                                              creater=str(staff_name))

                    post_finance = FinanceListModel(openid=self.request.auth.openid,
                                              dn_code=str(data['dn_code']),
                                              account_name=str(data['customer']),
                                              goods_code=str(data['goods_code'][j]),
                                              goods_desc=str(goods_detail.goods_desc),
                                              shipped_qty=int(data['goods_qty'][j]),
                                              selling_price=float(data['goods_price'][j])*int(data['goods_qty'][j]),
                                              product_cost=goods_cost,
                                              profit=float(data['goods_price'][j])*int(data['goods_qty'][j])-goods_cost,
                                              btw_cost=0,
                                              bol_commission=0,
                                              logistic_cost=0)

                    weight_list.append(goods_weight)
                    volume_list.append(goods_volume)
                    cost_list.append(goods_cost)
                    post_data_list.append(post_data)
                    post_finance_list.append(post_finance)
                total_weight = sumOfList(weight_list, len(weight_list))
                total_volume = sumOfList(volume_list, len(volume_list))
                total_cost = sumOfList(cost_list, len(cost_list))
                customer_city = customer.objects.filter(openid=self.request.auth.openid,
                                                        customer_name=str(data['customer']),
                                                        is_delete=False).first().customer_city
                warehouse_city = warehouse.objects.filter(openid=self.request.auth.openid, is_delete=False).first().warehouse_city
                transportation_fee = transportation.objects.filter(
                    Q(openid=self.request.auth.openid, send_city__icontains=warehouse_city, receiver_city__icontains=customer_city,
                      is_delete=False) | Q(openid='init_data', send_city__icontains=warehouse_city, receiver_city__icontains=customer_city,
                                           is_delete=False))
                transportation_res = {
                    "detail": []
                }
                if len(transportation_fee) >= 1:
                    transportation_list = []
                    for k in range(len(transportation_fee)):
                        transportation_cost = transportation_calculate(total_weight,
                                                                       total_volume,
                                                                       transportation_fee[k].weight_fee,
                                                                       transportation_fee[k].volume_fee,
                                                                       transportation_fee[k].min_payment)
                        transportation_detail = {
                            "transportation_supplier": transportation_fee[k].transportation_supplier,
                            "transportation_cost": transportation_cost
                        }
                        transportation_list.append(transportation_detail)
                    transportation_res['detail'] = transportation_list
                DnDetailModel.objects.bulk_create(post_data_list, batch_size=100)
                FinanceListModel.objects.bulk_create(post_finance_list, batch_size=10)
                DnListModel.objects.filter(openid=self.request.auth.openid, dn_code=str(data['dn_code']), is_delete=False).update(
                    customer=str(data['customer']), total_weight=total_weight, total_volume=total_volume,
                    total_cost=total_cost, transportation_fee=transportation_res)
                return Response({"detail": "success"}, status=200)
            else:
                raise APIException({"detail": "customer does not exists"})
        else:
            raise APIException({"detail": "DN Code does not exists"})

    def update(self, request, *args, **kwargs):
        data = self.request.data
        if DnListModel.objects.filter(openid=self.request.auth.openid, dn_code=str(data['dn_code']),
                                       dn_status=1, is_delete=False).exists():
            if customer.objects.filter(openid=self.request.auth.openid, customer_name=str(data['customer']),
                                       is_delete=False).exists():
                staff_name = staff.objects.filter(openid=self.request.auth.openid,
                                                  id=self.request.META.get('HTTP_OPERATOR')).first().staff_name
                for i in range(len(data['goods_code'])):
                    check_data = {
                        'openid': self.request.auth.openid,
                        'dn_code': str(data['dn_code']),
                        'customer': str(data['customer']),
                        'goods_code': str(data['goods_code'][i]),
                        'goods_qty': int(data['goods_qty'][i]),
                        'creater': str(staff_name)
                    }
                    serializer = self.get_serializer(data=check_data)
                    serializer.is_valid(raise_exception=True)
                dn_detail_list = DnDetailModel.objects.filter(openid=self.request.auth.openid,
                                              dn_code=str(data['dn_code']), is_delete=False)
                for v in range(len(dn_detail_list)):
                    goods_qty_change = stocklist.objects.filter(openid=self.request.auth.openid,
                                                                goods_code=str(dn_detail_list[v].goods_code)).first()
                    goods_qty_change.dn_stock = goods_qty_change.dn_stock - dn_detail_list[v].goods_qty
                    if goods_qty_change.dn_stock < 0:
                        goods_qty_change.dn_stock = 0
                    goods_qty_change.save()
                    dn_detail_list[v].is_delete = True
                    dn_detail_list[v].save()
                post_data_list = []
                weight_list = []
                volume_list = []
                cost_list = []
                for j in range(len(data['goods_code'])):
                    goods_detail = goods.objects.filter(openid=self.request.auth.openid,
                                                        goods_code=str(data['goods_code'][j]),
                                                        is_delete=False).first()
                    goods_weight = round(goods_detail.goods_weight * int(data['goods_qty'][j]) / 1000, 4)
                    goods_volume = round(goods_detail.unit_volume * int(data['goods_qty'][j]), 4)
                    goods_cost = round(goods_detail.goods_price * int(data['goods_qty'][j]), 2)
                    if stocklist.objects.filter(openid=self.request.auth.openid, goods_code=str(data['goods_code'][j]),
                                                can_order_stock__gt=0).exists():
                        goods_qty_change = stocklist.objects.filter(openid=self.request.auth.openid,
                                                                    goods_code=str(data['goods_code'][j])).first()
                        goods_qty_change.dn_stock = goods_qty_change.dn_stock + int(data['goods_qty'][j])
                        goods_qty_change.save()
                    else:
                        stocklist.objects.create(openid=self.request.auth.openid,
                                                 goods_code=str(data['goods_code'][j]),
                                                 goods_desc=goods_detail.goods_desc,
                                                 dn_stock=int(data['goods_qty'][j]))
                    post_data = DnDetailModel(openid=self.request.auth.openid,
                                              dn_code=str(data['dn_code']),
                                              customer=str(data['customer']),
                                              goods_code=str(data['goods_code'][j]),
                                              goods_desc=str(goods_detail.goods_desc),
                                              goods_qty=int(data['goods_qty'][j]),
                                              goods_weight=goods_weight,
                                              goods_volume=goods_volume,
                                              goods_cost=goods_cost,
                                              creater=str(staff_name))
                    weight_list.append(goods_weight)
                    volume_list.append(goods_volume)
                    cost_list.append(goods_cost)
                    post_data_list.append(post_data)
                total_weight = sumOfList(weight_list, len(weight_list))
                total_volume = sumOfList(volume_list, len(volume_list))
                total_cost = sumOfList(cost_list, len(cost_list))
                customer_city = customer.objects.filter(openid=self.request.auth.openid,
                                                        customer_name=str(data['customer']),
                                                        is_delete=False).first().customer_city
                warehouse_city = warehouse.objects.filter(openid=self.request.auth.openid, is_delete=False).first().warehouse_city
                transportation_fee = transportation.objects.filter(
                    Q(openid=self.request.auth.openid, send_city__icontains=warehouse_city,
                      receiver_city__icontains=customer_city,
                      is_delete=False) | Q(openid='init_data', send_city__icontains=warehouse_city,
                                           receiver_city__icontains=customer_city,
                                           is_delete=False))
                transportation_res = {
                    "detail": []
                }
                if len(transportation_fee) >= 1:
                    transportation_list = []
                    for k in range(len(transportation_fee)):
                        transportation_cost = transportation_calculate(total_weight,
                                                                       total_volume,
                                                                       transportation_fee[k].weight_fee,
                                                                       transportation_fee[k].volume_fee,
                                                                       transportation_fee[k].min_payment)
                        transportation_detail = {
                            "transportation_supplier": transportation_fee[k].transportation_supplier,
                            "transportation_cost": transportation_cost
                        }
                        transportation_list.append(transportation_detail)
                    transportation_res['detail'] = transportation_list
                DnDetailModel.objects.bulk_create(post_data_list, batch_size=100)
                DnListModel.objects.filter(openid=self.request.auth.openid, dn_code=str(data['dn_code']), is_delete=False).update(
                    customer=str(data['customer']), total_weight=total_weight, total_volume=total_volume,
                    total_cost=total_cost, transportation_fee=transportation_res)
                return Response({"detail": "success"}, status=200)
            else:
                raise APIException({"detail": "Customer does not exists"})
        else:
            raise APIException({"detail": "DN Code has been Confirmed or does not exists"})

    def destroy(self, request):
        #[Will] rewrite this function, this function will only be called for
        #bulk order cancelling for Wrong EAN and out of stock orders
        dn_complete = self.request.query_params.get('dn_complete', None)
        dn_status = self.request.query_params.get('dn_status', None)
        detail_list = DnDetailModel.objects.filter(openid=self.request.auth.openid,
                                                 dn_complete=dn_complete,
                                                 dn_status=dn_status,
                                                 is_delete=False).order_by('account_name')

        account_name = ''
        orderItems = []
        if detail_list.exists():
            for i in range(len(detail_list)):
                if detail_list[i].dn_complete == 3:
                    orderItems.append({'orderItemId': detail_list[i].orderitem_id,
                                  'reasonCode': "REQUESTED_BY_CUSTOMER"})
                else:
                    orderItems.append({'orderItemId': detail_list[i].orderitem_id,
                                  'reasonCode': "OUT_OF_STOCK"})
                cancel_data = {"orderItems": orderItems}
                detail_list[i].is_delete = True
                account_name = detail_list[i].account_name
                detail_list[i].save()
                dn_list = DnListModel.objects.filter(dn_code=detail_list[i].dn_code, is_delete=False).first()
                dn_list.is_delete = True
                dn_list.dn_status = 3
                dn_list.save()

            headers = {
                "Authorization": "Bearer " + obtain_access_token(account_name),
                "Accept": "application/vnd.retailer.v8+json",
                "Content-Type": "application/vnd.retailer.v8+json"
            }
            response = requests.put(cancelorder_url, json.dumps(cancel_data), headers=headers)
            return Response({"detail": "success"}, status=200)
        else:
            return Response({"detail": "nothing to delete"}, status=200)


class DnViewPrintViewSet(viewsets.ModelViewSet):
    """
        retrieve:
            Response a data list（get）
    """
    serializer_class = serializers.DNListGetSerializer
    pagination_class = MyPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnListFilter

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
                return DnListModel.objects.filter(openid=self.request.auth.openid, is_delete=False)
            else:
                return DnListModel.objects.filter(openid=self.request.auth.openid, id=id, is_delete=False)
        else:
            return DnListModel.objects.none()

    def get_serializer_class(self):
        if self.action in ['retrieve']:
            return serializers.DNDetailGetSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def retrieve(self, request, pk):
        qs = self.get_object()
        if qs.openid != self.request.auth.openid:
            raise APIException({"detail": "Cannot update data which not yours"})
        else:
            context = {}
            dn_detail_list = DnDetailModel.objects.filter(openid=self.request.auth.openid,
                                                          dn_code=qs.dn_code,
                                                          is_delete=False)
            dn_detail = serializers.DNDetailGetSerializer(dn_detail_list, many=True)
            customer_detail = customer.objects.filter(openid=self.request.auth.openid,
                                                            customer_name=qs.customer, is_delete=False).first()
            warehouse_detail = warehouse.objects.filter(openid=self.request.auth.openid, is_delete=False).first()
            context['dn_detail'] = dn_detail.data
            context['customer_detail'] = {
                "customer_name": customer_detail.customer_name,
                "customer_city": customer_detail.customer_city,
                "customer_address": customer_detail.customer_address,
                "customer_contact": customer_detail.customer_contact
            }
            context['warehouse_detail'] = {
                "warehouse_name": warehouse_detail.warehouse_name,
                "warehouse_city": warehouse_detail.warehouse_city,
                "warehouse_address": warehouse_detail.warehouse_address,
                "warehouse_contact": warehouse_detail.warehouse_contact
            }
        return Response(context, status=200)

class DnNewOrderViewSet(viewsets.ModelViewSet):
    """
        retrieve:
            Response a data list（get）
    """
    pagination_class = MyPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnListFilter

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
                return DnListModel.objects.filter(openid=self.request.auth.openid, is_delete=False)
            else:
                return DnListModel.objects.filter(openid=self.request.auth.openid, id=id, is_delete=False)
        else:
            return DnListModel.objects.none()

    def get_serializer_class(self):
        if self.action in ['create']:
            return serializers.DNListPartialUpdateSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def create(self, request, pk):
        qs = self.get_object()
        if qs.openid != self.request.auth.openid:
            raise APIException({"detail": "Cannot delete data which not yours"})
        else:
            if qs.dn_status == 1:
                if DnDetailModel.objects.filter(openid=self.request.auth.openid, dn_code=qs.dn_code,
                                                                dn_status=1, is_delete=False).exists():
                    qs.dn_status = 2
                    dn_detail_list = DnDetailModel.objects.filter(openid=self.request.auth.openid, dn_code=qs.dn_code,
                                                                    dn_status=1, is_delete=False)
                    for i in range(len(dn_detail_list)):
                        if stocklist.objects.filter(openid=self.request.auth.openid,
                                                                    goods_code=str(dn_detail_list[i].goods_code)).exists():
                            pass
                        else:
                            goods_detail = goods.objects.filter(openid=self.request.auth.openid, goods_code=str(dn_detail_list[i].goods_code), is_delete=False).first()
                            stocklist.objects.create(openid=self.request.auth.openid,
                                                     goods_code=str(dn_detail_list[i].goods_code),
                                                     goods_desc=goods_detail.goods_desc,
                                                     supplier=goods_detail.goods_supplier)
                        goods_qty_change = stocklist.objects.filter(openid=self.request.auth.openid,
                                                                    goods_code=str(
                                                                        dn_detail_list[i].goods_code)).first()
                        goods_qty_change.can_order_stock = goods_qty_change.can_order_stock - dn_detail_list[i].goods_qty
                        goods_qty_change.ordered_stock = goods_qty_change.ordered_stock + dn_detail_list[i].goods_qty
                        goods_qty_change.dn_stock = goods_qty_change.dn_stock - dn_detail_list[i].goods_qty
                        if goods_qty_change.can_order_stock < 0:
                            goods_qty_change.can_order_stock = 0
                        goods_qty_change.save()
                    dn_detail_list.update(dn_status=2)
                    qs.save()
                    serializer = self.get_serializer(qs, many=False)
                    headers = self.get_success_headers(serializer.data)
                    return Response(serializer.data, status=200, headers=headers)
                else:
                    raise APIException({"detail": "Please Enter The DN Detail"})
            else:
                raise APIException({"detail": "This DN Status Is Not Pre Order"})

class DnOrderReleaseViewSet(viewsets.ModelViewSet):
    """
        retrieve:
            Response a data list（get）
    """
    pagination_class = MyPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnListFilter

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
                return DnListModel.objects.filter(openid=self.request.auth.openid, dn_status=2, is_delete=False).order_by('account_name','dn_code')
            else:
                return DnListModel.objects.filter(openid=self.request.auth.openid, dn_status=2, id=id, is_delete=False)
        else:
            return DnListModel.objects.none()

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return serializers.DNListUpdateSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def create(self, request, *args, **kwargs):
        #[Will] Rewrite the whole create function of pickinglist, to generate pickinglist with data from DNDetaillist and Bin info
        normalorder_set = DnDetailModel.objects.filter(openid=self.request.auth.openid, is_delete=False, dn_status__lte=2, dn_complete=2, sending_date__lte=datetime.today().replace(hour=23,minute=59,second=59))
        staff_name = staff.objects.filter(openid=self.request.auth.openid,
                                          id=self.request.META.get('HTTP_OPERATOR')).first().staff_name

        for i in range(len(normalorder_set)):
            label_id = normalorder_set[i].label_id
            bin_set = stockbin.objects.filter(goods_code=normalorder_set[i].goods_code, bin_property='Normal')
            tobepick_amount = normalorder_set[i].goods_qty
            picked_amount = 0
            for j in range(len(bin_set)):
                tobepick_amount = tobepick_amount - picked_amount
                if bin_set[j].goods_qty >= tobepick_amount:
                    picked_amount = tobepick_amount
                    if PickingListModel.objects.filter(orderitem_id=normalorder_set[i].orderitem_id,
                                                      is_delete=False).exists():
                       pick_list = PickingListModel.objects.filter(orderitem_id=normalorder_set[i].orderitem_id,
                                                      is_delete=False).first()
                       pick_list.dn_code=normalorder_set[i].dn_code
                       pick_list.goods_code=normalorder_set[i].goods_code
                       pick_list.goods_desc=normalorder_set[i].goods_desc
                       pick_list.picking_status=0
                       pick_list.orderitem_id=normalorder_set[i].orderitem_id
                       pick_list.account_name=normalorder_set[i].account_name
                       pick_list.customer=normalorder_set[i].customer
                       pick_list.picked_qty = picked_amount
                       pick_list.pick_qty=normalorder_set[i].goods_qty
                       pick_list.bin_name=bin_set[j].bin_name
                       pick_list.openid=self.request.auth.openid
                       pick_list.creater=str(staff_name)
                       pick_list.label_id = label_id
                       pick_list.save()
                    else:
                        PickingListModel.objects.create(dn_code=normalorder_set[i].dn_code,
                                                    goods_code=normalorder_set[i].goods_code,
                                                    goods_desc=normalorder_set[i].goods_desc,
                                                    picking_status=0,
                                                    orderitem_id=normalorder_set[i].orderitem_id,
                                                    account_name=normalorder_set[i].account_name,
                                                    customer=normalorder_set[i].customer,
                                                    pick_qty=normalorder_set[i].goods_qty,
                                                    picked_qty=picked_amount,
                                                    bin_name=bin_set[j].bin_name,
                                                    openid=self.request.auth.openid,
                                                    label_id=label_id,
                                                    creater=str(staff_name))

                    dn_list = DnListModel.objects.filter(dn_code=normalorder_set[i].dn_code, account_name=normalorder_set[i].account_name, is_delete=False).first()
                    dn_list.dn_status = 2
                    dn_list.save()
                    normalorder_set[i].dn_status = 2
                    normalorder_set[i].goods_cost = bin_set[j].goods_cost
                    normalorder_set[i].save()
                    break
                else:
                    picked_amount = bin_set[j].goods_qty
                    if PickingListModel.objects.filter(orderitem_id=normalorder_set[i].orderitem_id,
                                                      is_delete=False).exists():
                        pick_list = PickingListModel.objects.filter(orderitem_id=normalorder_set[i].orderitem_id,
                                                                    is_delete=False).first()
                        pick_list.dn_code = normalorder_set[i].dn_code
                        pick_list.goods_code = normalorder_set[i].goods_code
                        pick_list.goods_desc = normalorder_set[i].goods_desc
                        pick_list.picking_status = 0
                        pick_list.orderitem_id = normalorder_set[i].orderitem_id
                        pick_list.account_name = normalorder_set[i].account_name
                        pick_list.customer = normalorder_set[i].customer
                        pick_list.picked_qty = picked_amount
                        pick_list.pick_qty = normalorder_set[i].goods_qty
                        pick_list.bin_name = bin_set[j].bin_name
                        pick_list.openid = self.request.auth.openid
                        pick_list.creater = str(staff_name)
                        pick_list.label_id = label_id
                        normalorder_set[i].goods_cost = bin_set[j].goods_cost
                        normalorder_set[i].save()
                        pick_list.save()
                    else:
                        PickingListModel.objects.create(dn_code=normalorder_set[i].dn_code,
                                            goods_code=normalorder_set[i].goods_code,
                                            goods_desc=normalorder_set[i].goods_desc,
                                            picking_status=0,
                                            orderitem_id=normalorder_set[i].orderitem_id,
                                            account_name=normalorder_set[i].account_name,
                                            customer=normalorder_set[i].customer,
                                            pick_qty=normalorder_set[i].goods_qty,
                                            picked_qty=picked_amount,
                                            bin_name=bin_set[j].bin_name,
                                            openid=self.request.auth.openid,
                                            label_id=label_id,
                                            creater=str(staff_name))

        dnlist_list = DnListModel.objects.filter(openid=self.request.auth.openid,
                                                 dn_status__lte=2,
                                                 dn_complete=2,
                                                 is_delete=False,
                                                 sending_date__lte=datetime.today().replace(hour=23,minute=59,second=59)).order_by('account_name','dn_code')
        pdf_list = []
        for dnlist in dnlist_list:
            pdf_list.append(dnlist.account_name+dnlist.dn_code+".pdf")
        output_file = 'merged.pdf'
        merge_pdfs(pdf_list, output_file)
        return Response({'detail': 'success'}, status=200)

    def update(self, request, pk):
        qs = self.get_object()
        if qs.openid != self.request.auth.openid:
            raise APIException({"detail": "Cannot Release Order Data Which Not Yours"})
        else:
            if qs.dn_status == 2:
                staff_name = staff.objects.filter(openid=self.request.auth.openid,
                                                  id=self.request.META.get('HTTP_OPERATOR')).first().staff_name
                dn_detail_list = DnDetailModel.objects.filter(openid=self.request.auth.openid,
                                                              dn_code=qs.dn_code,
                                                              dn_status=2, is_delete=False)
                picking_list = []
                picking_list_label = 0
                back_order_list = []
                back_order_list_label = 0
                back_order_goods_weight_list = []
                back_order_goods_volume_list = []
                back_order_goods_cost_list = []
                back_order_base_code = DnListModel.objects.filter(openid=self.request.auth.openid, is_delete=False).order_by('-id').first().dn_code
                dn_last_code = re.findall(r'\d+', str(back_order_base_code), re.IGNORECASE)
                back_order_dn_code = 'DN' + str(int(dn_last_code[0]) + 1).zfill(8)
                bar_code = Md5.md5(back_order_dn_code)
                total_weight = qs.total_weight
                total_volume = qs.total_volume
                total_cost = qs.total_cost
                for i in range(len(dn_detail_list)):
                    goods_detail = goods.objects.filter(openid=self.request.auth.openid,
                                                        goods_code=str(dn_detail_list[i].goods_code),
                                                        is_delete=False).first()
                    if stocklist.objects.filter(openid=self.request.auth.openid,
                                                goods_code=str(dn_detail_list[i].goods_code)).exists():
                        pass
                    else:
                        stocklist.objects.create(openid=self.request.auth.openid,
                                                 goods_code=str(goods_detail.goods_code),
                                                 goods_desc=goods_detail.goods_desc,
                                                 dn_stock=int(dn_detail_list[i].goods_qty))
                    goods_qty_change = stocklist.objects.filter(openid=self.request.auth.openid,
                                                                goods_code=str(
                                                                    dn_detail_list[i].goods_code)).first()
                    goods_bin_stock_list = stockbin.objects.filter(openid=self.request.auth.openid,
                                                                   goods_code=str(dn_detail_list[i].goods_code),
                                                                   bin_property="Normal").order_by('id')
                    can_pick_qty = goods_qty_change.onhand_stock - \
                                   goods_qty_change.inspect_stock - \
                                   goods_qty_change.hold_stock - \
                                   goods_qty_change.damage_stock - \
                                   goods_qty_change.pick_stock - \
                                   goods_qty_change.picked_stock
                    if can_pick_qty > 0:
                        if dn_detail_list[i].goods_qty > can_pick_qty:
                            if qs.back_order_label == False:
                                dn_pick_qty = dn_detail_list[i].pick_qty
                                for j in range(len(goods_bin_stock_list)):
                                    bin_can_pick_qty = goods_bin_stock_list[j].goods_qty - \
                                                       goods_bin_stock_list[j].pick_qty - \
                                                       goods_bin_stock_list[j].picked_qty
                                    if bin_can_pick_qty > 0:
                                        goods_bin_stock_list[j].pick_qty = goods_bin_stock_list[
                                                                               j].pick_qty + bin_can_pick_qty
                                        goods_qty_change.ordered_stock = goods_qty_change.ordered_stock - bin_can_pick_qty
                                        goods_qty_change.pick_stock = goods_qty_change.pick_stock + bin_can_pick_qty
                                        picking_list.append(PickingListModel(openid=self.request.auth.openid,
                                                                             dn_code=dn_detail_list[i].dn_code,
                                                                             bin_name=goods_bin_stock_list[j].bin_name,
                                                                             goods_code=goods_bin_stock_list[
                                                                                 j].goods_code,
                                                                             pick_qty=bin_can_pick_qty,
                                                                             creater=str(staff_name),
                                                                             t_code=goods_bin_stock_list[j].t_code))
                                        picking_list_label = 1
                                        dn_pick_qty = dn_pick_qty + bin_can_pick_qty
                                        goods_qty_change.save()
                                        goods_bin_stock_list[j].save()
                                    elif bin_can_pick_qty == 0:
                                        continue
                                    else:
                                        continue
                                dn_detail_list[i].pick_qty = dn_pick_qty
                                dn_back_order_qty = dn_detail_list[i].goods_qty - \
                                                   dn_detail_list[i].pick_qty - \
                                                   dn_detail_list[i].picked_qty
                                dn_detail_list[i].goods_qty = dn_pick_qty
                                dn_detail_list[i].dn_status = 3
                                goods_qty_change.back_order_stock = goods_qty_change.back_order_stock + \
                                                                    dn_back_order_qty
                                back_order_goods_volume = round(goods_detail.unit_volume * dn_back_order_qty, 4)
                                back_order_goods_weight = round(
                                    (goods_detail.goods_weight * dn_back_order_qty) / 1000, 4)
                                back_order_goods_cost = round(goods_detail.goods_price * dn_back_order_qty, 2)
                                back_order_list.append(DnDetailModel(dn_code=back_order_dn_code,
                                                                     dn_status=2,
                                                                     customer=qs.customer,
                                                                     goods_code=dn_detail_list[i].goods_code,
                                                                     goods_qty=dn_back_order_qty,
                                                                     goods_weight=back_order_goods_weight,
                                                                     goods_volume=back_order_goods_volume,
                                                                     goods_cost=back_order_goods_cost,
                                                                     creater=str(staff_name),
                                                                     back_order_label=True,
                                                                     openid=self.request.auth.openid,
                                                                     create_time=dn_detail_list[i].create_time))
                                back_order_list_label = 1
                                total_weight = total_weight - back_order_goods_weight
                                total_volume = total_volume - back_order_goods_volume
                                total_cost = total_cost - back_order_goods_cost
                                dn_detail_list[i].goods_weight = dn_detail_list[i].goods_weight - \
                                                                 back_order_goods_weight
                                dn_detail_list[i].goods_volume = dn_detail_list[i].goods_volume - \
                                                                 back_order_goods_volume
                                dn_detail_list[i].goods_cost = dn_detail_list[i].goods_cost - \
                                                                 back_order_goods_cost
                                back_order_goods_weight_list.append(back_order_goods_weight)
                                back_order_goods_volume_list.append(back_order_goods_volume)
                                back_order_goods_cost_list.append(back_order_goods_cost)
                                goods_qty_change.save()
                                dn_detail_list[i].save()
                            else:
                                dn_pick_qty = dn_detail_list[i].pick_qty
                                for j in range(len(goods_bin_stock_list)):
                                    bin_can_pick_qty = goods_bin_stock_list[j].goods_qty - \
                                                       goods_bin_stock_list[j].pick_qty - \
                                                       goods_bin_stock_list[j].picked_qty
                                    if bin_can_pick_qty > 0:
                                        goods_bin_stock_list[j].pick_qty = goods_bin_stock_list[
                                                                               j].pick_qty + bin_can_pick_qty
                                        goods_qty_change.ordered_stock = goods_qty_change.ordered_stock - bin_can_pick_qty
                                        goods_qty_change.pick_stock = goods_qty_change.pick_stock + bin_can_pick_qty
                                        picking_list.append(PickingListModel(openid=self.request.auth.openid,
                                                                             dn_code=dn_detail_list[i].dn_code,
                                                                             bin_name=goods_bin_stock_list[j].bin_name,
                                                                             goods_code=goods_bin_stock_list[
                                                                                 j].goods_code,
                                                                             pick_qty=bin_can_pick_qty,
                                                                             creater=str(staff_name),
                                                                             t_code=goods_bin_stock_list[j].t_code))
                                        picking_list_label = 1
                                        dn_pick_qty = dn_pick_qty + bin_can_pick_qty
                                        goods_qty_change.save()
                                        goods_bin_stock_list[j].save()
                                    elif bin_can_pick_qty == 0:
                                        continue
                                    else:
                                        continue
                                dn_detail_list[i].pick_qty = dn_pick_qty
                                dn_back_order_qty = dn_detail_list[i].goods_qty - \
                                                    dn_detail_list[i].pick_qty - \
                                                    dn_detail_list[i].picked_qty
                                dn_detail_list[i].goods_qty = dn_pick_qty
                                dn_detail_list[i].dn_status = 3
                                back_order_goods_volume = round(goods_detail.unit_volume * dn_back_order_qty, 4)
                                back_order_goods_weight = round(
                                    (goods_detail.goods_weight * dn_back_order_qty) / 1000, 4)
                                back_order_goods_cost = round(goods_detail.goods_price * dn_back_order_qty, 2)
                                back_order_list.append(DnDetailModel(dn_code=back_order_dn_code,
                                                                     dn_status=2,
                                                                     customer=qs.customer,
                                                                     goods_code=dn_detail_list[i].goods_code,
                                                                     goods_qty=dn_back_order_qty,
                                                                     goods_weight=back_order_goods_weight,
                                                                     goods_volume=back_order_goods_volume,
                                                                     goods_cost=back_order_goods_cost,
                                                                     creater=str(staff_name),
                                                                     back_order_label=True,
                                                                     openid=self.request.auth.openid,
                                                                     create_time=dn_detail_list[i].create_time))
                                back_order_list_label = 1
                                total_weight = total_weight - back_order_goods_weight
                                total_volume = total_volume - back_order_goods_volume
                                total_cost = total_cost - back_order_goods_cost
                                dn_detail_list[i].goods_weight = dn_detail_list[i].goods_weight - \
                                                                 back_order_goods_weight
                                dn_detail_list[i].goods_volume = dn_detail_list[i].goods_volume - \
                                                                 back_order_goods_volume
                                dn_detail_list[i].goods_cost = dn_detail_list[i].goods_cost - \
                                                                 back_order_goods_cost
                                back_order_goods_weight_list.append(back_order_goods_weight)
                                back_order_goods_volume_list.append(back_order_goods_volume)
                                back_order_goods_cost_list.append(back_order_goods_cost)
                                dn_detail_list[i].save()
                        elif dn_detail_list[i].goods_qty == can_pick_qty:
                            for j in range(len(goods_bin_stock_list)):
                                bin_can_pick_qty = goods_bin_stock_list[j].goods_qty - goods_bin_stock_list[j].pick_qty - \
                                                   goods_bin_stock_list[j].picked_qty
                                if bin_can_pick_qty > 0:
                                    dn_need_pick_qty = dn_detail_list[i].goods_qty - dn_detail_list[i].pick_qty - dn_detail_list[i].picked_qty
                                    if dn_need_pick_qty > bin_can_pick_qty:
                                        goods_bin_stock_list[j].pick_qty = goods_bin_stock_list[
                                                                               j].pick_qty + bin_can_pick_qty
                                        goods_qty_change.ordered_stock = goods_qty_change.ordered_stock - bin_can_pick_qty
                                        goods_qty_change.pick_stock = goods_qty_change.pick_stock + bin_can_pick_qty
                                        picking_list.append(PickingListModel(openid=self.request.auth.openid,
                                                                             dn_code=dn_detail_list[i].dn_code,
                                                                             bin_name=goods_bin_stock_list[j].bin_name,
                                                                             goods_code=goods_bin_stock_list[j].goods_code,
                                                                             pick_qty=bin_can_pick_qty,
                                                                             creater=str(staff_name),
                                                                             t_code=goods_bin_stock_list[j].t_code))
                                        picking_list_label = 1
                                        dn_detail_list[i].pick_qty = dn_detail_list[i].pick_qty + bin_can_pick_qty
                                        goods_bin_stock_list[j].save()
                                        goods_qty_change.save()
                                    elif dn_need_pick_qty == bin_can_pick_qty:
                                        goods_bin_stock_list[j].pick_qty = goods_bin_stock_list[
                                                                               j].pick_qty + bin_can_pick_qty
                                        goods_qty_change.ordered_stock = goods_qty_change.ordered_stock - bin_can_pick_qty
                                        goods_qty_change.pick_stock = goods_qty_change.pick_stock + bin_can_pick_qty
                                        picking_list.append(PickingListModel(openid=self.request.auth.openid,
                                                                             dn_code=dn_detail_list[i].dn_code,
                                                                             bin_name=goods_bin_stock_list[j].bin_name,
                                                                             goods_code=goods_bin_stock_list[j].goods_code,
                                                                             pick_qty=bin_can_pick_qty,
                                                                             creater=str(staff_name),
                                                                             t_code=goods_bin_stock_list[j].t_code))
                                        picking_list_label = 1
                                        dn_detail_list[i].pick_qty = dn_detail_list[i].pick_qty + bin_can_pick_qty
                                        dn_detail_list[i].dn_status = 3
                                        dn_detail_list[i].save()
                                        goods_bin_stock_list[j].save()
                                        goods_qty_change.save()
                                        break
                                    else:
                                        break
                                elif bin_can_pick_qty == 0:
                                    continue
                                else:
                                    continue
                        elif dn_detail_list[i].goods_qty < can_pick_qty:
                            for j in range(len(goods_bin_stock_list)):
                                bin_can_pick_qty = goods_bin_stock_list[j].goods_qty - \
                                                   goods_bin_stock_list[j].pick_qty - \
                                                   goods_bin_stock_list[j].picked_qty
                                if bin_can_pick_qty > 0:
                                    dn_need_pick_qty = dn_detail_list[i].goods_qty - \
                                                       dn_detail_list[i].pick_qty - \
                                                       dn_detail_list[i].picked_qty
                                    if dn_need_pick_qty > bin_can_pick_qty:
                                        goods_bin_stock_list[j].pick_qty = goods_bin_stock_list[j].pick_qty + \
                                                                           bin_can_pick_qty
                                        goods_qty_change.ordered_stock = goods_qty_change.ordered_stock - \
                                                                         bin_can_pick_qty
                                        goods_qty_change.pick_stock = goods_qty_change.pick_stock + \
                                                                      bin_can_pick_qty
                                        picking_list.append(PickingListModel(openid=self.request.auth.openid,
                                                                             dn_code=dn_detail_list[i].dn_code,
                                                                             bin_name=goods_bin_stock_list[j].bin_name,
                                                                             goods_code=goods_bin_stock_list[j].goods_code,
                                                                             pick_qty=bin_can_pick_qty,
                                                                             creater=str(staff_name),
                                                                             t_code=goods_bin_stock_list[j].t_code))
                                        picking_list_label = 1
                                        dn_detail_list[i].pick_qty = dn_detail_list[i].pick_qty + \
                                                                     bin_can_pick_qty
                                        dn_detail_list[i].save()
                                        goods_bin_stock_list[j].save()
                                        goods_qty_change.save()
                                    elif dn_need_pick_qty == bin_can_pick_qty:
                                        goods_bin_stock_list[j].pick_qty = goods_bin_stock_list[
                                                                               j].pick_qty + bin_can_pick_qty
                                        goods_qty_change.ordered_stock = goods_qty_change.ordered_stock - bin_can_pick_qty
                                        goods_qty_change.pick_stock = goods_qty_change.pick_stock + bin_can_pick_qty
                                        picking_list.append(PickingListModel(openid=self.request.auth.openid,
                                                                             dn_code=dn_detail_list[i].dn_code,
                                                                             bin_name=goods_bin_stock_list[j].bin_name,
                                                                             goods_code=goods_bin_stock_list[j].goods_code,
                                                                             pick_qty=bin_can_pick_qty,
                                                                             creater=str(staff_name),
                                                                             t_code=goods_bin_stock_list[j].t_code))
                                        picking_list_label = 1
                                        dn_detail_list[i].pick_qty = dn_detail_list[i].pick_qty + bin_can_pick_qty
                                        dn_detail_list[i].dn_status = 3
                                        dn_detail_list[i].save()
                                        goods_bin_stock_list[j].save()
                                        goods_qty_change.save()
                                        break
                                    elif dn_need_pick_qty < bin_can_pick_qty:
                                        goods_bin_stock_list[j].pick_qty = goods_bin_stock_list[j].pick_qty + \
                                                                           dn_need_pick_qty
                                        goods_qty_change.ordered_stock = goods_qty_change.ordered_stock - \
                                                                         dn_need_pick_qty
                                        goods_qty_change.pick_stock = goods_qty_change.pick_stock + \
                                                                      dn_need_pick_qty
                                        picking_list.append(PickingListModel(openid=self.request.auth.openid,
                                                                             dn_code=dn_detail_list[i].dn_code,
                                                                             bin_name=goods_bin_stock_list[j].bin_name,
                                                                             goods_code=goods_bin_stock_list[j].goods_code,
                                                                             pick_qty=dn_need_pick_qty,
                                                                             creater=str(staff_name),
                                                                             t_code=goods_bin_stock_list[j].t_code))
                                        picking_list_label = 1
                                        dn_detail_list[i].pick_qty = dn_detail_list[i].pick_qty + dn_need_pick_qty
                                        dn_detail_list[i].dn_status = 3
                                        dn_detail_list[i].save()
                                        goods_bin_stock_list[j].save()
                                        goods_qty_change.save()
                                        break
                                    else:
                                        break
                                elif bin_can_pick_qty == 0:
                                    continue
                                else:
                                    continue
                    elif can_pick_qty == 0:
                        if qs.back_order_label == False:
                            goods_qty_change.back_order_stock = goods_qty_change.back_order_stock + dn_detail_list[i].goods_qty
                            back_order_goods_volume = round(goods_detail.unit_volume * dn_detail_list[i].goods_qty, 4)
                            back_order_goods_weight = round((goods_detail.goods_weight * dn_detail_list[i].goods_qty) / 1000, 4)
                            back_order_goods_cost = round(goods_detail.goods_price * dn_detail_list[i].goods_qty, 2)
                            back_order_list.append(DnDetailModel(dn_code=back_order_dn_code,
                                                                 dn_status=2,
                                                                 customer=qs.customer,
                                                                 goods_code=dn_detail_list[i].goods_code,
                                                                 goods_qty=dn_detail_list[i].goods_qty,
                                                                 goods_weight=back_order_goods_weight,
                                                                 goods_volume=back_order_goods_volume,
                                                                 goods_cost=back_order_goods_cost,
                                                                 creater=str(staff_name),
                                                                 back_order_label=True,
                                                                 openid=self.request.auth.openid,
                                                                 create_time=dn_detail_list[i].create_time))
                            back_order_list_label = 1
                            total_weight = total_weight - back_order_goods_weight
                            total_volume = total_volume - back_order_goods_volume
                            total_cost = total_cost - back_order_goods_cost
                            back_order_goods_weight_list.append(back_order_goods_weight)
                            back_order_goods_volume_list.append(back_order_goods_volume)
                            back_order_goods_cost_list.append(back_order_goods_cost)
                            dn_detail_list[i].is_delete = True
                            dn_detail_list[i].save()
                            goods_qty_change.save()
                        else:
                            continue
                    else:
                        continue
                if picking_list_label == 1:
                    if back_order_list_label == 1:
                        back_order_total_volume = sumOfList(back_order_goods_volume_list,
                                                            len(back_order_goods_volume_list))
                        back_order_total_weight = sumOfList(back_order_goods_weight_list,
                                                            len(back_order_goods_weight_list))
                        back_order_total_cost = sumOfList(back_order_goods_cost_list,
                                                            len(back_order_goods_cost_list))
                        customer_city = customer.objects.filter(openid=self.request.auth.openid,
                                                                customer_name=str(qs.customer),
                                                                is_delete=False).first().customer_city
                        warehouse_city = warehouse.objects.filter(
                            openid=self.request.auth.openid, is_delete=False).first().warehouse_city
                        transportation_fee = transportation.objects.filter(
                            Q(openid=self.request.auth.openid, send_city__icontains=warehouse_city,
                              receiver_city__icontains=customer_city,
                              is_delete=False) | Q(openid='init_data', send_city__icontains=warehouse_city,
                                                   receiver_city__icontains=customer_city,
                                                   is_delete=False))
                        transportation_res = {
                            "detail": []
                        }
                        transportation_back_order_res = {
                            "detail": []
                        }
                        if len(transportation_fee) >= 1:
                            transportation_list = []
                            transportation_back_order_list = []
                            for k in range(len(transportation_fee)):
                                transportation_cost = transportation_calculate(total_weight,
                                                                               total_volume,
                                                                               transportation_fee[k].weight_fee,
                                                                               transportation_fee[k].volume_fee,
                                                                               transportation_fee[k].min_payment)
                                transportation_back_order_cost = transportation_calculate(back_order_total_weight,
                                                                               back_order_total_volume,
                                                                               transportation_fee[k].weight_fee,
                                                                               transportation_fee[k].volume_fee,
                                                                               transportation_fee[k].min_payment)
                                transportation_detail = {
                                    "transportation_supplier": transportation_fee[k].transportation_supplier,
                                    "transportation_cost": transportation_cost
                                }
                                transportation_back_order_detail = {
                                    "transportation_supplier": transportation_fee[k].transportation_supplier,
                                    "transportation_cost": transportation_back_order_cost
                                }
                                transportation_list.append(transportation_detail)
                                transportation_back_order_list.append(transportation_back_order_detail)
                            transportation_res['detail'] = transportation_list
                            transportation_back_order_res['detail'] = transportation_back_order_list
                        DnListModel.objects.create(openid=self.request.auth.openid,
                                                   dn_code=back_order_dn_code,
                                                   dn_status=2,
                                                   total_weight=back_order_total_weight,
                                                   total_volume=back_order_total_volume,
                                                   total_cost=back_order_total_cost,
                                                   customer=qs.customer,
                                                   creater=str(staff_name),
                                                   bar_code=bar_code,
                                                   back_order_label=True,
                                                   transportation_fee=transportation_back_order_res,
                                                   create_time=qs.create_time)
                        scanner.objects.create(openid=self.request.auth.openid, mode="DN", code=back_order_dn_code,
                                               bar_code=bar_code)
                        PickingListModel.objects.bulk_create(picking_list, batch_size=100)
                        DnDetailModel.objects.bulk_create(back_order_list, batch_size=100)
                        qs.total_weight = total_weight
                        qs.total_volume = total_volume
                        qs.total_cost = total_cost
                        qs.transportation_fee = transportation_res
                        qs.dn_status = 3
                        qs.save()
                    elif back_order_list_label == 0:
                        PickingListModel.objects.bulk_create(picking_list, batch_size=100)
                        qs.dn_status = 3
                        qs.save()
                elif picking_list_label == 0:
                    if back_order_list_label == 1:
                        DnDetailModel.objects.bulk_create(back_order_list, batch_size=100)
                        DnListModel.objects.create(openid=self.request.auth.openid,
                                                   dn_code=back_order_dn_code,
                                                   dn_status=2,
                                                   total_weight=qs.total_weight,
                                                   total_volume=qs.total_volume,
                                                   total_cost=qs.total_cost,
                                                   customer=qs.customer,
                                                   creater=str(staff_name),
                                                   bar_code=bar_code,
                                                   back_order_label=True,
                                                   transportation_fee=qs.transportation_fee,
                                                   create_time=qs.create_time)
                        scanner.objects.create(openid=self.request.auth.openid, mode="DN", code=back_order_dn_code,
                                               bar_code=bar_code)
                        qs.is_delete = True
                        qs.dn_status = 3
                        qs.save()
                return Response({"detail": "success"}, status=200)
            else:
                raise APIException({"detail": "This Order Does Not in Release Status"})

class DnPickingListViewSet(viewsets.ModelViewSet):
    """
        retrieve:
            Picklist for pk
    """
    pagination_class = MyPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnListFilter

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_queryset(self):
        id = self.get_project()
        if self.request.user:
            return DnListModel.objects.filter(openid=self.request.auth.openid, id=id, is_delete=False)
        else:
            return DnListModel.objects.none()

    def get_serializer_class(self):
        if self.action in ['retrieve']:
            return serializers.DNListGetSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def retrieve(self, request, pk):
        qs = self.get_object()
        if qs.dn_status < 3:
            raise APIException({"detail": "No Picking List Been Created"})
        else:
            picking_qs = PickingListModel.objects.filter(openid=self.request.auth.openid, dn_code=qs.dn_code, is_delete=False)
            serializer = serializers.DNPickingListGetSerializer(picking_qs, many=True)
            return Response(serializer.data, status=200)

class DnPickingListFilterViewSet(viewsets.ModelViewSet):
    """
        list:
            Picklist for Filter
    """
    pagination_class = MyPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnPickingListFilter

    def get_queryset(self):
        if self.request.user:
            return PickingListModel.objects.filter(openid=self.request.auth.openid,
                                                   picking_status=0,
                                                   is_delete=False).order_by('account_name','dn_code')
        else:
            return PickingListModel.objects.none()

    def get_serializer_class(self):
        if self.action in ['list']:
            return serializers.DNPickingCheckGetSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def create(self, request, *args, **kwargs):
        pick_list = PickingListModel.objects.filter(openid=self.request.auth.openid,picking_status=0, is_delete=False)

        for i in range(len(pick_list)):
            pick_list[i].picking_status = 1
            pick_list[i].picked_qty = pick_list[i].pick_qty
            tobe_picked = pick_list[i].picked_qty
            pick_list[i].intransit_qty = pick_list[i].pick_qty
            pick_list[i].save()
            stockbin_list = stockbin.objects.filter(bin_name=pick_list[i].bin_name, goods_code=pick_list[i].goods_code)
            for stockbin_item in stockbin_list:
                if stockbin_item.goods_qty >= tobe_picked:
                    stockbin_item.goods_qty = stockbin_item.goods_qty - tobe_picked
                    stockbin_item.save()
                    break
                else:
                    tobe_picked = tobe_picked - stockbin_item.goods_qty
                    stockbin_item.goods_qty = 0
                    stockbin_item.save()
            stocklist_list = stocklist.objects.filter(goods_code=pick_list[i].goods_code).first()
            stocklist_list.can_order_stock = stocklist_list.can_order_stock - pick_list[i].picked_qty
            stocklist_list.onhand_stock = stocklist_list.onhand_stock - pick_list[i].picked_qty
            stocklist_list.save()
            orderItems = []
            orderItems.append({'orderItemId': pick_list[i].orderitem_id})
            shipment_data = {"orderItems": orderItems,"shippingLabelId": pick_list[i].label_id }
            headers = {
                "Authorization": "Bearer " + obtain_access_token(pick_list[i].account_name),
                "Accept": "application/vnd.retailer.v8+json",
                "Content-Type": "application/vnd.retailer.v8+json"
            }
            result = requests.put(shipment_url, json.dumps(shipment_data), headers=headers)

        dn_list = DnListModel.objects.filter(openid=self.request.auth.openid,dn_status=2, is_delete=0)
        for i in range(len(dn_list)):
            dn_list[i].dn_status = 4
            dn_list[i].save()
        dn_detail = DnDetailModel.objects.filter(openid=self.request.auth.openid,dn_status=2, is_delete=0)
        for j in range(len(dn_detail)):
            dn_detail[j].dn_status = 4
            dn_detail[j].save()

        ObtainfinanceData()

        return Response({"detail": "success"}, status=200)


class DnPickedViewSet(viewsets.ModelViewSet):
    """
        create:
            Finish Picked
    """
    pagination_class = MyPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnListFilter

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
                return DnListModel.objects.filter(openid=self.request.auth.openid, is_delete=False)
            else:
                return DnListModel.objects.filter(openid=self.request.auth.openid, id=id, is_delete=False)
        else:
            return DnListModel.objects.none()

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return serializers.DNListUpdateSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def create(self, request, pk):
        qs = self.get_object()
        if qs.dn_status != 3:
            raise APIException({"detail": "This dn Status Not Pre Pick"})
        else:
            data = self.request.data
            for i in range(len(data['goodsData'])):
                pick_qty_change = PickingListModel.objects.filter(openid=self.request.auth.openid,
                                                                  dn_code=str(data['dn_code']),
                                                                  picking_status=0,
                                                                  t_code=str(data['goodsData'][i].get('t_code')), is_delete=False).first()
                if int(data['goodsData'][i].get('pick_qty')) < 0:
                    raise APIException({"detail": str(data['goodsData'][i].get('goods_code')) + " Picked Qty Must >= 0"})
                else:
                    if int(data['goodsData'][i].get('pick_qty')) > pick_qty_change.pick_qty:
                        raise APIException({"detail": str(data['goodsData'][i].get('goods_code')) + " Picked Qty Must Less Than Pick Qty"})
                    else:
                        continue
            qs.dn_status = 4
            staff_name = staff.objects.filter(openid=self.request.auth.openid,
                                              id=self.request.META.get('HTTP_OPERATOR')).first().staff_name
            for j in range(len(data['goodsData'])):
                goods_qty_change = stocklist.objects.filter(openid=self.request.auth.openid,
                                                            goods_code=str(data['goodsData'][j].get('goods_code'))).first()
                dn_detail = DnDetailModel.objects.filter(openid=self.request.auth.openid,
                                                         dn_code=str(data['dn_code']),
                                                         customer=str(data['customer']),
                                                         goods_code=str(data['goodsData'][j].get('goods_code'))).first()
                bin_qty_change = stockbin.objects.filter(openid=self.request.auth.openid,
                                                         t_code=str(data['goodsData'][j].get('t_code'))).first()
                pick_qty_change = PickingListModel.objects.filter(openid=self.request.auth.openid,
                                                                  dn_code=str(data['dn_code']),
                                                                  picking_status=0,
                                                                  t_code=str(data['goodsData'][j].get('t_code'))).first()
                qtychangerecorder.objects.create(openid=self.request.auth.openid,
                                                 mode_code=dn_detail.dn_code,
                                                 bin_name=bin_qty_change.bin_name,
                                                 goods_code=bin_qty_change.goods_code,
                                                 goods_desc=bin_qty_change.goods_desc,
                                                 goods_qty=0 - int(data['goodsData'][j].get('pick_qty')),
                                                 creater=str(staff_name)
                                                 )
                cur_date = timezone.now().date()
                bin_stock = stockbin.objects.filter(openid=self.request.auth.openid,
                                                    bin_name=bin_qty_change.bin_name,
                                                    goods_code=bin_qty_change.goods_code).aggregate(sum=Sum('goods_qty'))["sum"]
                cycle_qty = bin_stock - int(data['goodsData'][j].get('pick_qty'))
                cyclecount.objects.filter(openid=self.request.auth.openid,
                                          bin_name=bin_qty_change.bin_name,
                                          goods_code=bin_qty_change.goods_code,
                                          create_time__gte=cur_date, is_delete=False).update(goods_qty=cycle_qty)
                if int(data['goodsData'][j].get('pick_qty')) == pick_qty_change.pick_qty:
                    goods_qty_change.pick_stock = goods_qty_change.pick_stock - int(data['goodsData'][j].get('pick_qty'))
                    goods_qty_change.picked_stock = goods_qty_change.picked_stock + int(data['goodsData'][j].get('pick_qty'))
                    pick_qty_change.picked_qty = int(data['goodsData'][j].get('pick_qty'))
                    pick_qty_change.picking_status = 1
                    bin_qty_change.pick_qty = bin_qty_change.pick_qty - int(data['goodsData'][j].get('pick_qty'))
                    bin_qty_change.picked_qty = bin_qty_change.picked_qty + int(data['goodsData'][j].get('pick_qty'))
                    goods_qty_change.save()
                    pick_qty_change.save()
                    bin_qty_change.save()
                elif int(data['goodsData'][j].get('pick_qty')) < pick_qty_change.pick_qty:
                    goods_qty_change.pick_stock = goods_qty_change.pick_stock - dn_detail.pick_qty
                    goods_qty_change.picked_stock = goods_qty_change.picked_stock + int(data['goodsData'][j].get('pick_qty'))
                    goods_qty_change.can_order_stock = goods_qty_change.can_order_stock + (int(pick_qty_change.pick_qty) - int(
                        data['goodsData'][j].get('pick_qty')))
                    pick_qty_change.picked_qty = int(data['goodsData'][j].get('pick_qty'))
                    pick_qty_change.picking_status = 1
                    bin_qty_change.pick_qty = bin_qty_change.pick_qty - pick_qty_change.pick_qty
                    bin_qty_change.picked_qty = bin_qty_change.picked_qty + int(data['goodsData'][j].get('pick_qty'))
                    goods_qty_change.save()
                    pick_qty_change.save()
                    bin_qty_change.save()
                dn_detail.picked_qty = dn_detail.picked_qty + int(data['goodsData'][j].get('pick_qty'))
                if dn_detail.dn_status == 3:
                    dn_detail.dn_status = 4
                if dn_detail.pick_qty > 0:
                    dn_detail.pick_qty = 0
                dn_detail.save()
            qs.save()
            return Response({"Detail": "success"}, status=200)

    def update(self, request, *args, **kwargs):
        data = self.request.data
        qs = self.get_queryset().filter(dn_code=data['dn_code']).first()
        if qs.dn_status != 3:
            raise APIException({"detail": "This dn Status Not Pre Pick"})
        else:
            for i in range(len(data['goodsData'])):
                pick_qty_change = PickingListModel.objects.filter(openid=self.request.auth.openid,
                                                                  dn_code=str(data['dn_code']),
                                                                  picking_status=0,
                                                                  t_code=str(
                                                                      data['goodsData'][i].get('t_code')), is_delete=False).first()
                if int(data['goodsData'][i].get('picked_qty')) < 0:
                    raise APIException(
                        {"detail": str(data['goodsData'][i].get('goods_code')) + " Picked Qty Must >= 0"})
                else:
                    if int(data['goodsData'][i].get('picked_qty')) > pick_qty_change.pick_qty:
                        raise APIException(
                            {"detail": str(
                                data['goodsData'][i].get('goods_code')) + " Picked Qty Must Less Than Pick Qty"})
                    else:
                        continue
            qs.dn_status = 4
            staff_name = staff.objects.filter(openid=self.request.auth.openid,
                                              id=self.request.META.get('HTTP_OPERATOR')).first().staff_name
            for j in range(len(data['goodsData'])):
                goods_qty_change = stocklist.objects.filter(openid=self.request.auth.openid,
                                                            goods_code=str(
                                                                data['goodsData'][j].get('goods_code'))).first()
                dn_detail = DnDetailModel.objects.filter(openid=self.request.auth.openid,
                                                         dn_code=str(data['dn_code']),
                                                         goods_code=str(data['goodsData'][j].get('goods_code')), is_delete=False).first()
                bin_qty_change = stockbin.objects.filter(openid=self.request.auth.openid,
                                                         t_code=str(data['goodsData'][j].get('t_code'))).first()
                pick_qty_change = PickingListModel.objects.filter(openid=self.request.auth.openid,
                                                                  dn_code=str(data['dn_code']),
                                                                  picking_status=0,
                                                                  t_code=str(
                                                                      data['goodsData'][j].get('t_code')), is_delete=False).first()
                qtychangerecorder.objects.create(openid=self.request.auth.openid,
                                                 mode_code=dn_detail.dn_code,
                                                 bin_name=bin_qty_change.bin_name,
                                                 goods_code=bin_qty_change.goods_code,
                                                 goods_desc=bin_qty_change.goods_desc,
                                                 goods_qty=0 - int(data['goodsData'][j].get('picked_qty')),
                                                 creater=str(staff_name)
                                                 )
                cur_date = timezone.now().date()
                bin_stock = stockbin.objects.filter(openid=self.request.auth.openid,
                                                    bin_name=bin_qty_change.bin_name,
                                                    goods_code=bin_qty_change.goods_code).aggregate(sum=Sum('goods_qty'))["sum"]
                cycle_qty = bin_stock - int(data['goodsData'][j].get('picked_qty'))
                cyclecount.objects.filter(openid=self.request.auth.openid,
                                          bin_name=bin_qty_change.bin_name,
                                          goods_code=bin_qty_change.goods_code,
                                          create_time__gte=cur_date, is_delete=False).update(goods_qty=cycle_qty)
                if int(data['goodsData'][j].get('picked_qty')) == pick_qty_change.pick_qty:
                    goods_qty_change.pick_stock = goods_qty_change.pick_stock - int(
                        data['goodsData'][j].get('picked_qty'))
                    goods_qty_change.picked_stock = goods_qty_change.picked_stock + int(
                        data['goodsData'][j].get('picked_qty'))
                    pick_qty_change.picked_qty = int(data['goodsData'][j].get('picked_qty'))
                    pick_qty_change.picking_status = 1
                    bin_qty_change.pick_qty = bin_qty_change.pick_qty - int(data['goodsData'][j].get('picked_qty'))
                    bin_qty_change.picked_qty = bin_qty_change.picked_qty + int(data['goodsData'][j].get('picked_qty'))
                    goods_qty_change.save()
                    pick_qty_change.save()
                    bin_qty_change.save()
                elif int(data['goodsData'][j].get('picked_qty')) < pick_qty_change.pick_qty:
                    goods_qty_change.pick_stock = goods_qty_change.pick_stock - dn_detail.pick_qty
                    goods_qty_change.picked_stock = goods_qty_change.picked_stock + int(
                        data['goodsData'][j].get('picked_qty'))
                    pick_qty_change.picked_qty = int(data['goodsData'][j].get('picked_qty'))
                    pick_qty_change.picking_status = 1
                    bin_qty_change.pick_qty = bin_qty_change.pick_qty - pick_qty_change.pick_qty
                    bin_qty_change.picked_qty = bin_qty_change.picked_qty + int(data['goodsData'][j].get('picked_qty'))
                    goods_qty_change.save()
                    pick_qty_change.save()
                    bin_qty_change.save()
                dn_detail.picked_qty = dn_detail.picked_qty + int(data['goodsData'][j].get('picked_qty'))
                if dn_detail.dn_status == 3:
                    dn_detail.dn_status = 4
                if dn_detail.pick_qty > 0:
                    dn_detail.pick_qty = 0
                dn_detail.save()
            qs.save()
            return Response({"Detail": "success"}, status=200)

class DnDispatchViewSet(viewsets.ModelViewSet):
    """
        create:
            Confirm Dispatch
    """
    pagination_class = MyPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnListFilter

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_queryset(self):
        id = self.get_project()
        if self.request.user:
            return DnListModel.objects.filter(openid=self.request.auth.openid, id=id, is_delete=False)
        else:
            return DnListModel.objects.none()

    def get_serializer_class(self):
        if self.action in ['create']:
            return serializers.DNListUpdateSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def create(self, request, pk):
        qs = self.get_object()
        if qs.dn_status != 4:
            raise APIException({"detail": "This DN Status Not Picked"})
        else:
            qs.dn_status = 5
            data = self.request.data
            staff_name = staff.objects.filter(openid=self.request.auth.openid,
                                              id=self.request.META.get('HTTP_OPERATOR')).first().staff_name
            if driverlist.objects.filter(openid=self.request.auth.openid,
                                         driver_name=str(data['driver']),
                                         is_delete=False).exists():
                driver = driverlist.objects.filter(openid=self.request.auth.openid,
                                                   driver_name=str(data['driver']),
                                                   is_delete=False).first()
                dn_detail = DnDetailModel.objects.filter(openid=self.request.auth.openid,
                                                         dn_code=str(data['dn_code']),
                                                         dn_status=4, customer=qs.customer,
                                                         is_delete=False)
                pick_qty_change = PickingListModel.objects.filter(openid=self.request.auth.openid,
                                                                  dn_code=str(data['dn_code']), is_delete=False)
                for i in range(len(dn_detail)):
                    goods_qty_change = stocklist.objects.filter(openid=self.request.auth.openid,
                                                                goods_code=dn_detail[i].goods_code).first()
                    goods_qty_change.goods_qty = goods_qty_change.goods_qty - dn_detail[i].picked_qty
                    goods_qty_change.onhand_stock = goods_qty_change.onhand_stock - dn_detail[i].picked_qty
                    goods_qty_change.picked_stock = goods_qty_change.picked_stock - dn_detail[i].picked_qty
                    dn_detail[i].dn_status = 5
                    dn_detail[i].intransit_qty = dn_detail[i].picked_qty
                    dn_detail[i].save()
                    goods_qty_change.save()
                    if goods_qty_change.goods_qty == 0 and goods_qty_change.back_order_stock == 0:
                        goods_qty_change.delete()
                for j in range(len(pick_qty_change)):
                    bin_qty_change = stockbin.objects.filter(openid=self.request.auth.openid,
                                                             goods_code=pick_qty_change[j].goods_code,
                                                             bin_name=pick_qty_change[j].bin_name,
                                                             t_code=pick_qty_change[j].t_code).first()
                    bin_qty_change.goods_qty = bin_qty_change.goods_qty - pick_qty_change[j].picked_qty
                    if bin_qty_change.goods_qty == 0:
                        bin_qty_change.delete()
                        if stockbin.objects.filter(openid=self.request.auth.openid,
                                                   bin_name=pick_qty_change[j].bin_name, is_delete=False).exists():
                            pass
                        else:
                            binset.objects.filter(openid=self.request.auth.openid,
                                                  bin_name=pick_qty_change[j].bin_name, is_delete=False).update(empty_label=True)
                    else:
                        bin_qty_change.picked_qty = bin_qty_change.picked_qty - pick_qty_change[j].picked_qty
                        bin_qty_change.save()
                driverdispatch.objects.create(openid=self.request.auth.openid,
                                              driver_name=driver.driver_name,
                                              dn_code=str(data['dn_code']),
                                              contact=driver.contact,
                                              creater=str(staff_name))
                qs.save()
                return Response({"detail": "success"}, status=200)
            else:
                raise APIException({"detail": "Driver Does Not Exists"})

class DnPODViewSet(viewsets.ModelViewSet):
    """
        create:
            Confirm Dispatch
    """
    pagination_class = MyPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnListFilter

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_queryset(self):
        id = self.get_project()
        if self.request.user:
            return DnListModel.objects.filter(openid=self.request.auth.openid, id=id, is_delete=False)
        else:
            return DnListModel.objects.none()

    def get_serializer_class(self):
        if self.action in ['create']:
            return serializers.DNListUpdateSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def create(self, request, pk):
        qs = self.get_object()
        if qs.dn_status != 5:
            raise APIException({"detail": "This DN Status Not Intran-Sit"})
        else:
            qs.dn_status = 6
            data = self.request.data
            for i in range(len(data['goodsData'])):
                delivery_damage_qty = data['goodsData'][i].get('delivery_damage_qty')
                delivery_actual_qty = data['goodsData'][i].get('intransit_qty')
                if delivery_actual_qty < 0:
                    raise APIException({"detail": "Delivery Actual QTY Must >= 0"})
                else:
                    if delivery_damage_qty < 0:
                        raise APIException({"detail": "Delivery Damage QTY Must >= 0"})
            dn_detail = DnDetailModel.objects.filter(openid=self.request.auth.openid,
                                                     dn_code=str(data['dn_code']),
                                                     dn_status=5, customer=qs.customer,
                                                     is_delete=False)
            for j in range(len(data['goodsData'])):
                delivery_damage_qty = data['goodsData'][j].get('delivery_damage_qty')
                delivery_actual_qty = data['goodsData'][j].get('intransit_qty')
                goods_code = data['goodsData'][j].get('goods_code')
                if delivery_damage_qty > 0:
                    goods_detail = dn_detail.filter(goods_code=goods_code).first()
                    if delivery_actual_qty > goods_detail.intransit_qty:
                        goods_detail.delivery_actual_qty = delivery_actual_qty
                        goods_detail.delivery_more_qty = delivery_actual_qty - goods_detail.intransit_qty
                        goods_detail.delivery_damage_qty = delivery_damage_qty
                        goods_detail.intransit_qty = 0
                        goods_detail.dn_status = 6
                    elif delivery_actual_qty < goods_detail.intransit_qty:
                        goods_detail.delivery_actual_qty = delivery_actual_qty
                        goods_detail.delivery_shortage_qty = goods_detail.intransit_qty - delivery_actual_qty
                        goods_detail.delivery_damage_qty = delivery_damage_qty
                        goods_detail.intransit_qty = 0
                        goods_detail.dn_status = 6
                    elif delivery_actual_qty == goods_detail.intransit_qty:
                        goods_detail.delivery_actual_qty = delivery_actual_qty
                        goods_detail.delivery_damage_qty = delivery_damage_qty
                        goods_detail.intransit_qty = 0
                        goods_detail.dn_status = 6
                    else:
                        continue
                    goods_detail.save()
                elif delivery_damage_qty == 0:
                    goods_detail = dn_detail.filter(goods_code=goods_code).first()
                    if delivery_actual_qty > goods_detail.intransit_qty:
                        goods_detail.delivery_actual_qty = delivery_actual_qty
                        goods_detail.delivery_more_qty = delivery_actual_qty - goods_detail.intransit_qty
                        goods_detail.intransit_qty = 0
                        goods_detail.dn_status = 6
                    elif delivery_actual_qty < goods_detail.intransit_qty:
                        goods_detail.delivery_actual_qty = delivery_actual_qty
                        goods_detail.delivery_shortage_qty = goods_detail.intransit_qty - delivery_actual_qty
                        goods_detail.intransit_qty = 0
                        goods_detail.dn_status = 6
                    elif delivery_actual_qty == goods_detail.intransit_qty:
                        goods_detail.delivery_actual_qty = delivery_actual_qty
                        goods_detail.intransit_qty = 0
                        goods_detail.dn_status = 6
                    else:
                        continue
                    goods_detail.save()
            qs.save()
            return Response({"detail": "success"}, status=200)

class FileListDownloadView(viewsets.ModelViewSet):
    renderer_classes = (FileListRenderCN, ) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnListFilter

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_queryset(self):
        id = self.get_project()
        if self.request.user:
            empty_qs = DnListModel.objects.filter(
                Q(openid=self.request.auth.openid, dn_status=1, is_delete=False) & Q(customer=''))
            cur_date = timezone.now()
            date_check = relativedelta(day=1)
            if len(empty_qs) > 0:
                for i in range(len(empty_qs)):
                    if empty_qs[i].create_time <= cur_date - date_check:
                        empty_qs[i].delete()
            if id is None:
                return DnListModel.objects.filter(
                    Q(openid=self.request.auth.openid, is_delete=False) & ~Q(customer=''))
            else:
                return DnListModel.objects.filter(
                    Q(openid=self.request.auth.openid, id=id, is_delete=False) & ~Q(customer=''))
        else:
            return DnListModel.objects.none()

    def get_serializer_class(self):
        if self.action in ['list']:
            return serializers.FileListRenderSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def get_lang(self, data):
        lang = self.request.META.get('HTTP_LANGUAGE')
        if lang:
            if lang == 'zh-hans':
                return FileListRenderCN().render(data)
            else:
                return FileListRenderEN().render(data)
        else:
            return FileListRenderEN().render(data)

    def list(self, request, *args, **kwargs):
        from datetime import datetime
        dt = datetime.now()
        data = (
            FileListRenderSerializer(instance).data
            for instance in self.filter_queryset(self.get_queryset())
        )
        renderer = self.get_lang(data)
        response = StreamingHttpResponse(
            renderer,
            content_type="text/csv"
        )
        response['Content-Disposition'] = "attachment; filename='dnlist_{}.csv'".format(str(dt.strftime('%Y%m%d%H%M%S%f')))
        return response

class FileDetailDownloadView(viewsets.ModelViewSet):
    renderer_classes = (FileDetailRenderCN, ) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnDetailFilter

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
                return DnDetailModel.objects.filter(openid=self.request.auth.openid, is_delete=False)
            else:
                return DnDetailModel.objects.filter(openid=self.request.auth.openid, id=id, is_delete=False)
        else:
            return DnDetailModel.objects.none()

    def get_serializer_class(self):
        if self.action in ['list']:
            return serializers.FileDetailRenderSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def get_lang(self, data):
        lang = self.request.META.get('HTTP_LANGUAGE')
        if lang:
            if lang == 'zh-hans':
                return FileDetailRenderCN().render(data)
            else:
                return FileDetailRenderEN().render(data)
        else:
            return FileDetailRenderEN().render(data)

    def list(self, request, *args, **kwargs):
        from datetime import datetime
        dt = datetime.now()
        data = (
            FileDetailRenderSerializer(instance).data
            for instance in self.filter_queryset(self.get_queryset())
        )
        renderer = self.get_lang(data)
        response = StreamingHttpResponse(
            renderer,
            content_type="text/csv"
        )
        response['Content-Disposition'] = "attachment; filename='dndetail_{}.csv'".format(str(dt.strftime('%Y%m%d%H%M%S%f')))
        return response
