# 架构文档

## 1. 总体结构

项目分为四层：

1. 浏览器连接层：`playwright_helper.py`
2. 站点适配层：`sites/`
3. 能力封装层：`tool.py`
4. MCP 服务层：`server.py`、`__main__.py`

## 2. 核心模块

### `playwright_helper.py`

- 负责启动或连接浏览器
- 同时支持本地 CDP、远程 Playwright Server、直接拉起浏览器
- 统一提供 `get_page()` 和 `release_page()` 入口

### `sites/`

- 每个网站一个独立适配器
- 负责页面跳转、请求拦截、分页翻页和结果解析
- 当前包括：
  - `iwencai.py`
  - `tdx.py`
  - `eastmoney.py`

### `providers/`

- 封装纳米搜索、腾讯元宝、百度 AI 搜索等页面对话逻辑
- 主要用于把网页对话结果提取成纯文本

### `tool.py`

- 统一对外暴露 `query()` 和 `chat()`
- 按 `Site` 或 `Provider` 分发到具体实现

### `server.py`

- 使用 `fastmcp` 暴露 `query` 工具
- 管理浏览器实例与格式化输出

## 3. 调用链路

### 表格查询

1. 调用方传入查询条件、站点和查询类型
2. `tool.py` 选择对应 `sites/*` 适配器
3. 适配器驱动浏览器打开页面
4. 监听页面响应并提取结构化数据
5. 组装为 `pandas.DataFrame`
6. 调用方决定输出为 Markdown、CSV 或 JSON

### MCP 查询

1. `python -m mcp_query_table` 启动服务
2. `server.py` 初始化浏览器连接
3. MCP 客户端调用 `query` 工具
4. `QueryServer.query()` 执行实际网页查询
5. 结果按服务启动时指定格式返回

## 4. 设计特点

- 以真实浏览器行为代替手写请求
- 各站点适配互相隔离，便于单独修复
- MCP 与 Python 库共用同一套底层查询能力
- 适合频繁变化、难以稳定逆向的网页型数据源

## 5. 已知限制

- 强依赖网页结构，站点改版后需要重新适配
- 首次查询速度明显慢于直接 HTTP API
- 当前缺少系统化自动化测试
- 当前未内建鉴权、缓存和速率限制
