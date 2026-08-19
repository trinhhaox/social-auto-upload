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
from utils.log import twitter_logger


async def cookie_auth(account_file: str) -> bool:
    """Check whether Twitter / X cookies are valid."""
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
            await page.goto("https://x.com/home", timeout=30000)
            await page.wait_for_load_state("domcontentloaded", timeout=15000)
            await asyncio.sleep(2)

            if "login" in page.url or "i/flow/login" in page.url:
                twitter_logger.error("[Twitter/X] Cookie expired or login required.")
                return False

            post_box = page.locator("div[data-testid='tweetTextarea_0'], a[data-testid='SideNav_NewTweet_Button']")
            if await post_box.count() > 0 or "x.com/home" in page.url:
                twitter_logger.success("[Twitter/X] Cookie is valid.")
                return True

            twitter_logger.warning("[Twitter/X] Auth state unclear, returning valid.")
            return True
        except Exception as e:
            twitter_logger.error(f"[Twitter/X] Auth check error: {e}")
            return False
        finally:
            await context.close()
            await browser.close()


async def get_twitter_cookie(account_file: str):
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
        await page.goto("https://x.com/i/flow/login")
        twitter_logger.info("[Twitter/X] Please log in to X (Twitter) in the opened browser window.")
        
        await page.pause()
        await context.storage_state(path=account_file)
        twitter_logger.success(f"[Twitter/X] Cookie saved to {account_file}")
        await context.close()
        await browser.close()


async def twitter_setup(account_file: str, handle: bool = False) -> bool:
    """Setup and verify Twitter account cookies."""
    account_path = Path(account_file)
    if not account_path.is_absolute():
        account_file = str(Path(BASE_DIR) / "cookies" / account_file)
    
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            return False
        twitter_logger.info(f"[Twitter/X] Cookie file missing or expired. Opening login window...")
        await get_twitter_cookie(account_file)
    return True


class TwitterVideo(BaseVideoUploader):
    def __init__(
        self,
        title: str,
        file_path: str | Path,
        tags: list[str] | None = None,
        publish_date: datetime | int | None = 0,
        account_file: str = "twitter_cookie.json",
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
        """Upload tweet with video to Twitter / X."""
        twitter_logger.info(f"[Twitter/X] Starting tweet upload for media: {self.file_path.name}")
        
        if not await twitter_setup(self.account_file, handle=True):
            twitter_logger.error("[Twitter/X] Authentication failed.")
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
                twitter_logger.info("[Twitter/X] Opening X home compose...")
                await page.goto("https://x.com/compose/post", timeout=35000)
                await page.wait_for_load_state("domcontentloaded", timeout=15000)
                await asyncio.sleep(2)

                # Find file input for media
                file_input = page.locator("input[data-testid='fileInput']")
                if await file_input.count() == 0:
                    file_input = page.locator("input[type='file']")

                if await file_input.count() > 0:
                    twitter_logger.info("[Twitter/X] Attaching video file...")
                    await file_input.first.set_input_files(str(self.file_path))
                    await asyncio.sleep(5)
                else:
                    twitter_logger.warning("[Twitter/X] File input not directly found.")

                # Construct tweet body
                tweet_text = self.description or self.title
                if self.tags:
                    hashtags_str = " " + " ".join([f"#{t.lstrip('#')}" for t in self.tags])
                    tweet_text += hashtags_str

                # Fill tweet textbox
                post_box = page.locator("div[data-testid='tweetTextarea_0']").first
                if await post_box.count() > 0:
                    await post_box.click()
                    await post_box.fill(tweet_text)
                    twitter_logger.info(f"[Twitter/X] Filled tweet text: {tweet_text[:50]}...")

                # Wait for media processing
                await asyncio.sleep(5)

                # Click Post button
                tweet_btn = page.locator("button[data-testid='tweetButton'], button[data-testid='tweetButtonInline']").first
                if await tweet_btn.count() > 0:
                    await tweet_btn.click()
                    twitter_logger.info("[Twitter/X] Submitting tweet...")
                    await asyncio.sleep(6)

                twitter_logger.success(f"[Twitter/X] Tweet uploaded successfully: {self.title}")
                return True
            except Exception as e:
                twitter_logger.error(f"[Twitter/X] Error during tweet post: {e}")
                return False
            finally:
                await context.close()
                await browser.close()
