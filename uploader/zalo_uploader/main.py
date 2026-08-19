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
from utils.log import zalo_logger


async def cookie_auth(account_file: str) -> bool:
    """Check whether Zalo OA / Zalo cookies are valid."""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=LOCAL_CHROME_HEADLESS,
            args=["--disable-blink-features=AutomationControlled", "--lang=vi-VN"],
        )
        context = await browser.new_context(
            storage_state=account_file,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        context = await set_init_script(context)
        page = await context.new_page()

        try:
            await page.goto("https://oa.zalo.me/manage/content/video", timeout=30000)
            await page.wait_for_load_state("domcontentloaded", timeout=15000)
            await asyncio.sleep(2)

            if "login" in page.url:
                # Try chat.zalo.me
                await page.goto("https://chat.zalo.me/", timeout=20000)
                await asyncio.sleep(2)
                if "login" in page.url or await page.locator("text=Quét mã QR").count() > 0:
                    zalo_logger.error("[Zalo] Cookie expired or login required.")
                    return False

            zalo_logger.success("[Zalo] Cookie is valid.")
            return True
        except Exception as e:
            zalo_logger.error(f"[Zalo] Auth check error: {e}")
            return False
        finally:
            await context.close()
            await browser.close()


async def get_zalo_cookie(account_file: str):
    """Open browser for QR / manual login to Zalo and save cookie session."""
    Path(account_file).parent.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as playwright:
        options = {
            "args": ["--disable-blink-features=AutomationControlled", "--lang=vi-VN"],
            "headless": False,
        }
        browser = await playwright.chromium.launch(**options)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto("https://id.zalo.me/account?continue=https%3A%2F%2Foa.zalo.me%2Fmanage%2Fcontent%2Fvideo")
        zalo_logger.info("[Zalo] Please scan QR code or log in to Zalo in the opened browser window.")
        
        await page.pause()
        await context.storage_state(path=account_file)
        zalo_logger.success(f"[Zalo] Cookie saved to {account_file}")
        await context.close()
        await browser.close()


async def zalo_setup(account_file: str, handle: bool = False) -> bool:
    """Setup and verify Zalo account cookies."""
    account_path = Path(account_file)
    if not account_path.is_absolute():
        account_file = str(Path(BASE_DIR) / "cookies" / account_file)
    
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            return False
        zalo_logger.info(f"[Zalo] Cookie file missing or expired. Opening login window...")
        await get_zalo_cookie(account_file)
    return True


class ZaloVideo(BaseVideoUploader):
    def __init__(
        self,
        title: str,
        file_path: str | Path,
        tags: list[str] | None = None,
        publish_date: datetime | int | None = 0,
        account_file: str = "zalo_cookie.json",
        description: str = "",
        category: str = "",
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
        self.category = category
        self.headless = LOCAL_CHROME_HEADLESS

    async def upload(self) -> bool:
        """Upload video to Zalo Official Account / Video."""
        zalo_logger.info(f"[Zalo] Starting video upload: {self.file_path.name}")
        
        if not await zalo_setup(self.account_file, handle=True):
            zalo_logger.error("[Zalo] Authentication failed.")
            return False

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled", "--lang=vi-VN"],
            )
            context = await browser.new_context(
                storage_state=self.account_file,
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
            )
            context = await set_init_script(context)
            page = await context.new_page()

            try:
                zalo_logger.info("[Zalo] Opening Zalo OA video management...")
                await page.goto("https://oa.zalo.me/manage/content/video/create", timeout=35000)
                await page.wait_for_load_state("domcontentloaded", timeout=15000)
                await asyncio.sleep(2)

                # Attach media file
                file_input = page.locator("input[type='file']")
                if await file_input.count() > 0:
                    zalo_logger.info("[Zalo] Uploading video file...")
                    await file_input.first.set_input_files(str(self.file_path))
                    await asyncio.sleep(5)

                # Fill title
                title_input = page.locator("input[placeholder*='tiêu đề' i], input[placeholder*='title' i], input[name='title']").first
                if await title_input.count() > 0:
                    await title_input.fill(self.title)
                    zalo_logger.info(f"[Zalo] Added title: {self.title}")

                # Fill description & hashtags
                desc_text = self.description or self.title
                if self.tags:
                    desc_text += " " + " ".join([f"#{t.lstrip('#')}" for t in self.tags])

                desc_input = page.locator("textarea[placeholder*='mô tả' i], div[contenteditable='true'], textarea[name='description']").first
                if await desc_input.count() > 0:
                    await desc_input.fill(desc_text)
                    zalo_logger.info("[Zalo] Added description.")

                await asyncio.sleep(3)

                # Click Submit / Đăng video button
                publish_btn = page.get_by_role("button", name=re.compile(r"^(Đăng|Xuất bản|Lưu|Hoàn tất|Publish)$", re.I)).first
                if await publish_btn.count() > 0:
                    await publish_btn.click()
                    zalo_logger.info("[Zalo] Submitting video...")
                    await asyncio.sleep(6)

                zalo_logger.success(f"[Zalo] Video uploaded successfully: {self.title}")
                return True
            except Exception as e:
                zalo_logger.error(f"[Zalo] Error during Zalo video upload: {e}")
                return False
            finally:
                await context.close()
                await browser.close()
