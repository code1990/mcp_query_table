# 开发文档

## 1. 开发目录约定

统一目录：

```bash
/root/project
```

本项目目录：

```bash
/root/project/mcp_query_table
```

## 2. 开发环境

建议使用当前机器公共 Python 环境：

```bash
/root/.venv/bin/python
```

检查环境：

```bash
python3 --version
which python3
```

## 3. 安装依赖

```bash
cd /root/project/mcp_query_table
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

如果需要可编辑安装：

```bash
python3 -m pip install -e .
```

## 4. 常用开发流程

### 直接调试查询

```bash
cd /root/project/mcp_query_table
python3 examples/main.py
```

### 启动本地 MCP 服务

```bash
cd /root/project/mcp_query_table
python3 -m mcp_query_table --format markdown --endpoint http://127.0.0.1:9222
```

### 用 Inspector 调试

```bash
npx @modelcontextprotocol/inspector \
  python -m mcp_query_table --format markdown --endpoint http://127.0.0.1:9222
```

如果页面查询耗时较长，可以在浏览器中打开：

```text
http://localhost:5173/?timeout=300000
```

## 5. 代码组织建议

### 新增站点适配

1. 在 `mcp_query_table/sites/` 新建站点模块
2. 在 `tool.py` 中按 `Site` 分发
3. 更新 `README.md` 和 `docs/API.md`

### 新增对话提供商

1. 在 `mcp_query_table/providers/` 新建实现
2. 在 `tool.py` 中按 `Provider` 分发
3. 补充使用说明

## 6. 提交规范

建议使用：

- `feat:`
- `fix:`
- `docs:`
- `refactor:`
- `test:`

示例：

```bash
git add .
git commit -m "refactor: reorganize project layout and docs"
```

## 7. 开发注意事项

- 不要提交浏览器缓存、运行日志和编译产物
- 修改站点适配后要手工回归关键查询
- 页面抓取逻辑尽量减少对脆弱 CSS 选择器的依赖
- 默认路径和文档要以 `/root/project/mcp_query_table` 为准
