import asyncio
from pathlib import Path

from conf import BASE_DIR
from uploader.douyin_uploader.main import DouYinVideo
from uploader.ks_uploader.main import KSVideo
from uploader.tencent_uploader.main import TencentVideo
from uploader.xiaohongshu_uploader.main import XiaoHongShuVideo
from utils.constant import TencentZoneTypes
from utils.files_times import generate_schedule_time_next_day


def post_video_tencent(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0, is_draft=False):
    # 生成文件的完整路径
    account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
    files = [Path(BASE_DIR / "videoFile" / file) for file in files]
    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(len(files), videos_per_day, daily_times,start_days)
    else:
        publish_datetimes = [0 for i in range(len(files))]
    for index, file in enumerate(files):
        for cookie in account_file:
            print(f"文件路径{str(file)}")
            # 打印视频文件名、标题和 hashtag
            print(f"视频文件名：{file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")
            app = TencentVideo(title, str(file), tags, publish_datetimes[index], cookie, category, is_draft)
            asyncio.run(app.main(), debug=False)


def post_video_DouYin(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0,
                      thumbnail_path = '',
                      productLink = '', productTitle = ''):
    # 生成文件的完整路径
    account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
    files = [Path(BASE_DIR / "videoFile" / file) for file in files]
    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(len(files), videos_per_day, daily_times,start_days)
    else:
        publish_datetimes = [0 for i in range(len(files))]
    for index, file in enumerate(files):
        for cookie in account_file:
            print(f"文件路径{str(file)}")
            # 打印视频文件名、标题和 hashtag
            print(f"视频文件名：{file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")
            app = DouYinVideo(title, str(file), tags, publish_datetimes[index], cookie, thumbnail_path, productLink, productTitle)
            asyncio.run(app.douyin_upload_video(), debug=False)


def post_video_ks(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0):
    # 生成文件的完整路径
    account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
    files = [Path(BASE_DIR / "videoFile" / file) for file in files]
    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(len(files), videos_per_day, daily_times,start_days)
    else:
        publish_datetimes = [0 for i in range(len(files))]
    for index, file in enumerate(files):
        for cookie in account_file:
            print(f"文件路径{str(file)}")
            # 打印视频文件名、标题和 hashtag
            print(f"视频文件名：{file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")
            app = KSVideo(title, str(file), tags, publish_datetimes[index], cookie)
            asyncio.run(app.main(), debug=False)

def post_video_xhs(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0):
    # 生成文件的完整路径
    account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
    files = [Path(BASE_DIR / "videoFile" / file) for file in files]
    file_num = len(files)
    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(file_num, videos_per_day, daily_times,start_days)
    else:
        publish_datetimes = 0
    for index, file in enumerate(files):
        for cookie in account_file:
            # 打印视频文件名、标题和 hashtag
            print(f"视频文件名：{file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")
from uploader.facebook_uploader.main import FacebookVideo
from uploader.instagram_uploader.main import InstagramVideo
from uploader.twitter_uploader.main import TwitterVideo
from uploader.threads_uploader.main import ThreadsVideo
from uploader.pinterest_uploader.main import PinterestVideo
from uploader.zalo_uploader.main import ZaloVideo
from uploader.youtube_uploader.main import YouTubeVideo
from uploader.tk_uploader.main import TiktokVideo


def _resolve_paths(files, account_files):
    acc_paths = []
    for acc in account_files:
        p1 = Path(BASE_DIR / "cookiesFile" / acc)
        p2 = Path(BASE_DIR / "cookies" / acc)
        acc_paths.append(p1 if p1.exists() else p2)

    video_paths = []
    for f in files:
        p1 = Path(BASE_DIR / "videoFile" / f)
        p2 = Path(BASE_DIR / "videos" / f)
        video_paths.append(p1 if p1.exists() else p2)

    return video_paths, acc_paths


def post_video_facebook(title, files, tags, account_file, enableTimer=False, videos_per_day=1, daily_times=None, start_days=0, is_reel=True):
    video_paths, acc_paths = _resolve_paths(files, account_file)
    publish_datetimes = generate_schedule_time_next_day(len(video_paths), videos_per_day, daily_times, start_days) if enableTimer else [0] * len(video_paths)
    for index, file in enumerate(video_paths):
        for cookie in acc_paths:
            app = FacebookVideo(title, str(file), tags, publish_datetimes[index], str(cookie), is_reel=is_reel)
            asyncio.run(app.upload())


def post_video_instagram(title, files, tags, account_file, enableTimer=False, videos_per_day=1, daily_times=None, start_days=0):
    video_paths, acc_paths = _resolve_paths(files, account_file)
    publish_datetimes = generate_schedule_time_next_day(len(video_paths), videos_per_day, daily_times, start_days) if enableTimer else [0] * len(video_paths)
    for index, file in enumerate(video_paths):
        for cookie in acc_paths:
            app = InstagramVideo(title, str(file), tags, publish_datetimes[index], str(cookie))
            asyncio.run(app.upload())


def post_video_twitter(title, files, tags, account_file, enableTimer=False, videos_per_day=1, daily_times=None, start_days=0):
    video_paths, acc_paths = _resolve_paths(files, account_file)
    publish_datetimes = generate_schedule_time_next_day(len(video_paths), videos_per_day, daily_times, start_days) if enableTimer else [0] * len(video_paths)
    for index, file in enumerate(video_paths):
        for cookie in acc_paths:
            app = TwitterVideo(title, str(file), tags, publish_datetimes[index], str(cookie))
            asyncio.run(app.upload())


def post_video_threads(title, files, tags, account_file, enableTimer=False, videos_per_day=1, daily_times=None, start_days=0):
    video_paths, acc_paths = _resolve_paths(files, account_file)
    publish_datetimes = generate_schedule_time_next_day(len(video_paths), videos_per_day, daily_times, start_days) if enableTimer else [0] * len(video_paths)
    for index, file in enumerate(video_paths):
        for cookie in acc_paths:
            app = ThreadsVideo(title, str(file), tags, publish_datetimes[index], str(cookie))
            asyncio.run(app.upload())


def post_video_pinterest(title, files, tags, account_file, enableTimer=False, videos_per_day=1, daily_times=None, start_days=0, link="", board=""):
    video_paths, acc_paths = _resolve_paths(files, account_file)
    publish_datetimes = generate_schedule_time_next_day(len(video_paths), videos_per_day, daily_times, start_days) if enableTimer else [0] * len(video_paths)
    for index, file in enumerate(video_paths):
        for cookie in acc_paths:
            app = PinterestVideo(title, str(file), tags, publish_datetimes[index], str(cookie), link=link, board=board)
            asyncio.run(app.upload())


def post_video_zalo(title, files, tags, account_file, enableTimer=False, videos_per_day=1, daily_times=None, start_days=0, category=""):
    video_paths, acc_paths = _resolve_paths(files, account_file)
    publish_datetimes = generate_schedule_time_next_day(len(video_paths), videos_per_day, daily_times, start_days) if enableTimer else [0] * len(video_paths)
    for index, file in enumerate(video_paths):
        for cookie in acc_paths:
            app = ZaloVideo(title, str(file), tags, publish_datetimes[index], str(cookie), category=category)
            asyncio.run(app.upload())


def post_video_youtube(title, files, tags, account_file, enableTimer=False, videos_per_day=1, daily_times=None, start_days=0, thumbnail_path=None, playlist=None, visibility="public"):
    video_paths, acc_paths = _resolve_paths(files, account_file)
    for index, file in enumerate(video_paths):
        for cookie in acc_paths:
            app = YouTubeVideo(title, str(file), tags, str(cookie), thumbnail_path=thumbnail_path, playlist=playlist, visibility=visibility)
            asyncio.run(app.main())


def post_video_tiktok(title, files, tags, account_file, enableTimer=False, videos_per_day=1, daily_times=None, start_days=0):
    video_paths, acc_paths = _resolve_paths(files, account_file)
    publish_datetimes = generate_schedule_time_next_day(len(video_paths), videos_per_day, daily_times, start_days) if enableTimer else [0] * len(video_paths)
    for index, file in enumerate(video_paths):
        for cookie in acc_paths:
            app = TiktokVideo(title, str(file), tags, publish_datetimes[index], str(cookie))
            asyncio.run(app.main())