<template>
    <div>
      <transition appear enter-active-class="animated fadeIn">
      <q-table
        class="my-sticky-header-table shadow-24"
        :data="table_list"
        row-key="id"
        :separator="separator"
        :loading="loading"
        :filter="filter"
        :columns="columns"
        hide-bottom
        :pagination.sync="pagination"
        no-data-label="No data"
        no-results-label="No data you want"
        :table-style="{ height: height }"
        flat
        bordered
      >
         <template v-slot:top>
           <q-btn-group push>
             <q-btn :label="$t('refresh')" icon="refresh" @click="reFresh()">
               <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">
                 {{ $t('refreshtip') }}
               </q-tooltip>
             </q-btn>
             <q-btn :label="$t('outbound.download_all_label')" icon="img:statics/outbound/zegel.jpeg" @click="DownloadPickLabel('','ALL')">
               <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">
                 {{ $t('outbound.download_all_label') }}
               </q-tooltip>
             </q-btn>
             <q-btn :label="$t('print')" icon="print" @click="PrintPickingList()">
               <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">
                 {{ $t('print') }}
               </q-tooltip>
             </q-btn>
             <q-btn :label="$t('outbound.confirmpicked')" icon="refresh" @click="confirmallpicked()">
               <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">
                 {{ $t('outbound.confirm_pick_tip') }}
               </q-tooltip>
             </q-btn>
           </q-btn-group>
           <q-space />
           <q-input outlined rounded dense debounce="300" color="primary" v-model="filter" :placeholder="$t('search')" @blur="getSearchList()" @keyup.enter="getSearchList()">
             <template v-slot:append>
               <q-icon name="search" @click="getSearchList()"/>
             </template>
           </q-input>
         </template>
         <template v-slot:body="props">
           <q-tr :props="props">
               <q-td key="dn_code" :props="props">
                 {{ props.row.dn_code }}
               </q-td>
               <q-td key="account_name" :props="props">
                 {{ props.row.account_name }}
               </q-td>
               <q-td key="bin_name" :props="props">
                 {{ props.row.bin_name }}
               </q-td>
               <q-td key="goods_desc" :props="props">
                 {{ props.row.goods_desc }}
               </q-td>
               <q-td key="customer" :props="props">
                 {{ props.row.customer }}
               </q-td>
               <q-td key="pick_qty" :props="props">
                 {{ props.row.pick_qty }}
               </q-td>
             <q-td key="picked_qty" :props="props">
               {{ props.row.picked_qty }}
             </q-td>
             <q-td key="creater" :props="props">
               {{ props.row.creater }}
             </q-td>
             <q-td key="create_time" :props="props">
               {{ props.row.create_time }}
             </q-td>
             <q-td key="update_time" :props="props">
               {{ props.row.update_time }}
             </q-td>
             <q-td key="action" :props="props" style="width: 100px">
              <q-btn
                v-show="
                  $q.localStorage.getItem('staff_type') !== 'Supplier' &&
                    $q.localStorage.getItem('staff_type') !== 'Customer' &&
                    $q.localStorage.getItem('staff_type') !== 'Inbound' &&
                    $q.localStorage.getItem('staff_type') !== 'StockControl'
                "
                round
                flat
                push
                color="positive"
                icon="img:statics/outbound/zegel2.ico"
                @click="DownloadPickLabel(props.row.account_name,props.row.dn_code)"
              >
                <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('outbound.view_dn.download_zegel') }}</q-tooltip>
              </q-btn>
            </q-td>
           </q-tr>
         </template>
      </q-table>
        </transition>
      <template>
        <div class="q-pa-lg flex flex-center">
          <q-btn v-show="pathname_previous" flat push color="purple" :label="$t('previous')" icon="navigate_before" @click="getListPrevious()">
            <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">
              {{ $t('previous') }}
            </q-tooltip>
          </q-btn>
          <q-btn v-show="pathname_next" flat push color="purple" :label="$t('next')" icon-right="navigate_next" @click="getListNext()">
            <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">
              {{ $t('next') }}
            </q-tooltip>
          </q-btn>
          <q-btn v-show="!pathname_previous && !pathname_next" flat push color="dark" :label="$t('no_data')"></q-btn>
        </div>
      </template>
      <q-dialog v-model="viewPLForm">
        <q-card id="printPL">
          <q-bar class="bg-light-blue-10 text-white rounded-borders" style="height: 50px">
            <div>{{ $t('print') }}</div>
            <q-space />
          </q-bar>
          <div class="col-4" style="margin-top: 5%;"><img :src="bar_code" style="width: 21%;margin-left: 70%" /></div>
          <q-markup-table>
            <thead>
              <tr>
                <th class="text-left">{{ $t('outbound.view_dn.dn_code') }}</th>
                <th class="text-right">{{ $t('warehouse.view_binset.bin_name') }}</th>
                <th class="text-right">{{ $t('goods.view_goodslist.goods_desc') }}</th>
                <th class="text-right">{{ $t('baseinfo.view_customer.customer_name') }}</th>
                <th class="text-right">{{ $t('outbound.pickstock') }}</th>
                <th class="text-right">{{ $t('outbound.pickedstock') }}</th>
                <th class="text-right">Comments</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in pickinglist_print_table">
                <td class="text-left">{{ item.dn_code }}</td>
                <td class="text-right">{{ item.bin_name }}</td>
                <td class="text-right">{{ item.goods_desc }}</td>
                <td class="text-right">{{ item.customer }}</td>
                <td class="text-right">{{ item.pick_qty }}</td>
                <td class="text-right" v-show="picklist_check === 0"></td>
                <td class="text-right" v-show="picklist_check > 0">{{ item.picked_qty }}</td>
                <td class="text-right"></td>
              </tr>
            </tbody>
          </q-markup-table>
        </q-card>
        <div style="float: right; padding: 15px 15px 15px 0"><q-btn color="primary" icon="print" v-print="printPL">print</q-btn></div>
      </q-dialog>
    </div>
</template>
<router-view />

<script>
import { getauth, postauth, deleteauth, getfile, getPDF, baseurl } from 'boot/axios_request'

export default {
  name: 'Pagednprepick',
  data () {
    return {
      openid: '',
      login_name: '',
      authin: '0',
      pathname: 'dn/pickinglistfilter/',
      viewPLForm: false,
      pickinglist_print_table: [],
      pickinglist_check: 0,
      bar_code: '',
      printPL: {
        id: 'printPL',
        popTitle: this.$t('outbound.pickinglist')
      },
      pathname_previous: '',
      pathname_next: '',
      separator: 'cell',
      loading: false,
      height: '',
      table_list: [],
      bin_size_list: [],
      bin_property_list: [],
      warehouse_list: [],
      columns: [
        { name: 'dn_code', required: true, label: this.$t('outbound.view_dn.dn_code'), align: 'left', field: 'dn_code' },
        { name: 'account_name', label: this.$t('outbound.view_dn.account_name'), field: 'account_name', align: 'center' },
        { name: 'bin_name', label: this.$t('warehouse.view_binset.bin_name'), field: 'bin_name', align: 'center' },
        { name: 'goods_desc', label: this.$t('goods.view_goodslist.goods_desc'), field: 'goods_desc', align: 'center' },
        { name: 'customer', label: this.$t('baseinfo.view_customer.customer_name'), field: 'customer', align: 'center' },
        { name: 'pick_qty', label: this.$t('scan.view_picking.order_qty'), field: 'pick_qty', align: 'center' },
        { name: 'picked_qty', label: this.$t('scan.view_picking.available_qty'), field: 'picked_qty', align: 'center' },
        { name: 'creater', label: this.$t('creater'), field: 'creater', align: 'center' },
        { name: 'create_time', label: this.$t('createtime'), field: 'create_time', align: 'center' },
        { name: 'update_time', label: this.$t('updatetime'), field: 'update_time', align: 'center' },
        { name: 'action', label: this.$t('action'), align: 'right' }
      ],
      filter: '',
      pagination: {
        page: 1,
        rowsPerPage: '100'
      }
    }
  },
  methods: {
    getList () {
      var _this = this
      if (_this.$q.localStorage.has('auth')) {
        getauth(_this.pathname, {
        }).then(res => {
          _this.table_list = res.results
          _this.pathname_previous = res.previous
          _this.pathname_next = res.next
        }).catch(err => {
          _this.$q.notify({
            message: err.detail,
            icon: 'close',
            color: 'negative'
          })
        })
      } else {
      }
    },
    async DownloadPickLabel(account_name, dn_code){
      var _this = this
      var file_name = ""
      try{
        const axios = require("axios")
        const instance = axios.create({
          baseURL: baseurl,
        })
        const res = await instance.get('dn/shippinglabel/' + account_name+dn_code, {responseType: 'blob' });
        const downloadUrl = window.URL.createObjectURL(new Blob([res.data], {type: 'application/pdf'}));
        const link = document.createElement('a');
        link.href = downloadUrl
        if (dn_code === 'ALL'){
          file_name = new Date().toLocaleDateString()
        }else{
          file_name = account_name+dn_code
        }
        link.setAttribute('download', file_name + '.pdf');
        document.body.appendChild(link);
        link.click();
        link.remove();
      } catch (error) {
        console.error(error);
      }
    },
    DownloadPickLabel2(orderitem_id){
      var _this = this
      if (_this.$q.localStorage.has('auth')){
        getfile('dn/shippinglabel/')
          .then(res=>{
            const blob = new Blob([res.data], {type: 'application/pdf;base64'});
            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;
            //link.setAttribute('href', 'data:"application/pdf;base64,' + res.data.base64PDF);
            link.setAttribute('download', 'merged.pdf');
            document.body.appendChild(link);
            link.click();
            link.remove();
          })
          .catch(err => {
            _this.$q.notify({
              message: err.detail,
              icon: 'close',
              color: 'negative'
            })
          })
      }
    },
    PrintPickingList () {
      var _this = this
      _this.viewPLForm = true
      getauth(_this.pathname)
        .then(res => {
          _this.pickinglist_print_table = []
          _this.picklist_check = 0
          _this.pickinglist_print_table = res.results
        })
        .catch(err => {
          _this.$q.notify({
            message: err.detail,
            icon: 'close',
            color: 'negative'
          })
        })
    },
    getSearchList () {
      var _this = this
      if (_this.$q.localStorage.has('auth')) {
        getauth(_this.pathname + '?dn_code__icontains=' + _this.filter, {
        }).then(res => {
          _this.table_list = res.results
          _this.pathname_previous = res.previous
          _this.pathname_next = res.next
        }).catch(err => {
          _this.$q.notify({
            message: err.detail,
            icon: 'close',
            color: 'negative'
          })
        })
      } else {
      }
    },
    getListPrevious () {
      var _this = this
      if (_this.$q.localStorage.has('auth')) {
        getauth(_this.pathname_previous, {
        }).then(res => {
          _this.table_list = res.results
          _this.pathname_previous = res.previous
          _this.pathname_next = res.next
        }).catch(err => {
          _this.$q.notify({
            message: err.detail,
            icon: 'close',
            color: 'negative'
          })
        })
      } else {
      }
    },
    getListNext () {
      var _this = this
      if (_this.$q.localStorage.has('auth')) {
        getauth(_this.pathname_next, {
        }).then(res => {
          _this.table_list = res.results
          _this.pathname_previous = res.previous
          _this.pathname_next = res.next
        }).catch(err => {
          _this.$q.notify({
            message: err.detail,
            icon: 'close',
            color: 'negative'
          })
        })
      } else {
      }
    },
    reFresh () {
      var _this = this
      _this.getList()
    },
    confirmallpicked(){
      var _this = this
      postauth(_this.pathname, {})
        .then(res => {
          _this.table_list = []
          _this.getList()
          if (res.detail==='success') {
            _this.$q.notify({
              message: 'Success Shipped All Order',
              icon: 'check',
              color: 'green'
            })
          }
        })
        .catch(err => {
          _this.$q.notify({
            message: err.detail,
            icon: 'close',
            color: 'negative'
          })
        })
    }
  },
  created () {
    var _this = this
    if (_this.$q.localStorage.has('openid')) {
      _this.openid = _this.$q.localStorage.getItem('openid')
    } else {
      _this.openid = ''
      _this.$q.localStorage.set('openid', '')
    }
    if (_this.$q.localStorage.has('login_name')) {
      _this.login_name = _this.$q.localStorage.getItem('login_name')
    } else {
      _this.login_name = ''
      _this.$q.localStorage.set('login_name', '')
    }
    if (_this.$q.localStorage.has('auth')) {
      _this.authin = '1'
      _this.getList()
    } else {
      _this.authin = '0'
    }
  },
  mounted () {
    var _this = this
    if (_this.$q.platform.is.electron) {
      _this.height = String(_this.$q.screen.height - 290) + 'px'
    } else {
      _this.height = _this.$q.screen.height - 290 + '' + 'px'
    }
  },
  updated () {
  },
  destroyed () {
  }
}
</script>
