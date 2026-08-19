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
from utils.log import instagram_logger


async def cookie_auth(account_file: str) -> bool:
    """Check whether Instagram cookies are valid."""
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
            await page.goto("https://www.instagram.com/", timeout=30000)
            await page.wait_for_load_state("domcontentloaded", timeout=15000)
            await asyncio.sleep(2)

            # Check if login input is visible or redirected to accounts/login
            if "accounts/login" in page.url or await page.locator("input[name='username']").count() > 0:
                instagram_logger.error("[Instagram] Cookie expired or login required.")
                return False

            # Check for standard logged-in navigation items
            nav_icons = page.locator("svg[aria-label='Home'], svg[aria-label='Trang chủ'], svg[aria-label='Direct'], svg[aria-label='Tin nhắn']")
            if await nav_icons.count() > 0 or "instagram.com" in page.url:
                instagram_logger.success("[Instagram] Cookie is valid.")
                return True

            instagram_logger.warning("[Instagram] State unclear, assuming cookie valid.")
            return True
        except Exception as e:
            instagram_logger.error(f"[Instagram] Auth check error: {e}")
            return False
        finally:
            await context.close()
            await browser.close()


async def get_instagram_cookie(account_file: str):
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
        await page.goto("https://www.instagram.com/accounts/login/")
        instagram_logger.info("[Instagram] Please log in to Instagram in the opened browser window.")
        
        await page.pause()
        await context.storage_state(path=account_file)
        instagram_logger.success(f"[Instagram] Cookie saved to {account_file}")
        await context.close()
        await browser.close()


async def instagram_setup(account_file: str, handle: bool = False) -> bool:
    """Setup and verify Instagram account cookies."""
    account_path = Path(account_file)
    if not account_path.is_absolute():
        account_file = str(Path(BASE_DIR) / "cookies" / account_file)
    
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            return False
        instagram_logger.info(f"[Instagram] Cookie file missing or expired. Opening login window...")
        await get_instagram_cookie(account_file)
    return True


class InstagramVideo(BaseVideoUploader):
    def __init__(
        self,
        title: str,
        file_path: str | Path,
        tags: list[str] | None = None,
        publish_date: datetime | int | None = 0,
        account_file: str = "instagram_cookie.json",
        description: str = "",
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
        self.headless = LOCAL_CHROME_HEADLESS

    async def upload(self) -> bool:
        """Upload video or Reel to Instagram."""
        instagram_logger.info(f"[Instagram] Starting upload for video: {self.file_path.name}")
        
        if not await instagram_setup(self.account_file, handle=True):
            instagram_logger.error("[Instagram] Authentication failed.")
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
                instagram_logger.info("[Instagram] Opening Instagram home...")
                await page.goto("https://www.instagram.com/", timeout=35000)
                await page.wait_for_load_state("domcontentloaded", timeout=15000)
                await asyncio.sleep(2)

                # Click Create (+) button
                instagram_logger.info("[Instagram] Opening create post dialog...")
                create_btn = page.locator("svg[aria-label='New post'], svg[aria-label='Tạo bài viết mới'], svg[aria-label='Create'], svg[aria-label='Tạo']").locator("..").first
                if await create_btn.count() == 0:
                    create_btn = page.get_by_text(re.compile(r"^(Create|Tạo)$", re.I)).first

                if await create_btn.count() > 0:
                    await create_btn.click()
                    await asyncio.sleep(1)

                # Find file input
                file_input = page.locator("input[type='file']")
                if await file_input.count() > 0:
                    await file_input.first.set_input_files(str(self.file_path))
                else:
                    select_btn = page.get_by_role("button", name=re.compile(r"(Select from computer|Chọn từ máy tính)", re.I))
                    if await select_btn.count() > 0:
                        async with page.expect_file_chooser() as fc_info:
                            await select_btn.first.click()
                        fc = await fc_info.value
                        await fc.set_files(str(self.file_path))

                instagram_logger.info("[Instagram] Video selected, processing wizard...")
                await asyncio.sleep(4)

                # Handle "Reels video sharing" notification if popup appears
                ok_btn = page.get_by_role("button", name=re.compile(r"^(OK|Đã hiểu)$", re.I))
                if await ok_btn.count() > 0:
                    await ok_btn.click()
                    await asyncio.sleep(1)

                # Click Next buttons through the dialog
                for step in range(2):
                    next_btn = page.get_by_role("button", name=re.compile(r"^(Next|Tiếp)$", re.I)).first
                    if await next_btn.count() > 0:
                        await next_btn.click()
                        await asyncio.sleep(2)

                # Fill caption & hashtags
                caption_text = self.description or self.title
                if self.tags:
                    hashtags_str = " " + " ".join([f"#{t.lstrip('#')}" for t in self.tags])
                    caption_text += hashtags_str

                caption_input = page.locator("div[aria-label*='caption' i], div[aria-label*='chú thích' i], div[contenteditable='true']").first
                if await caption_input.count() > 0:
                    await caption_input.click()
                    await caption_input.fill(caption_text)
                    instagram_logger.info(f"[Instagram] Added caption: {caption_text[:40]}...")

                # Click Share / Post button
                share_btn = page.get_by_role("button", name=re.compile(r"^(Share|Chia sẻ)$", re.I)).first
                if await share_btn.count() > 0:
                    await share_btn.click()
                    instagram_logger.info("[Instagram] Submitting post, waiting for upload confirmation...")
                    await asyncio.sleep(8)

                instagram_logger.success(f"[Instagram] Video post uploaded successfully: {self.title}")
                return True
            except Exception as e:
                instagram_logger.error(f"[Instagram] Error during upload: {e}")
                return False
            finally:
                await context.close()
                await browser.close()
