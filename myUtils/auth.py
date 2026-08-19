import asyncio
import configparser
import os

from playwright.async_api import async_playwright
from xhs import XhsClient

from conf import BASE_DIR, LOCAL_CHROME_HEADLESS
from utils.base_social_media import set_init_script
from utils.log import tencent_logger, kuaishou_logger, douyin_logger
from pathlib import Path
from uploader.xhs_uploader.main import sign_local


async def cookie_auth_douyin(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=LOCAL_CHROME_HEADLESS)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://creator.douyin.com/creator-micro/content/upload")
        try:
            await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload", timeout=5000)
            # 2024.06.17 抖音创作者中心改版
            # 判断
            # 等待“扫码登录”元素出现，超时 5 秒（如果 5 秒没出现，说明 cookie 有效）
            try:
                await page.get_by_text("扫码登录").wait_for(timeout=5000)
                douyin_logger.error("[+] cookie 失效，需要扫码登录")
                return False
            except:
                douyin_logger.success("[+]  cookie 有效")
                return True
        except:
            douyin_logger.error("[+] 等待5秒 cookie 失效")
            await context.close()
            await browser.close()
            return False


async def cookie_auth_tencent(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=LOCAL_CHROME_HEADLESS)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://channels.weixin.qq.com/platform/post/create")
        try:
            await page.wait_for_selector('div.title-name:has-text("微信小店")', timeout=5000)  # 等待5秒
            tencent_logger.error("[+] 等待5秒 cookie 失效")
            return False
        except:
            tencent_logger.success("[+] cookie 有效")
            return True


async def cookie_auth_ks(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=LOCAL_CHROME_HEADLESS)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://cp.kuaishou.com/article/publish/video")
        try:
            await page.wait_for_selector("div.names div.container div.name:text('机构服务')", timeout=5000)  # 等待5秒

            kuaishou_logger.info("[+] 等待5秒 cookie 失效")
            return False
        except:
            kuaishou_logger.success("[+] cookie 有效")
            return True


async def cookie_auth_xhs(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=LOCAL_CHROME_HEADLESS)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://creator.xiaohongshu.com/creator-micro/content/upload")
        try:
            await page.wait_for_url("https://creator.xiaohongshu.com/creator-micro/content/upload", timeout=5000)
        except:
            print("[+] 等待5秒 cookie 失效")
            await context.close()
            await browser.close()
            return False
        # 2024.06.17 抖音创作者中心改版
        if await page.get_by_text('手机号登录').count() or await page.get_by_text('扫码登录').count():
            print("[+] 等待5秒 cookie 失效")
            return False
        else:
            print("[+] cookie 有效")
            return True


from uploader.facebook_uploader.main import cookie_auth as cookie_auth_facebook
from uploader.instagram_uploader.main import cookie_auth as cookie_auth_instagram
from uploader.twitter_uploader.main import cookie_auth as cookie_auth_twitter
from uploader.threads_uploader.main import cookie_auth as cookie_auth_threads
from uploader.pinterest_uploader.main import cookie_auth as cookie_auth_pinterest
from uploader.zalo_uploader.main import cookie_auth as cookie_auth_zalo
from uploader.youtube_uploader.main import cookie_auth as cookie_auth_youtube
from uploader.tk_uploader.main import cookie_auth as cookie_auth_tiktok


async def check_cookie(type: int, file_path: str | Path) -> bool:
    target_path = Path(BASE_DIR / "cookiesFile" / file_path)
    if not target_path.exists():
        # Fallback to cookies/ folder
        fallback_path = Path(BASE_DIR / "cookies" / file_path)
        if fallback_path.exists():
            target_path = fallback_path
        else:
            return False

    str_path = str(target_path)
    try:
        match int(type):
            case 1:  # Xiaohongshu
                return await cookie_auth_xhs(target_path)
            case 2:  # WeChat Channels
                return await cookie_auth_tencent(target_path)
            case 3:  # Douyin
                return await cookie_auth_douyin(target_path)
            case 4:  # Kuaishou
                return await cookie_auth_ks(target_path)
            case 5:  # Facebook
                return await cookie_auth_facebook(str_path)
            case 6:  # Instagram
                return await cookie_auth_instagram(str_path)
            case 7:  # Twitter / X
                return await cookie_auth_twitter(str_path)
            case 8:  # Threads
                return await cookie_auth_threads(str_path)
            case 9:  # Pinterest
                return await cookie_auth_pinterest(str_path)
            case 10:  # Zalo
                return await cookie_auth_zalo(str_path)
            case 11:  # YouTube
                return await cookie_auth_youtube(str_path)
            case 12:  # TikTok
                return await cookie_auth_tiktok(str_path)
            case _:
                return False
    except Exception as e:
        print(f"[check_cookie error for type {type}]: {e}")
        return False

