# 接口文档

## 1. 服务信息

- 服务名：`mcp_query_table`
- 协议：`MCP`
- 入口：`python -m mcp_query_table`
- 默认工具：`query`

启动示例：

```bash
cd /root/project/mcp_query_table
python3 -m mcp_query_table --format markdown --endpoint http://127.0.0.1:9222
```

## 2. 启动参数

### `--format`

输出格式：

- `markdown`
- `csv`
- `json`

### `--transport`

传输方式：

- `stdio`
- `sse`
- `streamable-http`

### `--endpoint`

浏览器连接地址：

- 本地 CDP，例如 `http://127.0.0.1:9222`
- 远程 Playwright WS，例如 `ws://127.0.0.1:3000`

### `--executable_path`

本地浏览器路径，例如：

```text
/usr/bin/google-chrome
```

### `--user_data_dir`

浏览器用户数据目录。建议在需要登录的网站场景里显式提供。

## 3. MCP 工具

### `query`

用途：查询财经网页表格数据。

参数：

- `query_input`：查询条件
- `query_type`：查询类型
- `max_page`：最多翻页数，范围 1 到 10
- `rename`：是否使用站点返回的友好列名
- `site`：目标站点

### `query_type` 可选值

- `A股`
- `港股`
- `美股`
- `指数`
- `基金`
- `ETF`
- `可转债`
- `板块`
- `资讯`

### `site` 可选值

- `同花顺`
- `通达信`
- `东方财富`

## 4. 返回结果

返回内容是字符串，具体格式取决于服务启动参数：

- `markdown`：Markdown 表格
- `csv`：CSV 文本
- `json`：JSON 字符串

## 5. 使用示例

### Python 命令行启动

```bash
python3 -m mcp_query_table \
  --format markdown \
  --transport sse \
  --port 8000 \
  --endpoint http://127.0.0.1:9222
```

### Cline 配置示例

```json
{
  "mcpServers": {
    "mcp_query_table": {
      "timeout": 300,
      "command": "/root/.venv/bin/python",
      "args": [
        "-m",
        "mcp_query_table",
        "--format",
        "markdown",
        "--endpoint",
        "http://127.0.0.1:9222",
        "--executable_path",
        "/usr/bin/google-chrome",
        "--user_data_dir",
        "/root/.config/google-chrome-mcp"
      ]
    }
  }
}
```
