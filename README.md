# mcp_query_table

`mcp_query_table` 是一个基于 `playwright` 的财经网页表格查询项目，支持把网页查询能力暴露为 `MCP` 服务。

当前统一项目目录要求如下：

```text
/root/project/mcp_query_table
```

当前版本：

```text
0.3.13
```

## 项目定位

- 直接查询财经网站表格数据，减少手工复制和网页操作
- 将查询能力封装为 Python 库，供脚本直接调用
- 将查询能力封装为 `MCP` 服务，供 Cline、Cherry Studio、MCP Inspector 等客户端调用
- 保留可选的 `Streamlit` 页面，便于把查询结果进一步交给大模型分析

## 当前支持

### 表格查询站点

- 同花顺问财
- 通达信问小达
- 东方财富条件选股

### 对话提供商

- 纳米搜索
- 腾讯元宝
- 百度 AI 搜索

## 项目结构

```text
mcp_query_table/
├── mcp_query_table/
│   ├── __main__.py
│   ├── enums.py
│   ├── playwright_helper.py
│   ├── providers/
│   ├── server.py
│   ├── sites/
│   └── tool.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEVELOPMENT.md
│   ├── DEPLOYMENT.md
│   ├── API.md
│   ├── FAQ.md
│   └── OPERATIONS.md
├── examples/
├── streamlit/
├── requirements.txt
└── pyproject.toml
```

## 环境要求

- Python 3.10+
- 已安装 Chrome 或 Edge
- 首次运行前已安装 Playwright 浏览器依赖

当前机器建议 Python 环境：

```bash
/root/.venv/bin/python
```

## 快速开始

### 安装依赖

```bash
cd /root/project/mcp_query_table
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

### 作为 Python 库使用

```python
import asyncio

from mcp_query_table import AsyncBrowser, QueryType, Site, query


async def main():
    async with AsyncBrowser(
        endpoint="http://127.0.0.1:9222",
        executable_path="/usr/bin/google-chrome",
        user_data_dir="/root/.config/google-chrome",
    ) as browser:
        page = await browser.get_page()
        df = await query(
            page,
            query_input="收益最好的200只ETF",
            query_type=QueryType.ETF,
            max_page=1,
            site=Site.THS,
        )
        print(df.to_markdown())
        await browser.release_page(page)


asyncio.run(main())
```

### 启动 MCP 服务

标准输入输出模式：

```bash
cd /root/project/mcp_query_table
python3 -m mcp_query_table \
  --format markdown \
  --endpoint http://127.0.0.1:9222 \
  --executable_path /usr/bin/google-chrome \
  --user_data_dir /root/.config/google-chrome
```

SSE 模式：

```bash
cd /root/project/mcp_query_table
python3 -m mcp_query_table \
  --format markdown \
  --transport sse \
  --host 0.0.0.0 \
  --port 8000 \
  --endpoint http://127.0.0.1:9222 \
  --executable_path /usr/bin/google-chrome \
  --user_data_dir /root/.config/google-chrome
```

启动后：

- SSE 地址：`http://127.0.0.1:8000/sse`
- Streamable HTTP 地址：`http://127.0.0.1:8000/mcp`

## 常见使用场景

- 查询“2024年涨幅最大的100只股票按市值排名”
- 查询“年初至今收益率前50的基金”
- 查询“今日涨幅前5的概念板块”
- 将查询结果转成 Markdown 或 CSV 供大模型继续分析

## 运行注意事项

- 浏览器窗口宽度要足够，避免站点切到移动版页面
- 如果目标站点要求登录，建议提前在指定 `user_data_dir` 里完成登录
- 无头模式下建议显式指定 `user_data_dir`
- 各站点表结构不同，同一查询在不同站点得到的结果可能不同

## i问财新版抓取与 RE 记录（2026-10）

实现位于 `mcp_query_table/sites/iwencai.py`。页面已有两套数据链路，代码会自动分支；旧链路不要删除。

| 场景 | 首屏信号 | 翻页信号 | 解析方式 |
| --- | --- | --- | --- |
| 旧版 | `/unifiedwap/unified-wap/v2/result/get-robot-data` | `/gateway/urp/v7/landing/getDataList` | 直接解析 JSON 中的 `datas`、`columns` 与 `meta` |
| 当前新版 | `/gateway/aime/stream-query`（SSE） | `/gateway/render/encrypt/getData` | 浏览器完成解密和渲染后，从结果表读取 |

新版不要把 `stream-query` 当作普通 JSON；首屏表格配置、总数和首批数据在 SSE 的 `data:` 事件里。翻页接口的请求会携带动态登录态、令牌及加密 SQL，响应由页面处理；当前实现不重放这些敏感、易失效的参数，而是让已登录的 Playwright 页面完成请求。

### 当前新版流程

1. 使用已登录浏览器打开 `/screener/result?w=<问句>&querytype=stock`，宽度保持大于 768。
2. 等待 `.pcwencai-pagination-wrap` 可见，以 `/gateway/aime/stream-query` 判定新版链路。
3. 选择“显示100条/页”，并等待下拉框文字确实更新，避免网络响应先到而 DOM 仍是 50 条时漏掉首屏数据。
4. 点击“股票代码”表头两次。当前页面第一次为降序、第二次为升序；升序状态的图标为 `i.thead-order.sort-rise`，首两条应为 `000001`、`000002`。
5. 每次点击“下页”等待 `/gateway/render/encrypt/getData`，再读取 DOM 中单元格数最多的 `table`（另一张是冻结列副本）。跳过序号和勾选框两列，将其余单元格按表头组成 DataFrame。
6. 当 `.next-link` 带有 `disabled` 时停止，或达到调用者的 `max_page`。

2026-10-17 对“行业概念”的验收结果为 5,582 行、100 条/页共 56 页；行情和成分会变化，后续应以页面的实时总数为准。

### 下次接口改版时的检查顺序

1. 先用真实、已授权的登录页面捕获首屏和一次翻页的 URL、状态码、内容类型及 JSON/SSE 的顶层结构；不要记录 Cookie、`hexin-v`、token、完整请求体或完整响应体。
2. 若新版 SSE、分页 URL 或表格选择器改变，先确认页面是否仍能渲染出结果；优先修正浏览器驱动的流程，而不是复制临时的加密参数。
3. 验证页大小切换、代码升序、首页/末页、总行数和第一页代码。最小回归测试：

```bash
cd /root/project/mcp_query_table
PYTHONPATH=. python -m unittest tests.test_iwencai -v
```

登录态仅存放在本机私有浏览器配置或受限权限的本地文件，绝不提交到 Git、README、测试 fixture 或日志。

### REA/Chrome DevTools 受控验证（2026-10-17）

本项目的正确抓取边界是“让已登录浏览器完成页面请求，再读取渲染后的表格”，而不是复刻 `stream-query` 或 `render/encrypt/getData` 的加密请求。REA 的受控浏览器回放确认：未登录的临时 profile 能加载“行业概念”页面，但不会出现结果表；因此登录态是运行前置条件。

使用本机受限的登录 profile 验证主实现首屏时，`行业概念` 返回 100 行、8 列，且升序后的前两只代码为 `000001`、`000002`。完整抓取继续按上文的 100 条/页、代码升序、逐页 DOM 读取和末页 `disabled` 判断执行。

建议：

1. 把登录态保存在专用 `user_data_dir`，由人工完成登录；不要在生产脚本中读取或注入 cookie 文本。
2. Chrome DevTools MCP 适合观察页面与排查改版，REA 适合保留最小的受控运行证据；两者都不应成为重放动态 token、`hexin-v` 或加密 SQL 的理由。
3. `iwencai_single.py` 仍使用旧 JSON 接口，不能作为新版生产入口。需要独立脚本时，应复用 `mcp_query_table/sites/iwencai.py` 的浏览器渲染流程，或明确标记该脚本为旧版示例。

最小验证命令：

```bash
cd /root/project/mcp_query_table
PYTHONPATH=. python -m unittest tests.test_iwencai -v
```

## 文档

- [架构文档](docs/ARCHITECTURE.md)
- [开发文档](docs/DEVELOPMENT.md)
- [部署文档](docs/DEPLOYMENT.md)
- [接口文档](docs/API.md)
- [FAQ](docs/FAQ.md)
- [运维手册](docs/OPERATIONS.md)

## 单文件版 `i问财`

仓库根目录下提供了 `iwencai_single.py`，用于在不启动 `MCP` 服务的情况下，直接查询新版 `i问财` 选股页并导出结果。

安装依赖：

```commandline
pip install -r iwencai_single_requirements.txt
playwright install chromium
```

直接运行：

```commandline
python iwencai_single.py
```

脚本默认会：

1. 打开 `i问财` 选股结果页
2. 自动切换到 `100条/页`
3. 按分页抓取数据
4. 导出到当前目录下的 `行业概念_single.xlsx`

如需复用，可直接调用：

```python
from iwencai_single import QueryType, query_iwencai
```

## 参考

- [Streamlit 说明](streamlit/README.md)
- [示例脚本](examples/main.py)
