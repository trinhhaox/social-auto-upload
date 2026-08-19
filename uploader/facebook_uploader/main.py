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
from utils.files_times import get_absolute_path
from utils.log import facebook_logger


async def cookie_auth(account_file: str) -> bool:
    """Check whether Facebook cookies are valid."""
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
            # Check Meta Business Suite or Facebook Home
            await page.goto("https://business.facebook.com/latest/home", timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)

            # If redirected to login page, cookie expired
            if "login" in page.url or "checkpoint" in page.url:
                facebook_logger.error("[Facebook] Cookie expired or login required.")
                return False

            facebook_logger.success("[Facebook] Cookie is valid.")
            return True
        except Exception as e:
            # Fallback check on standard facebook.com
            try:
                await page.goto("https://www.facebook.com/", timeout=20000)
                await page.wait_for_load_state("domcontentloaded", timeout=10000)
                if "login" in page.url or await page.locator("input[name='email']").count() > 0:
                    facebook_logger.error("[Facebook] Cookie expired.")
                    return False
                facebook_logger.success("[Facebook] Cookie is valid via Facebook Web.")
                return True
            except Exception as inner_e:
                facebook_logger.error(f"[Facebook] Auth check error: {inner_e}")
                return False
        finally:
            await context.close()
            await browser.close()


async def get_facebook_cookie(account_file: str):
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
        await page.goto("https://www.facebook.com/login")
        facebook_logger.info("[Facebook] Please log in to your Facebook account in the opened browser window.")
        
        # Wait for login completion
        await page.pause()
        await context.storage_state(path=account_file)
        facebook_logger.success(f"[Facebook] Cookie saved to {account_file}")
        await context.close()
        await browser.close()


async def facebook_setup(account_file: str, handle: bool = False) -> bool:
    """Setup and verify Facebook account cookies."""
    account_path = Path(account_file)
    if not account_path.is_absolute():
        account_file = str(Path(BASE_DIR) / "cookies" / account_file)
    
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            return False
        facebook_logger.info(f"[Facebook] Cookie file missing or expired. Opening login window...")
        await get_facebook_cookie(account_file)
    return True


class FacebookVideo(BaseVideoUploader):
    def __init__(
        self,
        title: str,
        file_path: str | Path,
        tags: list[str] | None = None,
        publish_date: datetime | int | None = 0,
        account_file: str = "facebook_cookie.json",
        description: str = "",
        is_reel: bool = True,
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
        self.is_reel = is_reel
        self.headless = LOCAL_CHROME_HEADLESS

    async def upload(self) -> bool:
        """Upload video or Reel to Facebook via Meta Business Suite / Web interface."""
        facebook_logger.info(f"[Facebook] Starting upload for video: {self.file_path.name}")
        
        if not await facebook_setup(self.account_file, handle=True):
            facebook_logger.error("[Facebook] Authentication failed.")
            return False

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled", "--lang=en-US"],
            )
            context = await browser.new_context(
                storage_state=self.account_file,
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                viewport={"width": 1366, "height": 768},
            )
            context = await set_init_script(context)
            page = await context.new_page()

            try:
                # Open Meta Business Suite Reel / Video composer
                facebook_logger.info("[Facebook] Navigating to Meta Business Suite composer...")
                target_url = "https://business.facebook.com/latest/reels_composer" if self.is_reel else "https://business.facebook.com/latest/content_management"
                await page.goto(target_url, timeout=40000)
                await page.wait_for_load_state("domcontentloaded", timeout=20000)
                await asyncio.sleep(3)

                # Locate file input
                facebook_logger.info("[Facebook] Uploading media file...")
                file_input = page.locator("input[type='file'][accept*='video']")
                if await file_input.count() == 0:
                    file_input = page.locator("input[type='file']")
                
                if await file_input.count() > 0:
                    await file_input.first.set_input_files(str(self.file_path))
                else:
                    facebook_logger.warning("[Facebook] File input not directly found, attempting button trigger...")
                    upload_btn = page.get_by_role("button", name=re.compile(r"(Add video|Upload|Thêm video)", re.I))
                    if await upload_btn.count() > 0:
                        async with page.expect_file_chooser() as fc_info:
                            await upload_btn.first.click()
                        file_chooser = await fc_info.value
                        await file_chooser.set_files(str(self.file_path))

                # Wait for video upload to process
                facebook_logger.info("[Facebook] Waiting for video processing...")
                await asyncio.sleep(6)

                # Fill description & hashtags
                caption_text = self.description or self.title
                if self.tags:
                    hashtags_str = " " + " ".join([f"#{t.lstrip('#')}" for t in self.tags])
                    caption_text += hashtags_str

                caption_input = page.locator("div[role='textbox'], textarea, div[contenteditable='true']").first
                if await caption_input.count() > 0:
                    await caption_input.click()
                    await caption_input.fill(caption_text)
                    facebook_logger.info(f"[Facebook] Filled caption: {caption_text[:40]}...")

                # Handle schedule if specified
                if isinstance(self.publish_date, datetime):
                    facebook_logger.info(f"[Facebook] Configuring schedule time: {self.publish_date.strftime('%Y-%m-%d %H:%M')}")
                    schedule_radio = page.locator("text=Schedule, text=Lên lịch").first
                    if await schedule_radio.count() > 0:
                        await schedule_radio.click()
                        await asyncio.sleep(1)

                # Click Publish / Next buttons through the wizard
                publish_btn = page.get_by_role("button", name=re.compile(r"^(Publish|Post|Lên lịch|Chia sẻ|Tiếp|Next)$", re.I)).last
                if await publish_btn.count() > 0:
                    await publish_btn.click()
                    await asyncio.sleep(4)
                
                facebook_logger.success(f"[Facebook] Upload request submitted successfully: {self.title}")
                return True
            except Exception as e:
                facebook_logger.error(f"[Facebook] Error during upload: {e}")
                return False
            finally:
                await context.close()
                await browser.close()
