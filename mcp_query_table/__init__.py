from ._version import __version__

from .enums import QueryType, Site, Provider
from .playwright_helper import AsyncBrowser, SyncBrowser
from .tool import query, chat

BrowserManager = AsyncBrowser

TIMEOUT = 1000 * 60 * 3  # 3分钟，在抓取EventStream数据时等待数据返回，防止外层30秒超时
TIMEOUT_60 = 1000 * 60  # 1分钟

# TODO 临时测试
# TIMEOUT = None
# TIMEOUT_60 = None
