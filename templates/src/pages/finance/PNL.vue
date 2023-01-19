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
             <q-btn
              v-show="
                $q.localStorage.getItem('staff_type') !== 'Supplier' &&
                  $q.localStorage.getItem('staff_type') !== 'Customer' &&
                  $q.localStorage.getItem('staff_type') !== 'Inbound' &&
                  $q.localStorage.getItem('staff_type') !== 'StockControl'
              "
              :label="$t('finance.view_pnl.fetch_financedata')"
              icon="img:statics/capital/fetch.png"
              @click="fetchfinancedata()"
            >
              <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('finance.view_pnl.fetch_financedata') }}</q-tooltip>
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
               <q-td key="account_name" :props="props">
                 {{ props.row.account_name }}
               </q-td>
               <q-td key="order_id" :props="props">
                 {{ props.row.dn_code }}
               </q-td>
               <q-td key="orderitem_id" :props="props">
                 {{ props.row.orderitem_id }}
               </q-td>
               <q-td key="goods_desc" :props="props">
                 {{ props.row.goods_desc }}
               </q-td>
               <q-td key="quantity" :props="props">
                 {{ props.row.shipped_qty }}
               </q-td>
             <q-td key="selling_price" :props="props">
               {{ props.row.selling_price }}
             </q-td>
             <q-td key="btw_cost" :props="props">
               {{ props.row.btw_cost }}
             </q-td>
             <q-td key="bol_commission" :props="props">
               {{ props.row.bol_commission }}
             </q-td>
             <q-td key="logistic" :props="props">
               {{ props.row.logistic_cost }}
             </q-td>
             <q-td key="product_cost" :props="props">
               {{ props.row.product_cost }}
             </q-td>
             <q-td key="selling_date" :props="props">
               {{ props.row.selling_date }}
             </q-td>
             <q-td key="create_time" :props="props">
               {{ props.row.create_time }}
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
    </div>
</template>
    <router-view />

<script>
import { getauth, postauth } from 'boot/axios_request'

export default {
  name: 'Pagednpnl',
  data () {
    return {
      openid: '',
      login_name: '',
      authin: '0',
      dn_code: '',
      pathname: 'payment/pnl/',
      param: '?dn_complete=2&dn_status=1',
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
        { name: 'account_name', required: true, label: this.$t('outbound.view_dn.account_name'), align: 'left', field: 'account_name' },
        { name: 'order_id', required: true, label: this.$t('finance.view_pnl.order_id'), align: 'left', field: 'order_id' },
        { name: 'orderitem_id', label: this.$t('finance.view_pnl.order_item_id'), field: 'orderitem_id', align: 'center' },
        { name: 'goods_desc', label: this.$t('finance.view_pnl.goods_desc'), field: 'goods_desc', align: 'center' },
        { name: 'quantity', label: this.$t('finance.view_pnl.quantity'), field: 'quantity', align: 'center' },
        { name: 'selling_price', label: this.$t('finance.view_pnl.selling_price'), field: 'selling_price', align: 'center' },
        { name: 'btw_cost', label: this.$t('finance.view_pnl.btw'), field: 'btw_cost', align: 'center' },
        { name: 'bol_commission', label: this.$t('finance.view_pnl.bol_commission'), field: 'bol_commission', align: 'center' },
        { name: 'logistic', label: this.$t('finance.view_pnl.logistic_cost'), field: 'logistic', align: 'center' },
        { name: 'product_cost', label: this.$t('finance.view_pnl.product_cost'), field: 'product_cost', align: 'center' },
        { name: 'selling_date', label: this.$t('finance.view_pnl.selling_date'), field: 'selling_date', align: 'center' },
        { name: 'create_time', label: this.$t('finance.view_pnl.create_time'), field: 'create_time', align: 'center' }
      ],
      filter: '',
      pagination: {
        page: 1,
        rowsPerPage: '30'
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
    getSearchList () {
      var _this = this
      if (_this.$q.localStorage.has('auth')) {
        getauth(_this.pathname + '&dn_code__icontains=' + _this.filter, {
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
    fetchfinancedata () {
      var _this = this
      postauth(_this.pathname, {})
        .then(res => {
          _this.table_list = []
          _this.getList()
          if (!res.detail) {
            _this.$q.notify({
              message: 'Success Release All Order',
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
    _this.dn_code = _this.$route.params.dn_code
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
