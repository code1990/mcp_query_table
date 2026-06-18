import unittest
from types import SimpleNamespace

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


class IwencaiTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        iwencai.P.reset()

    def test_convert_type(self):
        self.assertIs(iwencai.convert_type("LONG"), int)
        self.assertIs(iwencai.convert_type("DOUBLE"), float)
        self.assertIs(iwencai.convert_type("STR"), str)
        self.assertIs(iwencai.convert_type("DATE"), str)

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


if __name__ == "__main__":
    unittest.main()
