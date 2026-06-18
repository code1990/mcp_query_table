import asyncio

from mcp_query_table import AsyncBrowser, QueryType, Site, query
from mcp_query_table.playwright_helper import get_chrome_path, get_chrome_use_data


async def main() -> None:
    endpoint = "http://127.0.0.1:9222"
    executable_path = get_chrome_path()
    user_data_dir = str(get_chrome_use_data())

    async with AsyncBrowser(
            endpoint=endpoint,
            executable_path=executable_path,
            devtools=False,
            user_data_dir=user_data_dir) as browser:
        page = await browser.get_page()
        df = await query(page, '收益最好的200只ETF', query_type=QueryType.ETF, max_page=1, site=Site.THS)
        print(df.to_markdown())
        df = await query(page, '年初至今收益率前50', query_type=QueryType.Fund, max_page=1, site=Site.TDX)
        print(df.to_csv())
        df = await query(page, '流通市值前10的行业板块', query_type=QueryType.Index, max_page=1, site=Site.TDX)
        print(df.to_csv())
        # TODO 东财翻页要提前登录
        df = await query(page, '今日涨幅前5的概念板块;', query_type=QueryType.Board, max_page=3, site=Site.EastMoney)
        print(df)
        await browser.release_page(page)
        print('done')


if __name__ == '__main__':
    asyncio.run(main())
