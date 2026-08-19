# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import os
import re
from datetime import datetime
from pathlib import Path

from playwright.async_api import Playwright, async_playwright

from conf import BASE_DIR, LOCAL_CHROME_HEADLESS
from uploader.base_video import BaseVideoUploader
from utils.base_social_media import set_init_script
from utils.log import pinterest_logger


async def cookie_auth(account_file: str) -> bool:
    """Check whether Pinterest cookies are valid."""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=LOCAL_CHROME_HEADLESS,
            args=["--disable-blink-features=AutomationControlled", "--lang=en-US"],
        )
        context = await browser.new_context(
            storage_state=account_file,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        context = await set_init_script(context)
        page = await context.new_page()

        try:
            await page.goto("https://www.pinterest.com/pin-creation-tool/", timeout=30000)
            await page.wait_for_load_state("domcontentloaded", timeout=15000)
            await asyncio.sleep(2)

            if "login" in page.url:
                pinterest_logger.error("[Pinterest] Cookie expired or login required.")
                return False

            pinterest_logger.success("[Pinterest] Cookie is valid.")
            return True
        except Exception as e:
            pinterest_logger.error(f"[Pinterest] Auth check error: {e}")
            return False
        finally:
            await context.close()
            await browser.close()


async def get_pinterest_cookie(account_file: str):
    """Open browser for manual login and save cookie session."""
    Path(account_file).parent.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as playwright:
        options = {
            "args": ["--disable-blink-features=AutomationControlled", "--lang=en-US"],
            "headless": False,
        }
        browser = await playwright.chromium.launch(**options)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto("https://www.pinterest.com/login/")
        pinterest_logger.info("[Pinterest] Please log in to Pinterest in the opened browser window.")
        
        await page.pause()
        await context.storage_state(path=account_file)
        pinterest_logger.success(f"[Pinterest] Cookie saved to {account_file}")
        await context.close()
        await browser.close()


async def pinterest_setup(account_file: str, handle: bool = False) -> bool:
    """Setup and verify Pinterest account cookies."""
    account_path = Path(account_file)
    if not account_path.is_absolute():
        account_file = str(Path(BASE_DIR) / "cookies" / account_file)
    
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            return False
        pinterest_logger.info(f"[Pinterest] Cookie file missing or expired. Opening login window...")
        await get_pinterest_cookie(account_file)
    return True


class PinterestVideo(BaseVideoUploader):
    def __init__(
        self,
        title: str,
        file_path: str | Path,
        tags: list[str] | None = None,
        publish_date: datetime | int | None = 0,
        account_file: str = "pinterest_cookie.json",
        description: str = "",
        link: str = "",
        board: str = "",
    ):
        self.title = title
        self.file_path = self.validate_video_file(file_path)
        self.tags = tags or []
        self.publish_date = self.validate_publish_date(publish_date)
        
        account_path = Path(account_file)
        if not account_path.is_absolute():
            self.account_file = str(Path(BASE_DIR) / "cookies" / account_file)
        else:
            self.account_file = account_file
            
        self.description = description
        self.link = link
        self.board = board
        self.headless = LOCAL_CHROME_HEADLESS

    async def upload(self) -> bool:
        """Upload Video Pin to Pinterest."""
        pinterest_logger.info(f"[Pinterest] Starting video pin upload: {self.file_path.name}")
        
        if not await pinterest_setup(self.account_file, handle=True):
            pinterest_logger.error("[Pinterest] Authentication failed.")
            return False

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled", "--lang=en-US"],
            )
            context = await browser.new_context(
                storage_state=self.account_file,
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
            )
            context = await set_init_script(context)
            page = await context.new_page()

            try:
                pinterest_logger.info("[Pinterest] Opening Pin creation tool...")
                await page.goto("https://www.pinterest.com/pin-creation-tool/", timeout=35000)
                await page.wait_for_load_state("domcontentloaded", timeout=15000)
                await asyncio.sleep(2)

                # Attach media file
                file_input = page.locator("input[type='file']")
                if await file_input.count() > 0:
                    pinterest_logger.info("[Pinterest] Uploading video file...")
                    await file_input.first.set_input_files(str(self.file_path))
                    await asyncio.sleep(5)

                # Fill title
                title_input = page.locator("input[placeholder*='title' i], input[placeholder*='tiêu đề' i], #storyboard-selector-title").first
                if await title_input.count() > 0:
                    await title_input.fill(self.title)
                    pinterest_logger.info(f"[Pinterest] Added title: {self.title}")

                # Fill description & hashtags
                desc_text = self.description or self.title
                if self.tags:
                    desc_text += " " + " ".join([f"#{t.lstrip('#')}" for t in self.tags])

                desc_input = page.locator("div[aria-label*='description' i], div[contenteditable='true'], textarea[placeholder*='description' i]").first
                if await desc_input.count() > 0:
                    await desc_input.fill(desc_text)
                    pinterest_logger.info("[Pinterest] Added description.")

                # Fill link if given
                if self.link:
                    link_input = page.locator("input[placeholder*='link' i]").first
                    if await link_input.count() > 0:
                        await link_input.fill(self.link)

                await asyncio.sleep(3)

                # Click Publish / Save button
                save_btn = page.locator("button[data-test-id='board-dropdown-save-button'], button:has-text('Publish'), button:has-text('Lưu')").first
                if await save_btn.count() > 0:
                    await save_btn.click()
                    pinterest_logger.info("[Pinterest] Submitting pin...")
                    await asyncio.sleep(6)

                pinterest_logger.success(f"[Pinterest] Pin created successfully: {self.title}")
                return True
            except Exception as e:
                pinterest_logger.error(f"[Pinterest] Error during pin creation: {e}")
                return False
            finally:
                await context.close()
                await browser.close()
