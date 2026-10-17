# 项目维护说明

## i问财

- 主实现：`mcp_query_table/sites/iwencai.py`；测试：`tests/test_iwencai.py`。
- 保留旧接口分支；新版以 `stream-query` 与 `render/encrypt/getData` 驱动已登录浏览器，不重放加密请求。
- 新版抓取顺序固定为：100 条/页 → 股票代码升序（`sort-rise`，首项 `000001`）→ 逐页读取渲染表格。
- 表格有冻结列副本，读取 `td` 数最多的 `table`，跳过前两列。
- 任何 Cookie、`hexin-v`、token、加密 SQL 或完整请求体都不得进入仓库、fixture、日志或文档。

## 验证

```bash
PYTHONPATH=. python -m unittest tests.test_iwencai -v
```

页面改版时先用已授权的真实浏览器确认首屏、翻页、排序和最终行数，再改代码。
