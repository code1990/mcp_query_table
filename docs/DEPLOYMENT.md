# 部署文档

## 1. 部署目标

将 `mcp_query_table` 部署为本机可访问的 MCP 服务，对外提供财经网页查询能力。

## 2. 部署目录

统一要求：

```bash
/root/project
```

项目目录：

```bash
/root/project/mcp_query_table
```

## 3. 获取代码

```bash
cd /root/project
git clone git@github.com:code1990/mcp_query_table.git
cd mcp_query_table
```

更新代码：

```bash
git pull origin main
```

## 4. 安装依赖

```bash
cd /root/project/mcp_query_table
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

如果运行环境没有 Chrome，可自行安装并指定 `--executable_path`。

## 5. 浏览器准备

推荐两种方式：

### 方式一：先手工启动本地 Chrome 并开放 CDP

```bash
/usr/bin/google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/root/.config/google-chrome-mcp
```

随后启动服务：

```bash
cd /root/project/mcp_query_table
python3 -m mcp_query_table \
  --format markdown \
  --endpoint http://127.0.0.1:9222 \
  --executable_path /usr/bin/google-chrome \
  --user_data_dir /root/.config/google-chrome-mcp
```

### 方式二：让 Playwright 直接拉起浏览器

这种方式更适合脚本直接调用，不一定适合长期驻留服务。

## 6. 启动服务

### STDIO

```bash
cd /root/project/mcp_query_table
python3 -m mcp_query_table --format markdown --endpoint http://127.0.0.1:9222
```

### SSE

```bash
cd /root/project/mcp_query_table
python3 -m mcp_query_table \
  --format markdown \
  --transport sse \
  --host 0.0.0.0 \
  --port 8000 \
  --endpoint http://127.0.0.1:9222
```

### Streamable HTTP

```bash
cd /root/project/mcp_query_table
python3 -m mcp_query_table \
  --format markdown \
  --transport streamable-http \
  --host 0.0.0.0 \
  --port 8000 \
  --endpoint http://127.0.0.1:9222
```

## 7. MCP 客户端接入

### SSE 地址

```text
http://127.0.0.1:8000/sse
```

### Streamable HTTP 地址

```text
http://127.0.0.1:8000/mcp
```

## 8. 运维建议

- 站点要求登录时，单独维护专用 `user_data_dir`
- 不要把浏览器默认用户目录直接用于生产
- 把服务限制在内网或本机使用
- 站点改版后优先检查 `sites/` 适配器
