#!/usr/bin/env python3
"""
Minimal standalone iWenCai fetcher for the 2026 screener UI.

Dependencies:
- pandas
- playwright
- playwright-stealth>=2.0.0 (optional)

Example:
    python iwencai_single.py
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from enum import Enum
from pathlib import Path

import pandas as pd
from playwright.async_api import Page, async_playwright

try:
    from playwright_stealth import Stealth
except Exception:  # pragma: no cover - optional dependency
    Stealth = None


logger = logging.getLogger(__name__)


class QueryType(Enum):
    CNStock = "stock"
    Index = "zhishu"
    Fund = "fund"
    HKStock = "hkstock"
    USStock = "usstock"
    ConBond = "conbond"
    ETF = "fund"


PAGE1_URL = "https://www.iwencai.com/unifiedwap/unified-wap/v2/result/get-robot-data"
PAGE2_URL = "https://www.iwencai.com/gateway/urp/v7/landing/getDataList"


def convert_type(type_name: str):
    if type_name == "LONG":
        return int
    if type_name == "DOUBLE":
        return float
    if type_name == "STR":
        return str
    if type_name == "INT":
        return int
    return type_name


class Pagination:
    def __init__(self) -> None:
        self.datas: dict[int, list[dict]] = {}
        self.limit = 100
        self.page = 1
        self.row_count = 0
        self.columns: list[dict] = []

    def reset(self) -> None:
        self.datas = {}
        self.limit = 100
        self.page = 1
        self.row_count = 0
        self.columns = []

    def update(self, datas, columns, page, limit, row_count) -> None:
        self.datas[page] = datas
        self.columns = columns
        self.limit = int(limit)
        self.page = int(page)
        self.row_count = int(row_count)

    def has_next(self, max_page: int) -> bool:
        return self.page * self.limit < self.row_count and self.page < max_page

    def get_dataframe(self, rename: bool) -> pd.DataFrame:
        rows: list[dict] = []
        for page in sorted(self.datas):
            rows.extend(self.datas[page])

        columns = {x["key"]: x["index_name"] for x in self.columns}
        dtypes = {x["key"]: convert_type(x["type"]) for x in self.columns}
        df = pd.DataFrame(rows)
        for key, dtype in dtypes.items():
            if isinstance(dtype, str):
                continue
            try:
                df[key] = df[key].astype(dtype)
            except Exception:
                logger.info("convert failed {}:{}", key, dtype)

        return df.rename(columns=columns) if rename else df


P = Pagination()


def parse_page1(json_data):
    data = json_data["data"]["answer"][0]["txt"][0]["content"]["components"][0]["data"]
    meta = data["meta"]
    return data["datas"], data["columns"], int(meta["page"]), int(meta["limit"]), int(meta["extra"]["row_count"])


def parse_page2(json_data):
    data = json_data["answer"]["components"][0]["data"]
    meta = data["meta"]
    return data["datas"], data["columns"], int(meta["page"]), int(meta["limit"]), int(meta["extra"]["row_count"])


async def on_response(response) -> None:
    if response.url.startswith(PAGE1_URL):
        P.update(*parse_page1(await response.json()))
    if response.url.startswith(PAGE2_URL):
        P.update(*parse_page2(await response.json()))


async def switch_page_size(page: Page, page_size: int = 100) -> bool:
    target_text = f"显示{page_size}条/页"
    current_candidates = [
        page.locator(".drop-down-box span").first,
        page.locator(".pcwencai-pagination-wrap .drop-down-box span").first,
    ]
    current_text = None
    for current in current_candidates:
        try:
            current_text = (await current.inner_text()).strip()
            if current_text:
                break
        except Exception:
            continue
    if not current_text:
        return False
    if target_text in current_text:
        return False

    dropdown_candidates = [
        page.locator(".drop-down-box").first,
        page.locator(".pcwencai-pagination-wrap .drop-down-box").first,
    ]
    option_candidates = [
        page.get_by_text(target_text, exact=True),
        page.locator(f"text={target_text}").first,
    ]
    async with page.expect_response(lambda resp: resp.url.startswith(PAGE2_URL)) as resp_info:
        clicked = False
        for dropdown in dropdown_candidates:
            try:
                await dropdown.click()
                clicked = True
                break
            except Exception:
                continue
        if not clicked:
            return False

        chosen = False
        for option in option_candidates:
            try:
                await option.click()
                chosen = True
                break
            except Exception:
                continue
        if not chosen:
            return False
    await on_response(await resp_info.value)
    return True


async def query_iwencai(
    query_text: str,
    query_type: QueryType = QueryType.CNStock,
    max_page: int = 56,
    rename: bool = True,
    per_page: int = 100,
    headless: bool = True,
) -> pd.DataFrame:
    start_time = time.perf_counter()
    logger.info(
        "start query=%s type=%s max_page=%s per_page=%s headless=%s",
        query_text,
        query_type.value,
        max_page,
        per_page,
        headless,
    )
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        if Stealth is not None:
            try:
                await Stealth().apply_stealth_async(context)
            except Exception as exc:
                logger.warning("stealth apply failed: %s", exc)
        page = await context.new_page()
        await page.route(re.compile(r".*\\.(?:jpg|jpeg|png|gif|webp)(?:$|\\?)"), lambda route: route.abort())

        P.reset()
        logger.info("loading iwencai screener page")
        async with page.expect_response(lambda resp: resp.url.startswith(PAGE1_URL)) as resp_info:
            await page.goto(
                f"https://www.iwencai.com/screener/result?w={query_text}&querytype={query_type.value}",
                wait_until="load",
            )
        await on_response(await resp_info.value)
        logger.info("loaded first page rows=%s limit=%s total=%s", len(P.datas.get(1, [])), P.limit, P.row_count)

        try:
            changed = await switch_page_size(page, per_page)
            if changed:
                logger.info("switched page size to %s", per_page)
            else:
                logger.info("page size already %s or switch skipped", per_page)
        except Exception as exc:
            logger.warning("switch page size failed: %s", exc)

        next_link_candidates = [
            page.locator(".next-link").first,
            page.locator(".pcwencai-pagination-wrap .next-link").first,
            page.get_by_text("下页", exact=True),
        ]
        while P.has_next(max_page):
            logger.info("page %s / approx %s", P.page, (P.row_count + P.limit - 1) // P.limit)
            async with page.expect_response(lambda resp: resp.url.startswith(PAGE2_URL)) as resp_info:
                clicked = False
                for next_link in next_link_candidates:
                    try:
                        await next_link.click()
                        clicked = True
                        break
                    except Exception:
                        continue
                if not clicked:
                    raise RuntimeError("next page control not found")
            await on_response(await resp_info.value)

        df = P.get_dataframe(rename)
        logger.info(
            "finished rows=%s cols=%s pages=%s elapsed=%.2fs",
            len(df),
            len(df.columns),
            len(P.datas),
            time.perf_counter() - start_time,
        )
        await context.close()
        await browser.close()
        return df


async def _main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    start_time = time.perf_counter()
    out = Path("行业概念_single.xlsx")
    df = await query_iwencai("行业概念", QueryType.CNStock, max_page=56, rename=True, per_page=100)
    df.to_excel(out, index=False)
    logger.info("saved xlsx=%s elapsed=%.2fs", out.resolve(), time.perf_counter() - start_time)
    print(out.resolve())
    print(df.shape)
    print(df["股票代码"].nunique())


if __name__ == "__main__":
    asyncio.run(_main())
