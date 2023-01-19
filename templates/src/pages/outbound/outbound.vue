<template>
  <q-page class="flex flex-top">
<template>
  <div class="q-pa-md">
    <div class="q-gutter-y-md" style="max-width: 100%">
      <q-tabs v-model="detaillink">
          <q-tab name="dn" :label="$t('outbound.dn')" icon="img:statics/outbound/dnlist.png" @click="navigate('dn')" />
          <q-tab name="freshorder" :label="$t('outbound.wrongorder')" icon="img:statics/outbound/freshorder.png" @click="navigate('freshorder')" />
          <q-tab name="customercancel" :label="$t('outbound.customercancel')" icon="img:statics/outbound/pickstock.png" @click="navigate('customercancel')" />
          <q-tab name="backorder" :label="$t('outbound.backorder')" icon="img:statics/outbound/backorder.png" @click="navigate('backorder')" />
          <q-tab name="neworder" :label="$t('outbound.neworder')" icon="img:statics/outbound/order.png" @click="navigate('neworder')" />
          <q-tab name="pickinglist" :label="$t('outbound.pickinglist')" icon="img:statics/outbound/pickinglist.png" @click="navigate('pickinglist')" />
          <q-tab name="shippedstock" :label="$t('outbound.shippedstock')" icon="img:statics/outbound/outbound.png" @click="navigate('shippedstock')" />
      </q-tabs>
    </div>
  </div>
</template>
    <div class="main-table">
      <router-view />
    </div>
  </q-page>
</template>

<script>
export default {
  name: 'Pageoutbound',
  data () {
    return {
      detaillink: 'dn'
    }
  },
  methods: {
    updateSelectedTab(){
      if (this.$route.name === 'dn'){
        this.detaillink = 'dn'
      } else if (this.$route.name === 'freshorderbycode'){
        this.detaillink = 'freshorder'
      } else if (this.$route.name === 'freshorder'){
        this.detaillink = 'freshorder'
      } else if (this.$route.name === 'customercancelbycode'){
        this.detaillink = 'customercancel'
      } else if (this.$route.name === 'customercancel'){
        this.detaillink = 'customercancel'
      } else if (this.$route.name === 'backorderbycode'){
        this.detaillink = 'backorder'
      } else if (this.$route.name === 'backorder'){
        this.detaillink = 'backorder'
      } else if (this.$route.name === 'neworderbycode'){
        this.detaillink = 'neworder'
      } else if (this.$route.name === 'neworder'){
        this.detaillink = 'neworder'
      } else if (this.$route.name === 'pickinglist'){
        this.detaillink = 'pickinglist'
      } else if (this.$route.name === 'shippedstock'){
        this.detaillink = 'shippedstock'
      } else {
        this.detaillink = 'dn'
      }
    },
    navigate(routename){
      this.$router.push({name: routename})
    }
  },
  created(){
    this.updateSelectedTab()
  },
  watch: {
    '$route': 'updateSelectedTab'
  }
}
</script>
