<template>
  <q-page class="flex flex-top">
<template>
  <div class="q-pa-md">
    <div class="q-gutter-y-md" style="max-width: 100%">
      <q-tabs
        v-model="detaillink"
      >
        <transition appear enter-active-class="animated zoomIn">
          <q-route-tab name="dn" :label="$t('outbound.dn')" icon="img:statics/outbound/dnlist.png" :to="{ name: 'dn' }" exact/>
        </transition>
        <transition appear enter-active-class="animated zoomIn">
          <q-route-tab name="freshorder" :label="$t('outbound.wrongorder')" icon="img:statics/outbound/freshorder.png" :to="{ name: 'freshorder' }" exact/>
        </transition>
        <transition appear enter-active-class="animated zoomIn">
          <q-route-tab name="customercancel" :label="$t('outbound.customercancel')" icon="img:statics/outbound/pickstock.png" :to="{ name: 'customercancel' }" exact/>
        </transition>
        <transition appear enter-active-class="animated zoomIn">
          <q-route-tab name="backorder" :label="$t('outbound.backorder')" icon="img:statics/outbound/backorder.png" :to="{ name: 'backorder' }" exact/>
        </transition>
        <transition appear enter-active-class="animated zoomIn">
          <q-route-tab name="neworder" :label="$t('outbound.neworder')" icon="img:statics/outbound/order.png" :to="{ name: 'neworder' }" exact/>
        </transition>
        <transition appear enter-active-class="animated zoomIn">
          <q-route-tab name="pickinglist" :label="$t('outbound.pickinglist')" icon="img:statics/outbound/pickinglist.png" :to="{ name: 'pickinglist' }" exact/>
        </transition>
        <transition appear enter-active-class="animated zoomIn">
          <q-route-tab name="shippedstock" :label="$t('outbound.shippedstock')" icon="img:statics/outbound/outbound.png" :to="{ name: 'shippedstock' }" exact/>
        </transition>
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
        this.selectedTab = 0
      } else if (this.$route.name === 'freshorderbycode'){
        this.selectedTab = 1
      } else if (this.$route.name === 'backorderbycode'){
        this.selectedTab = 2
      } else if (this.$route.name === 'neworderbycode'){
        this.selectedTab = 3
      } else {
        this.selectedTab =0
      }
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
