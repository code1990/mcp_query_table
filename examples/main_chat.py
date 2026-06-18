import asyncio

from mcp_query_table import AsyncBrowser, chat
from mcp_query_table.enums import Provider
from mcp_query_table.playwright_helper import get_chrome_path, get_chrome_use_data


async def main() -> None:
    async with AsyncBrowser(
            endpoint="http://127.0.0.1:9222",
            executable_path=get_chrome_path(),
            devtools=False,
            user_data_dir=str(get_chrome_use_data())) as browser:
        page1 = await browser.get_page()
        page2 = await browser.get_page()

        with open("mcp.txt", 'r', encoding='utf-8') as f:
            prompt = f.read()

        files = [
            # r"D:\Users\Kan\Documents\GitHub\mcp_query_table\examples\mcp.txt",
            r"d:\1.png"
        ]

        output = await chat(page1, "2+3等于多少？", provider=Provider.BaiDu)
        print(output)
        output = await chat(page1, "3+4等于多少？", provider=Provider.Nami)
        print(output)
        output = await chat(page2, "4+5等于多少？", provider=Provider.YuanBao)
        print(output)
        output = await chat(page2, "这张照片的拍摄参数是多少？", files=files, provider=Provider.Nami)
        print(output)
        output = await chat(page2, "描述下文件内容", files=files, provider=Provider.YuanBao)
        print(output)
        output = await chat(page2, "描述下文件内容", files=files, provider=Provider.BaiDu)
        print(output)

        await browser.release_page(page1)
        await browser.release_page(page2)


if __name__ == '__main__':
    asyncio.run(main())
