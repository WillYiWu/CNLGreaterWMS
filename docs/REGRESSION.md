# CNLGreaterWMS 回归测试

## 执行

使用 Python 3.11，在仓库根目录运行：

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/regression.py
```

已有虚拟环境只需最后一条。任何失败返回非零退出码。入口自动发现项目全部 Django 测试；不连接生产数据库，不需要真实 Bol.com 凭据。内存数据库每次重建并销毁，应用表按当前模型生成，故本套不验证历史数据库迁移。网络连接被禁止，第三方调用由测试模拟。面单下载测试使用临时目录。

## 用例与预期（29 项测试，含多个参数化子场景）

| 文件 | 数量 | 场景与预期 |
| --- | --- | --- |
| dn/test_shipping_labels.py | 6 | 订单明细与拣货表超过 200 条仍能命中；裸订单号/明细号兼容；过滤删除及其他租户记录；拣货表回退；首次下载后缓存复用 |
| dn/test_regression.py | 10 | 精确账号前缀；明细优先；删除明细回退；201 条干扰数据；query openid 过滤；header 优先；上游 400/401/404/429/500 不缓存；非 PDF 不缓存；超时与 token 失败返回 404 |
| dn/test_serializers.py | 8 | 同 EAN 不同租户返回各自 SKU；缺失/删除商品返回空字段；重复数据选最新有效商品；列表隔离；真实订单详情接口返回 200 及正确商品 |
| dn/tests.py | 5 | EAN→SKU 退货匹配；旧 EAN 财务记录兼容；店铺及租户隔离；重复同步不重复冲销 |

## 测试数据

`tests/fixtures/shipping_labels.json` 是可编辑的合成场景数据，直接由新增测试读取。包含虚构店铺 RegressionStore、订单 REG-0001、两个租户、201 条新订单干扰数量及上游错误状态码。每次运行自动创建测试记录，无需手工导入。

其他数据由各测试文件的 create_record/create_goods/create_finance 工厂建立，覆盖共享 EAN、不同租户 SKU、已删除商品、退货金额及重复同步。不得替换为生产客户资料、订单或密钥。

## 每次修改后的执行要求

1. 为新功能或修复增加可复现用例和数据。
2. 运行统一入口，处理失败后重新全量运行。
3. 记录命令、数量、结果和未覆盖范围，再交付。

`AGENTS.md` 已记录此要求。`regression.yml` 在 push/PR 时检查；现有 Azure 发布流程在构建阶段也运行回归，失败会阻止后续部署。GitHub 是否强制禁止合并取决于仓库分支保护设置，本次未修改该设置。

## 本次检查记录与边界

首次全量运行：29 项中 28 项通过、1 项失败。旧测试 `test_login_openid_does_not_affect_return_matching` 源自旧的跨身份匹配规则；提交 `1964a4bf`（Add openid check to segregate data by account）已明确改为租户隔离，因此更新为同店铺名、不同 openid 的财务记录不得被处理。未修改业务代码。

此为首版后端回归基线，尚不覆盖完整库存出入库、权限体系、前端操作、真实 Bol.com 服务及生产部署。面单文件缓存的跨租户访问授权也不在当前隔离断言内；这里验证的是数据库查询隔离。生产部署后仍需复查实际问题订单。不能把自动测试通过等同于全项目所有功能或线上恢复已验证。

最终本地执行：`.venv/bin/python scripts/regression.py`，29 项全部通过，退出码 0。CI 配置已编写，尚未推送触发或进行云端验证。

## 发货管理每页 120 行（2026-10-25）

- 发货模块分页默认及上限均为 120，其他模块分页不变；所有 10 个发货表格统一使用数值型 `rowsPerPage: 120`。
- `dn/test_pagination.py` 新增 2 项测试（含参数化场景）：默认分页、超限请求截到 120、合法较小分页、241 条记录连续翻页无丢失。
- 测试机执行 `.venv/bin/python scripts/regression.py`：31 项通过。
- 前端执行 `NODE_OPTIONS=--openssl-legacy-provider ./node_modules/.bin/quasar build`：通过。
- 本地 Chrome 使用实际 Vue/Quasar 和 10 个页面的 QTable 配置，分别注入 241 条合成记录，均只渲染 120 行；未连接生产服务。完整页面业务操作与生产部署未验证。
