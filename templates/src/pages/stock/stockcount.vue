<template>
  <div>
    <transition appear enter-active-class="animated fadeIn">
      <q-table
        id="table"
        class="my-sticky-header-column-table shadow-24"
        :data="table_list"
        row-key="id"
        :separator="separator"
        :loading="loading"
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
            <q-btn
              v-show="
                $q.localStorage.getItem('staff_type') !== 'Supplier' &&
                  $q.localStorage.getItem('staff_type') !== 'Customer' &&
                  $q.localStorage.getItem('staff_type') !== 'Inbound' &&
                  $q.localStorage.getItem('staff_type') !== 'Outbound' &&
                  $q.localStorage.getItem('staff_type') !== 'StockControl'
              "
              :label="$t('new')"
              icon="add"
              @click="newForm = true"
            >
              <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('newtip') }}</q-tooltip>
            </q-btn>
          </q-btn-group>
          <q-space />
          <q-input outlined rounded dense debounce="300" color="primary" v-model="filter" :placeholder="$t('search')" @input="getSearchList()">
            <template v-slot:append>
              <q-icon name="search" />
            </template>
          </q-input>
        </template>
        <template v-slot:body="props">
          <q-tr :props="props">
            <template v-if="props.row.id === editid">
              <q-td key="bin_name" :props="props">
                <q-input
                  dense
                  outlined
                  square
                  v-model="editFormData.bin_name"
                  :label="$t('stock.view_stocklist.onhand_stock')"
                  autofocus
                  :rules="[val => (val && val.length > 0) || error2]"
                />
              </q-td>
            </template>
            <template v-else-if="props.row.id !== editid">
              <q-td key="bin_name" :props="props">{{ props.row.bin_name }}</q-td>
            </template>
            <template v-if="props.row.id === editid">
              <q-td key="goods_code" :props="props">
                <q-input
                  dense
                  outlined
                  square
                  v-model="editFormData.goods_code"
                  :label="$t('stock.view_stocklist.onhand_stock')"
                  autofocus
                  :rules="[val => (val && val.length > 0) || error2]"
                />
              </q-td>
            </template>
            <template v-else-if="props.row.id !== editid">
              <q-td key="goods_code" :props="props">{{ props.row.goods_code }}</q-td>
            </template>
            <q-td key="goods_desc" :props="props">{{ props.row.goods_desc }}</q-td>
            <template v-if="props.row.id === editid">
              <q-td key="goods_qty" :props="props">
                <q-input
                  dense
                  outlined
                  square
                  v-model="editFormData.goods_qty"
                  :label="$t('stock.view_stocklist.onhand_stock')"
                  autofocus
                  :rules="[val => (val && val.length > 0) || error2]"
                />
              </q-td>
            </template>
            <template v-else-if="props.row.id !== editid">
              <q-td key="goods_qty" :props="props">{{ props.row.goods_qty }}</q-td>
            </template>
            <q-td key="bin_property" :props="props">{{ props.row.bin_property }}</q-td>
            <q-td key="create_time" :props="props">{{ props.row.create_time }}</q-td>
            <q-td key="update_time" :props="props">{{ props.row.update_time }}</q-td>
            <template v-if="!editMode">
              <q-td key="action" :props="props" style="width: 175px">
                <q-btn
                  v-show="
                    $q.localStorage.getItem('staff_type') !== 'Supplier' &&
                      $q.localStorage.getItem('staff_type') !== 'Customer' &&
                      $q.localStorage.getItem('staff_type') !== 'Inbound' &&
                      $q.localStorage.getItem('staff_type') !== 'Outbound' &&
                      $q.localStorage.getItem('staff_type') !== 'StockControl'
                  "
                  round
                  flat
                  push
                  color="purple"
                  :icon="props.row.is_lock ? 'lock' : 'lock_open'"
                  @click="unlock(props.row)"
                >
                  <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">
                    {{ props.row.is_lock ? $t('staff.view_staff.unlock') : $t('staff.view_staff.lock') }}
                  </q-tooltip>
                </q-btn>
                <q-btn
                  v-show="
                    $q.localStorage.getItem('staff_type') !== 'Supplier' &&
                      $q.localStorage.getItem('staff_type') !== 'Customer' &&
                      $q.localStorage.getItem('staff_type') !== 'Inbound' &&
                      $q.localStorage.getItem('staff_type') !== 'Outbound' &&
                      $q.localStorage.getItem('staff_type') !== 'StockControl'
                  "
                  round
                  flat
                  push
                  color="purple"
                  icon="edit"
                  @click="editData(props.row)"
                >
                  <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('edit') }}</q-tooltip>
                </q-btn>
              </q-td>
            </template>
            <template v-else-if="editMode">
              <template v-if="props.row.id === editid">
                <q-td key="action" :props="props" style="width: 150px">
                  <q-btn round flat push color="secondary" icon="check" @click="editDataSubmit()">
                    <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('confirmedit') }}</q-tooltip>
                  </q-btn>
                  <q-btn round flat push color="red" icon="close" @click="editDataCancel()">
                    <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('canceledit') }}</q-tooltip>
                  </q-btn>
                </q-td>
              </template>
              <template v-else-if="props.row.id !== editid"></template>
            </template>
          </q-tr>
        </template>
      </q-table>
    </transition>
    <template>
      <div class="q-pa-lg flex flex-center">
        <q-btn v-show="pathname_previous" flat push color="purple" :label="$t('previous')" icon="navigate_before" @click="getListPrevious()">
          <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('previous') }}</q-tooltip>
        </q-btn>
        <q-btn v-show="pathname_next" flat push color="purple" :label="$t('next')" icon-right="navigate_next" @click="getListNext()">
          <q-tooltip content-class="bg-amber text-black shadow-4" :offset="[10, 10]" content-style="font-size: 12px">{{ $t('next') }}</q-tooltip>
        </q-btn>
        <q-btn v-show="!pathname_previous && !pathname_next" flat push color="dark" :label="$t('no_data')"></q-btn>
      </div>
    </template>
   </div>
</template>
<router-view />

<script>
import { getauth, postauth, putauth, deleteauth, getfile } from 'boot/axios_request'
import { date, exportFile, LocalStorage } from 'quasar'

export default {
  name: 'Pagestockcount',
  data () {
    return {
      openid: '',
      login_name: '',
      authin: '0',
      pathname: 'stock/correction/',
      pathname_previous: '',
      pathname_next: '',
      separator: 'cell',
      loading: false,
      height: '',
      table_list: [],
      account_type_list: [],
      columns: [
        { name: 'bin_name', required: true, label: this.$t('warehouse.view_binset.bin_name'), align: 'left', field: 'bin_name' },
        { name: 'goods_code', label: this.$t('stock.view_stocklist.goods_code'), field: 'goods_code', align: 'center' },
        { name: 'goods_desc', label: this.$t('stock.view_stocklist.goods_desc'), field: 'goods_desc', align: 'center' },
        { name: 'goods_qty', label: this.$t('stock.view_stocklist.onhand_stock'), field: 'onhand_stock', align: 'center' },
        { name: 'bin_property', label: this.$t('warehouse.view_binset.bin_property'), field: 'bin_property', align: 'center' },
        { name: 'create_time', label: this.$t('createtime'), field: 'create_time', align: 'center' },
        { name: 'update_time', label: this.$t('updatetime'), field: 'update_time', align: 'center' },
        { name: 'action', label: this.$t('action'), align: 'right' }
      ],
      pagination: {
        page: 1,
        rowsPerPage: '30'
      },
      editid: 0,
      editFormData: {},
      editMode: false,
      deleteForm: false,
      deleteid: 0,
      filter: '',
      error1: this.$t('staff.view_staff.error1'),
      error2: this.$t('staff.view_staff.error2')
    }
  },
  methods: {
    getList () {
      var _this = this
      getauth(_this.pathname, {})
        .then(res => {
          _this.table_list = res.results
          _this.pathname_previous = res.previous
          _this.pathname_next = res.next
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
      _this.filter = _this.filter.replace(/\s+/g, '')
      getauth(_this.pathname + '?staff_name__icontains=' + _this.filter, {})
        .then(res => {
          _this.table_list = res.results
          _this.pathname_previous = res.previous
          _this.pathname_next = res.next
        })
        .catch(err => {
          _this.$q.notify({
            message: err.detail,
            icon: 'close',
            color: 'negative'
          })
        })
    },
    getListPrevious () {
      var _this = this
      getauth(_this.pathname_previous, {})
        .then(res => {
          _this.table_list = res.results
          _this.pathname_previous = res.previous
          _this.pathname_next = res.next
        })
        .catch(err => {
          _this.$q.notify({
            message: err.detail,
            icon: 'close',
            color: 'negative'
          })
        })
    },
    getListNext () {
      var _this = this
      getauth(_this.pathname_next, {})
        .then(res => {
          _this.table_list = res.results
          _this.pathname_previous = res.previous
          _this.pathname_next = res.next
        })
        .catch(err => {
          _this.$q.notify({
            message: err.detail,
            icon: 'close',
            color: 'negative'
          })
        })
    },
    reFresh () {
      var _this = this
      _this.getList()
    },
    unlock (val) {
      putauth(this.pathname + val.id + '/', {
        is_lock: !val.is_lock,
        goods_qty: val.goods_qty,
      })
        .then(res => {
          this.getList()
          let message = 'Success unlocked'
          if (!val.is_lock) {
            message = 'Success locked'
          }
          this.$q.notify({
            message: message,
            icon: 'check',
            color: 'green'
          })
        })
        .catch(err => {
          this.$q.notify({
            message: err.detail,
            icon: 'close',
            color: 'negative'
          })
        })
    },
    editData (e) {
      var _this = this
      _this.editMode = true
      _this.editid = e.id
      _this.editFormData = {
        bin_name: e.bin_name,
        goods_code: e.goods_code,
        goods_qty: e.goods_qty,
      }
    },
    editDataSubmit () {
      var _this = this
      putauth(_this.pathname + _this.editid + '/', _this.editFormData)
        .then(res => {
          _this.editDataCancel()
          _this.getList()
          _this.$q.notify({
            message: 'Success Edit Data',
            icon: 'check',
            color: 'green'
          })
        })
        .catch(err => {
          _this.$q.notify({
            message: err.detail,
            icon: 'close',
            color: 'negative'
          })
        })
    },
    editDataCancel () {
      var _this = this
      _this.editMode = false
      _this.editid = 0
      _this.editFormData = {
        bin_name: '',
        goods_code: '',
        goods_qty: ''
      }
    }
  },
  created () {
    var _this = this
    if (LocalStorage.has('openid')) {
      _this.openid = LocalStorage.getItem('openid')
    } else {
      _this.openid = ''
      LocalStorage.set('openid', '')
    }
    if (LocalStorage.has('login_name')) {
      _this.login_name = LocalStorage.getItem('login_name')
    } else {
      _this.login_name = ''
      LocalStorage.set('login_name', '')
    }
    if (LocalStorage.has('auth')) {
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
    if (LocalStorage.getItem('lang') === 'zh-hans') {
      _this.account_type_list = ['经理', '主管', '收货组', '发货组', '库存控制', '客户', '供应商']
    } else {
      _this.account_type_list = ['Manager', 'Supervisor', 'Inbount', 'Outbound', 'StockControl', 'Customer', 'Supplier']
    }
  },
  updated () {
  },
  destroyed () {
  }
}
</script>
