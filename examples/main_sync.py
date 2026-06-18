"""
本示例演示如何用同步风格调用项目中的异步查询接口。

适合 Python REPL 或直接脚本运行，不适合 Windows 下的 Jupyter Notebook。
"""

import revolving_asyncio  # pip install revolving_asyncio

from mcp_query_table import BrowserManager, QueryType, Site, query

bm = BrowserManager(
    endpoint="http://127.0.0.1:9333",
    executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    devtools=False,
)
query_sync = revolving_asyncio.to_sync(query)
get_page = revolving_asyncio.to_sync(bm.get_page)
release_page = revolving_asyncio.to_sync(bm.release_page)

page1 = get_page()
page2 = get_page()

df = query_sync(page2, "收盘价>50元的港股", query_type=QueryType.HKStock, max_page=3, site=Site.THS)
print(df.to_markdown())

df = query_sync(page1, "年初至今收益率前50", query_type=QueryType.Fund, max_page=3, site=Site.TDX)
print(df.to_csv())

df = query_sync(page2, "收盘价>50元", query_type=QueryType.HKStock, max_page=3, site=Site.EastMoney)
release_page(page1)
release_page(page2)
print(df)
