import re

with open('/Users/willwu/Documents/Github_Cursor/CNLGreaterWMS/templates/src/pages/goods/goodslist.vue', 'r') as f:
    content = f.read()

# 1. Add sku_code input
sku_input = """          <q-input
            dense
            outlined
            square
            v-model="newFormData.goods_code"
            :label="$t('goods.view_goodslist.goods_code')"
            autofocus
            :rules="[val => (val && val.length > 0) || error1]"
            @keyup.enter="newDataSubmit()"
          />
          <q-input
            dense
            outlined
            square
            v-model="newFormData.sku_code"
            label="SKU ID"
            @blur="fetchSkuDetails()"
            @keyup.enter="newDataSubmit()"
          />"""
content = re.sub(
    r'<q-input\s+dense\s+outlined\s+square\s+v-model="newFormData\.goods_code"[\s\S]*?@keyup\.enter="newDataSubmit\(\)"\s*/>',
    sku_input,
    content,
    count=1
)

# 2. Add readonly to goods_cost and goods_price
cost_input = """          <q-input
            dense
            outlined
            square
            readonly
            v-model.number="newFormData.goods_cost"
            type="number"
            :label="$t('goods.view_goodslist.goods_cost')"
            :rules="[val => (val && val > 0) || error15]"
            @keyup.enter="newDataSubmit()"
          />"""
content = re.sub(
    r'<q-input\s+dense\s+outlined\s+square\s+v-model\.number="newFormData\.goods_cost"[\s\S]*?@keyup\.enter="newDataSubmit\(\)"\s*/>',
    cost_input,
    content,
    count=1
)

price_input = """          <q-input
            dense
            outlined
            square
            readonly
            v-model.number="newFormData.goods_price"
            type="number"
            :label="$t('goods.view_goodslist.goods_price')"
            :rules="[val => (val && val > 0) || error16]"
            @keyup.enter="newDataSubmit()"
          />"""
content = re.sub(
    r'<q-input\s+dense\s+outlined\s+square\s+v-model\.number="newFormData\.goods_price"[\s\S]*?@keyup\.enter="newDataSubmit\(\)"\s*/>',
    price_input,
    content,
    count=1
)

# 3. Add fetchSkuDetails to methods
methods_str = """  methods: {
    fetchSkuDetails() {
      var _this = this;
      if (_this.newFormData.sku_code) {
        getauth('goods/sku/?sku_code=' + _this.newFormData.sku_code, {})
          .then(res => {
            if (res.results && res.results.length > 0) {
              _this.newFormData.goods_desc = res.results[0].sku_desc;
              _this.newFormData.goods_cost = res.results[0].sku_cost;
              // Set goods_price to the same as cost by default since sku model doesn't have price
              _this.newFormData.goods_price = res.results[0].sku_cost;
            }
          })
          .catch(err => {});
      }
    },"""
content = content.replace("  methods: {", methods_str)

# 4. Default goods_supplier to 阿里巴巴卖家 in newDataCancel
new_data_cancel = """    newDataCancel() {
      var _this = this;
      _this.newForm = false;
      _this.newFormData = {
        goods_code: '',
        sku_code: '',
        goods_desc: '',
        goods_supplier: '阿里巴巴卖家',
        goods_weight: '',
        goods_w: '',
        goods_d: '',
        goods_h: '',
        goods_unit: '',
        goods_class: '',
        goods_brand: '',
        goods_color: '',
        goods_shape: '',
        goods_specs: '',
        goods_origin: '',
        goods_cost: '',
        goods_price: '',
        creater: ''
      };
    },"""

# Note: newDataCancel is defined in content like this:
content = re.sub(
    r'newDataCancel\(\)\s*\{[\s\S]*?creater:\s*\'\'\s*\};\s*\},',
    new_data_cancel,
    content,
    count=1
)

with open('/Users/willwu/Documents/Github_Cursor/CNLGreaterWMS/templates/src/pages/goods/goodslist.vue', 'w') as f:
    f.write(content)
