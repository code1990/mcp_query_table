import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from mcp_query_table.enums import QueryType
from mcp_query_table.sites import iwencai


class FakeResponse:
    def __init__(self, url, payload=None):
        self.url = url
        self._payload = payload or {}

    async def json(self):
        return self._payload


class FakeLocator:
    def __init__(self, text=None, click_ok=True):
        self.text = text
        self.click_ok = click_ok
        self.click_count = 0

    @property
    def first(self):
        return self

    async def inner_text(self):
        if self.text is None:
            raise RuntimeError("missing text")
        return self.text

    async def click(self):
        self.click_count += 1
        if not self.click_ok:
            raise RuntimeError("click failed")


class FakeExpectResponse:
    def __init__(self, response):
        self.response = response
        self.value = None

    async def __aenter__(self):
        self.value = self._resolve()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def _resolve(self):
        return self.response


class FakePage:
    def __init__(self, current_text="显示50条/页", click_ok=True, response_url=iwencai._PAGE2_):
        self.current_text = current_text
        self.click_ok = click_ok
        self.response_url = response_url
        self.goto_url = None
        self.viewport = None
        self.route_calls = []
        self._response = FakeResponse(response_url, {})
        self.dropdown = FakeLocator(click_ok=click_ok)
        self.option = FakeLocator(click_ok=click_ok)
        self.next_link = FakeLocator(click_ok=click_ok)

    def locator(self, selector):
        if "span" in selector and "drop-down-box" in selector:
            return FakeLocator(text=self.current_text)
        if "drop-down-box" in selector:
            return self.dropdown
        if "next-link" in selector:
            return self.next_link
        return FakeLocator()

    def get_by_text(self, text, exact=False):
        if text.startswith("显示"):
            return self.option
        if text == "下页":
            return self.next_link
        return FakeLocator()

    async def route(self, pattern, handler):
        self.route_calls.append(pattern.pattern)

    async def set_viewport_size(self, size):
        self.viewport = size

    async def goto(self, url, wait_until="load"):
        self.goto_url = url

    def expect_response(self, predicate):
        return FakeExpectResponse(self._response)


class HiddenPaginationPage:
    def locator(self, selector):
        return self

    async def is_visible(self):
        return False


class IwencaiTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        iwencai.P.reset()

    def test_convert_type(self):
        self.assertIs(iwencai.convert_type("LONG"), int)
        self.assertIs(iwencai.convert_type("DOUBLE"), float)
        self.assertIs(iwencai.convert_type("STR"), str)
        self.assertIs(iwencai.convert_type("DATE"), str)

    def test_futures_query_type(self):
        self.assertEqual(iwencai._querytype_[QueryType.Futures], "futures")

    def test_scope_menu_query_types(self):
        expected = {
            QueryType.CNStock: "stock",
            QueryType.AShareIndex: "azhishu",
            QueryType.ListedETF: "listedfund",
            QueryType.FundManager: "fundmanager",
            QueryType.FundCompany: "fundcompany",
            QueryType.HKIndex: "hkzhishu",
            QueryType.USIndex: "uszhishu",
            QueryType.ThreeBoard: "threeboard",
            QueryType.Insurance: "insurance",
            QueryType.WealthManagement: "lccp",
            QueryType.Forex: "foreign_exchange",
            QueryType.Macro: "macro",
        }
        for query_type, querytype in expected.items():
            self.assertEqual(iwencai._querytype_[query_type], querytype)

    def test_parse_robot_and_datalist(self):
        robot = {
            "data": {
                "answer": [
                    {
                        "txt": [
                            {
                                "content": {
                                    "components": [
                                        {
                                            "data": {
                                                "datas": [{"a": 1}],
                                                "columns": [{"key": "a", "index_name": "A", "type": "LONG"}],
                                                "meta": {"page": 1, "limit": 100, "extra": {"row_count": 1000}},
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        }
        self.assertEqual(iwencai.get_robot_data(robot), ([{"a": 1}], [{"key": "a", "index_name": "A", "type": "LONG"}], 1, 100, 1000))

        data_list = {
            "answer": {
                "components": [
                    {
                        "data": {
                            "datas": [{"a": 2}],
                            "columns": [{"key": "a", "index_name": "A", "type": "LONG"}],
                            "meta": {"page": "2", "limit": "50", "extra": {"row_count": 1000}},
                        }
                    }
                ]
            }
        }
        self.assertEqual(iwencai.getDataList(data_list), ([{"a": 2}], [{"key": "a", "index_name": "A", "type": "LONG"}], 2, 50, 1000))

    def test_pagination_dataframe_sorted_and_renamed(self):
        iwencai.P.update([{"a": "2"}], [{"key": "a", "index_name": "A", "type": "LONG"}], 2, 50, 100)
        iwencai.P.update([{"a": "1"}], [{"key": "a", "index_name": "A", "type": "LONG"}], 1, 50, 100)

        df = iwencai.P.get_dataframe(rename=True)
        self.assertEqual(list(df["A"]), [1, 2])
        self.assertEqual(df["A"].dtype.kind, "i")

    def test_new_table_dataframe(self):
        df = iwencai.get_new_dataframe(["股票代码", "股票简称"], [["000001", "平安银行"], ["000002", "万科A"]])
        self.assertEqual(df.to_dict("records"), [
            {"股票代码": "000001", "股票简称": "平安银行"},
            {"股票代码": "000002", "股票简称": "万科A"},
        ])

    async def test_query_new_reads_single_page_when_pagination_is_hidden(self):
        frame = iwencai.pd.DataFrame([{"股票代码": "000001"}])
        with patch.object(iwencai, "sort_new_by_primary", new_callable=AsyncMock) as sort, \
             patch.object(iwencai, "switch_new_page_size", new_callable=AsyncMock) as switch, \
             patch.object(iwencai, "get_new_table", new_callable=AsyncMock, return_value=frame):
            result = await iwencai.query_new(HiddenPaginationPage(), max_page=10)

        self.assertEqual(result.to_dict("records"), [{"股票代码": "000001"}])
        sort.assert_awaited_once()
        switch.assert_not_awaited()

    async def test_switch_page_size_noop_when_already_target(self):
        page = FakePage(current_text="显示100条/页")
        changed = await iwencai.switch_page_size(page, 100)
        self.assertFalse(changed)
        self.assertEqual(page.dropdown.click_count, 0)

    async def test_switch_page_size_clicks_and_updates(self):
        payload = {
            "answer": {
                "components": [
                    {
                        "data": {
                            "datas": [],
                            "columns": [],
                            "meta": {"page": 1, "limit": 100, "extra": {"row_count": 0}},
                        }
                    }
                ]
            }
        }
        page = FakePage(current_text="显示50条/页", response_url=iwencai._PAGE2_)
        page._response = FakeResponse(iwencai._PAGE2_, payload)
        changed = await iwencai.switch_page_size(page, 100)
        self.assertTrue(changed)
        self.assertEqual(page.dropdown.click_count, 1)
        self.assertEqual(page.option.click_count, 1)

    async def test_query_rejects_unsupported_type(self):
        page = FakePage()
        with self.assertRaises(TypeError):
            await iwencai.query(page, type_=SimpleNamespace())

    async def test_query_builds_screening_url(self):
        payload = {
            "data": {
                "answer": [
                    {
                        "txt": [
                            {
                                "content": {
                                    "components": [
                                        {
                                            "data": {
                                                "datas": [],
                                                "columns": [],
                                                "meta": {"page": 1, "limit": 100, "extra": {"row_count": 0}},
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        }
        page = FakePage(current_text="显示100条/页", response_url=iwencai._PAGE1_)
        page._response = FakeResponse(iwencai._PAGE1_, payload)

        df = await iwencai.query(page, w="测试条件", type_=QueryType.CNStock, max_page=1, rename=False)

        self.assertIn("https://www.iwencai.com/screener/result?w=测试条件&querytype=stock", page.goto_url)
        self.assertTrue(df.empty)

    async def test_query_applies_each_scope_querytype(self):
        payload = {
            "data": {
                "answer": [
                    {
                        "txt": [
                            {
                                "content": {
                                    "components": [
                                        {
                                            "data": {
                                                "datas": [],
                                                "columns": [],
                                                "meta": {"page": 1, "limit": 100, "extra": {"row_count": 0}},
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        }
        for query_type, querytype in iwencai._querytype_.items():
            if not isinstance(query_type, QueryType):
                continue
            page = FakePage(current_text="显示100条/页", response_url=iwencai._PAGE1_)
            page._response = FakeResponse(iwencai._PAGE1_, payload)
            await iwencai.query(page, w="测试条件", type_=query_type, max_page=1, rename=False)
            self.assertIn(f"querytype={querytype}", page.goto_url)


if __name__ == "__main__":
    unittest.main()
