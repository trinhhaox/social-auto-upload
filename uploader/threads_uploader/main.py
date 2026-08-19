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
from utils.log import threads_logger


async def cookie_auth(account_file: str) -> bool:
    """Check whether Threads cookies are valid."""
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
            await page.goto("https://www.threads.net/", timeout=30000)
            await page.wait_for_load_state("domcontentloaded", timeout=15000)
            await asyncio.sleep(2)

            if "login" in page.url or await page.locator("text=Log in with Instagram").count() > 0:
                threads_logger.error("[Threads] Cookie expired or login required.")
                return False

            threads_logger.success("[Threads] Cookie is valid.")
            return True
        except Exception as e:
            threads_logger.error(f"[Threads] Auth check error: {e}")
            return False
        finally:
            await context.close()
            await browser.close()


async def get_threads_cookie(account_file: str):
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
        await page.goto("https://www.threads.net/login")
        threads_logger.info("[Threads] Please log in to Threads in the opened browser window.")
        
        await page.pause()
        await context.storage_state(path=account_file)
        threads_logger.success(f"[Threads] Cookie saved to {account_file}")
        await context.close()
        await browser.close()


async def threads_setup(account_file: str, handle: bool = False) -> bool:
    """Setup and verify Threads account cookies."""
    account_path = Path(account_file)
    if not account_path.is_absolute():
        account_file = str(Path(BASE_DIR) / "cookies" / account_file)
    
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            return False
        threads_logger.info(f"[Threads] Cookie file missing or expired. Opening login window...")
        await get_threads_cookie(account_file)
    return True


class ThreadsVideo(BaseVideoUploader):
    def __init__(
        self,
        title: str,
        file_path: str | Path,
        tags: list[str] | None = None,
        publish_date: datetime | int | None = 0,
        account_file: str = "threads_cookie.json",
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
        """Upload video post to Threads."""
        threads_logger.info(f"[Threads] Starting upload for media: {self.file_path.name}")
        
        if not await threads_setup(self.account_file, handle=True):
            threads_logger.error("[Threads] Authentication failed.")
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
                threads_logger.info("[Threads] Navigating to Threads home...")
                await page.goto("https://www.threads.net/", timeout=35000)
                await page.wait_for_load_state("domcontentloaded", timeout=15000)
                await asyncio.sleep(2)

                # Click Start a thread compose box or icon
                compose_trigger = page.locator("text=What's new?, text=Bắt đầu một thread..., svg[aria-label='Create'], svg[aria-label='Tạo']").first
                if await compose_trigger.count() > 0:
                    await compose_trigger.click()
                    await asyncio.sleep(1)

                # Attach media file
                file_input = page.locator("input[type='file']")
                if await file_input.count() > 0:
                    threads_logger.info("[Threads] Attaching video file...")
                    await file_input.first.set_input_files(str(self.file_path))
                    await asyncio.sleep(4)

                # Compose thread text
                post_text = self.description or self.title
                if self.tags:
                    hashtags_str = " " + " ".join([f"#{t.lstrip('#')}" for t in self.tags])
                    post_text += hashtags_str

                # Fill contenteditable textbox
                textbox = page.locator("div[contenteditable='true'], div[role='textbox']").first
                if await textbox.count() > 0:
                    await textbox.click()
                    await textbox.fill(post_text)
                    threads_logger.info(f"[Threads] Filled thread text: {post_text[:50]}...")

                await asyncio.sleep(4)

                # Click Post button
                post_btn = page.get_by_role("button", name=re.compile(r"^(Post|Đăng)$", re.I)).first
                if await post_btn.count() > 0:
                    await post_btn.click()
                    threads_logger.info("[Threads] Submitting post...")
                    await asyncio.sleep(6)

                threads_logger.success(f"[Threads] Post uploaded successfully: {self.title}")
                return True
            except Exception as e:
                threads_logger.error(f"[Threads] Error during upload: {e}")
                return False
            finally:
                await context.close()
                await browser.close()
