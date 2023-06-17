<template>
  <div>
    <q-dialog v-model="newForm">
      <q-card class="shadow-24">
        <q-bar class="bg-light-blue-10 text-white rounded-borders" style="height: 50px">
          <div>{{ $t('password') }}</div>
          <q-space />
          <q-btn dense flat icon="close" v-close-popup>
            <q-tooltip content-class="bg-amber text-black shadow-4">{{ $t('index.close') }}</q-tooltip>
          </q-btn>
        </q-bar>

          <q-input
            dense
            outlined
            square
            v-model.trim="newFormData.password"
            :label="$t('index.password')"
            autofocus
            :rules="[val => (val && val.length > 0) || error1]"
            @keyup.enter="newDataSubmit()"
          />

        <div style="float: right; padding: 15px 15px 15px 0">
          <q-btn color="white" text-color="black" style="margin-right: 25px" @click="newDataCancel()">{{ $t('cancel') }}</q-btn>
          <q-btn color="primary" @click="newDataSubmit()">{{ $t('submit') }}</q-btn>
        </div>
      </q-card>
    </q-dialog>
  </div>
</template>

<script>
import IEcharts from 'vue-echarts-v3/src/full.js';
import { getauth } from 'boot/axios_request';
import {LocalStorage} from "quasar";

export default {
  name: 'charts',
  data() {
    return {
      login_name: '',
      newForm: false,
      newFormData: {
        password: ''
      },
      authin: '0',
      pathname: 'dashboard/',
      height: '',
      height2: '',
      width: '100%',
      barChartOption: {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
          // Use axis to trigger tooltip
          type: 'shadow' // 'shadow' as default; can also be 'line' or 'shadow'
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        legend: {},
        tooltip: {},
        dataset: {
        },
        xAxis: {
          type: 'value'
        },
        yAxis: {
          type: 'category',
          data: []
        },
        series: []
      },
      selected_product: this.$t('dashboards.monthly'),
      product_options: [this.$t('dashboards.monthly'),
                        this.$t('dashboards.daily')]
    };
  },
  methods: {
    getList() {
      var _this = this;
      var param = "";
      if (_this.selected_product === _this.$t('dashboards.monthly')){
        param = "Monthly";
      }else{
        param = "Daily";
      }
      if (_this.$q.localStorage.has('auth')) {
        getauth(_this.pathname + 'sales/'+param, {})
          .then(res => {
            _this.barChartOption.yAxis.data = res.yAxis;
            _this.barChartOption.series = res.series;
          })
          .catch(err => {
            console.log(err);
          });
      } else {
      }
    },
    newDataSubmit () {
      var _this = this
      if (_this.newFormData.password == '556677'){
        _this.$router.push({name: 'newPNL'})
      }
    },
    newDataCancel () {
      var _this = this
      _this.newForm = false
    },
  },
  created() {
    var _this = this
    _this.newForm = true
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
    } else {
      _this.authin = '0'
    }
  },
  mounted() {
    var _this = this;
    _this.newForm = true
    if (_this.$q.platform.is.electron) {
      _this.height = String(_this.$q.screen.height - 190) + 'px';
    } else {
      _this.height = _this.$q.screen.height - 190 + '' + 'px';
    }
    if (_this.$q.platform.is.electron) {
      _this.height2 = String(_this.$q.screen.height - 270) + 'px';
    } else {
      _this.height2 = _this.$q.screen.height - 270 + '' + 'px';
    }
    _this.getList();
  },
  components: {
    IEcharts
  }
};
</script>
