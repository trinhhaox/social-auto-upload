import asyncio
import json
import sqlite3

from patchright.async_api import async_playwright

from myUtils.auth import check_cookie
from utils.base_social_media import set_init_script
import uuid
from pathlib import Path
from conf import BASE_DIR, LOCAL_CHROME_HEADLESS, LOCAL_CHROME_PATH

# 统一获取浏览器启动配置（防风控+引入本地浏览器）
def get_browser_options():
    options = {
        'headless': LOCAL_CHROME_HEADLESS,
        'args': [
            '--disable-blink-features=AutomationControlled',  # 核心防爬屏蔽：去掉 window.navigator.webdriver 标签
            '--lang=zh-CN',
            '--disable-infobars',
            '--start-maximized'
        ]
    }
    # 如果用户在 conf.py 里配置了本地 Chrome，就用本地的，这样成功率极高
    if LOCAL_CHROME_PATH:
        options['executable_path'] = LOCAL_CHROME_PATH

    return options

# 抖音登录
async def douyin_cookie_gen(id,status_queue):
    url_changed_event = asyncio.Event()
    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()
    async with async_playwright() as playwright:
        options = get_browser_options()
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://creator.douyin.com/")
        original_url = page.url
        img_locator = page.get_by_role("img", name="二维码")
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        print("✅ 图片地址:", src)
        status_queue.put(src)
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)
        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            status_queue.put("500")
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(3, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                                INSERT INTO user_info (type, filePath, userName, status)
                                VALUES (?, ?, ?, ?)
                                ''', (3, f"{uuid_v1}.json", id, 1))
            conn.commit()
            print("✅ 用户状态已记录")
        status_queue.put("200")


# 视频号登录
async def get_tencent_cookie(id,status_queue):
    url_changed_event = asyncio.Event()
    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()

    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': LOCAL_CHROME_HEADLESS,  # Set headless option here
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        # Pause the page, and start recording manually.
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto("https://channels.weixin.qq.com")
        original_url = page.url

        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        # 等待 iframe 出现（最多等 60 秒）
        iframe_locator = page.frame_locator("iframe").first

        # 获取 iframe 中的第一个 img 元素
        img_locator = iframe_locator.get_by_role("img").first

        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        print("✅ 图片地址:", src)
        status_queue.put(src)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(2,f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                                INSERT INTO user_info (type, filePath, userName, status)
                                VALUES (?, ?, ?, ?)
                                ''', (2, f"{uuid_v1}.json", id, 1))
            conn.commit()
            print("✅ 用户状态已记录")
        status_queue.put("200")

# 快手登录
async def get_ks_cookie(id,status_queue):
    url_changed_event = asyncio.Event()
    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()
    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': LOCAL_CHROME_HEADLESS,  # Set headless option here
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://cp.kuaishou.com")

        # 定位并点击“立即登录”按钮（类型为 link）
        await page.get_by_role("link", name="立即登录").click()
        await page.get_by_text("扫码登录").click()
        img_locator = page.get_by_role("img", name="qrcode")
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        original_url = page.url
        print("✅ 图片地址:", src)
        status_queue.put(src)
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(4, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                                        INSERT INTO user_info (type, filePath, userName, status)
                                        VALUES (?, ?, ?, ?)
                                        ''', (4, f"{uuid_v1}.json", id, 1))
            conn.commit()
            print("✅ 用户状态已记录")
        status_queue.put("200")

# 小红书登录
async def xiaohongshu_cookie_gen(id,status_queue):
    url_changed_event = asyncio.Event()

    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()

    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': LOCAL_CHROME_HEADLESS,  # Set headless option here
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://creator.xiaohongshu.com/")
        await page.locator('img.css-wemwzq').click()

        img_locator = page.get_by_role("img").nth(2)
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        original_url = page.url
        print("✅ 图片地址:", src)
        status_queue.put(src)
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(1, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                           INSERT INTO user_info (type, filePath, userName, status)
                           VALUES (?, ?, ?, ?)
                           ''', (1, f"{uuid_v1}.json", id, 1))
            conn.commit()
            print("✅ 用户状态已记录")
        status_queue.put("200")


# Hàm đăng nhập tự động mở cửa sổ trình duyệt chung cho các nền tảng quốc tế và Zalo
async def browser_login_gen(platform_type: int, login_url: str, id: str, status_queue):
    print(f"🚀 Bắt đầu luồng đăng nhập trình duyệt cho platform type={platform_type}, account={id}")
    async with async_playwright() as playwright:
        user_data_dir = BASE_DIR / "browser_profiles" / f"profile_{platform_type}_{id}"
        user_data_dir.mkdir(parents=True, exist_ok=True)

        launch_args = [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-infobars',
            '--start-maximized',
            '--lang=vi-VN,en-US',
            '--disable-features=IsolateOrigins,site-per-process'
        ]

        options = {
            'headless': False,  # Luôn mở giao diện cửa sổ
            'args': launch_args,
            'ignore_default_args': ['--enable-automation'],  # QUAN TRỌNG: Loại bỏ cờ automation để Google không chặn
            'viewport': {'width': 1280, 'height': 800},
            'user_agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }

        if LOCAL_CHROME_PATH:
            options['executable_path'] = LOCAL_CHROME_PATH

        try:
            # Sử dụng persistent context để vượt qua hoàn toàn cơ chế bảo mật của Google và các mạng xã hội
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                **options
            )
            # Triệt tiêu triệt để dấu hiệu automation
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.chrome = {
                    runtime: {}
                };
            """)

            pages = context.pages
            page = pages[0] if pages else await context.new_page()

            await page.goto(login_url)
            print(f"🌐 Đã mở trang đăng nhập: {login_url}")

            # Đợi người dùng hoàn tất đăng nhập (hoặc tối đa 240s)
            for _ in range(80):
                await asyncio.sleep(3)
                if page.is_closed():
                    break
                cookies = await context.cookies()
                cookie_names = [c.get('name', '') for c in cookies]

                # Điều kiện phát hiện đăng nhập thành công theo từng nền tảng
                is_logged_in = False
                if platform_type == 11:  # YouTube
                    if ('SID' in cookie_names or 'SSID' in cookie_names or 'LOGIN_INFO' in cookie_names) and ('accounts.google.com' not in page.url or 'studio.youtube.com' in page.url):
                        is_logged_in = True
                elif platform_type == 5:  # Facebook
                    if 'c_user' in cookie_names or 'xs' in cookie_names:
                        is_logged_in = True
                elif platform_type == 6:  # Instagram
                    if 'sessionid' in cookie_names or 'ds_user_id' in cookie_names:
                        is_logged_in = True
                elif platform_type == 12:  # TikTok
                    if 'sessionid' in cookie_names or 'sessionid_ss' in cookie_names:
                        is_logged_in = True
                elif platform_type == 7:  # Twitter / X
                    if 'auth_token' in cookie_names or 'ct0' in cookie_names:
                        is_logged_in = True
                elif len(cookies) >= 5 and ('login' not in page.url.lower() and 'signin' not in page.url.lower()):
                    is_logged_in = True

                if is_logged_in:
                    print(f"✅ Đã phát hiện phiên đăng nhập thành công cho platform {platform_type}!")
                    await asyncio.sleep(2)  # Đợi cookie ghi hoàn chỉnh
                    break

            uuid_v1 = uuid.uuid1()
            cookies_dir = Path(BASE_DIR / "cookiesFile")
            cookies_dir.mkdir(parents=True, exist_ok=True)
            cookie_file = cookies_dir / f"{uuid_v1}.json"
            
            try:
                await context.storage_state(path=str(cookie_file))
            except Exception as se:
                print(f"[storage_state fallback]: {se}")
                cookies = await context.cookies()
                with open(cookie_file, 'w', encoding='utf-8') as f:
                    json.dump({"cookies": cookies, "origins": []}, f, ensure_ascii=False, indent=2)

            # Lưu vào database
            with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO user_info (type, filePath, userName, status)
                VALUES (?, ?, ?, ?)
                ''', (int(platform_type), f"{uuid_v1}.json", id, 1))
                conn.commit()
                print(f"✅ Đã lưu tài khoản {id} vào cơ sở dữ liệu")

            await context.close()
            status_queue.put("200")
        except Exception as e:
            print(f"❌ Lỗi đăng nhập platform {platform_type}: {e}")
            status_queue.put("500")


async def get_facebook_cookie(id, status_queue):
    await browser_login_gen(5, "https://www.facebook.com/login", id, status_queue)

async def get_instagram_cookie(id, status_queue):
    await browser_login_gen(6, "https://www.instagram.com/accounts/login/", id, status_queue)

async def get_twitter_cookie(id, status_queue):
    await browser_login_gen(7, "https://x.com/i/flow/login", id, status_queue)

async def get_threads_cookie(id, status_queue):
    await browser_login_gen(8, "https://www.threads.net/login", id, status_queue)

async def get_pinterest_cookie(id, status_queue):
    await browser_login_gen(9, "https://www.pinterest.com/login/", id, status_queue)

async def get_zalo_cookie(id, status_queue):
    await browser_login_gen(10, "https://id.zalo.me/account?continue=https%3A%2F%2Foa.zalo.me%2Fmanage%2Fcontent%2Fvideo", id, status_queue)

async def get_youtube_cookie(id, status_queue):
    print(f"🚀 Bắt đầu luồng đăng nhập YouTube Studio (Patchright Chrome) cho account={id}")
    async with async_playwright() as playwright:
        try:
            # Sử dụng Patchright với channel="chrome" để loại bỏ 100% cờ bot detection của Google
            browser = await playwright.chromium.launch(
                headless=False,
                channel="chrome",
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-infobars',
                    '--start-maximized',
                    '--lang=vi-VN,en-US'
                ]
            )
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            )
            context = await set_init_script(context)
            page = await context.new_page()

            # Mở studio.youtube.com để Google kích hoạt flow đăng nhập tự nhiên
            await page.goto("https://studio.youtube.com", wait_until="domcontentloaded")
            print(f"🔐 Đã mở YouTube Studio, vui lòng đăng nhập tài khoản Google...")

            ok = False
            for _ in range(300):
                await asyncio.sleep(2)
                if page.is_closed():
                    break
                if "/channel/" in page.url or ("studio.youtube.com" in page.url and "signin" not in page.url.lower() and "rejected" not in page.url.lower()):
                    await asyncio.sleep(3)
                    ok = True
                    break

            if ok:
                uuid_v1 = uuid.uuid1()
                cookies_dir = Path(BASE_DIR / "cookiesFile")
                cookies_dir.mkdir(parents=True, exist_ok=True)
                cookie_file = cookies_dir / f"{uuid_v1}.json"
                try:
                    await context.storage_state(path=str(cookie_file))
                except Exception as se:
                    print(f"[YouTube storage_state fallback]: {se}")
                    cookies = await context.cookies()
                    with open(cookie_file, 'w', encoding='utf-8') as f:
                        json.dump({"cookies": cookies, "origins": []}, f, ensure_ascii=False, indent=2)

                with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                    INSERT INTO user_info (type, filePath, userName, status)
                    VALUES (?, ?, ?, ?)
                    ''', (11, f"{uuid_v1}.json", id, 1))
                    conn.commit()
                    print(f"✅ Đã lưu tài khoản YouTube {id} vào cơ sở dữ liệu")

                await browser.close()
                status_queue.put("200")
            else:
                await browser.close()
                status_queue.put("500")
        except Exception as e:
            print(f"❌ Lỗi đăng nhập YouTube: {e}")
            status_queue.put("500")

async def get_tiktok_cookie(id, status_queue):
    await browser_login_gen(12, "https://www.tiktok.com/login?lang=en", id, status_queue)



