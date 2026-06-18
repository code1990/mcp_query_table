# 运维手册

## 1. 启动 STDIO 服务

```bash
cd /root/project/mcp_query_table
python3 -m mcp_query_table --format markdown --endpoint http://127.0.0.1:9222
```

## 2. 启动 SSE 服务

```bash
cd /root/project/mcp_query_table
python3 -m mcp_query_table \
  --format markdown \
  --transport sse \
  --host 0.0.0.0 \
  --port 8000 \
  --endpoint http://127.0.0.1:9222
```

## 3. 启动 Streamable HTTP 服务

```bash
cd /root/project/mcp_query_table
python3 -m mcp_query_table \
  --format markdown \
  --transport streamable-http \
  --host 0.0.0.0 \
  --port 8000 \
  --endpoint http://127.0.0.1:9222
```

## 4. 查看当前 Git 变更

```bash
cd /root/project/mcp_query_table
git status --short
```

## 5. 更新代码

```bash
cd /root/project/mcp_query_table
git pull origin main
```

## 6. 重新安装本地包

```bash
cd /root/project/mcp_query_table
python3 -m pip install -e .
```

## 7. 调试站点适配

```bash
cd /root/project/mcp_query_table
python3 examples/main.py
```

## 8. 调试 Streamlit 页面

```bash
cd /root/project/mcp_query_table/streamlit
python3 -m streamlit run app.py --server.enableStaticServing=true
```
