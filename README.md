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
