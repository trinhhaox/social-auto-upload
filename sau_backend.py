import asyncio
import os
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from queue import Queue
from flask_cors import CORS
from myUtils.auth import check_cookie
from flask import Flask, request, jsonify, Response, render_template, send_from_directory
from werkzeug.utils import secure_filename
from conf import BASE_DIR
from myUtils.login import (
    get_tencent_cookie,
    douyin_cookie_gen,
    get_ks_cookie,
    xiaohongshu_cookie_gen,
    get_facebook_cookie,
    get_instagram_cookie,
    get_twitter_cookie,
    get_threads_cookie,
    get_pinterest_cookie,
    get_zalo_cookie,
    get_youtube_cookie,
    get_tiktok_cookie,
)
from myUtils.postVideo import (
    post_video_tencent,
    post_video_DouYin,
    post_video_ks,
    post_video_xhs,
    post_video_facebook,
    post_video_instagram,
    post_video_twitter,
    post_video_threads,
    post_video_pinterest,
    post_video_zalo,
    post_video_youtube,
    post_video_tiktok,
)

active_queues = {}
app = Flask(__name__)

# Cho phép tất cả các nguồn truy cập CORS
CORS(app)

def init_db():
    try:
        db_path = Path(BASE_DIR / "db" / "database.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        Path(BASE_DIR / "videoFile").mkdir(parents=True, exist_ok=True)
        Path(BASE_DIR / "cookiesFile").mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type INTEGER NOT NULL,
                filePath TEXT NOT NULL,
                userName TEXT NOT NULL,
                status INTEGER DEFAULT 0
            )''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                filesize REAL,
                upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                file_path TEXT
            )''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS publish_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                platform_type INTEGER,
                platform_name TEXT,
                account_count INTEGER,
                file_count INTEGER,
                status TEXT DEFAULT 'Success',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            conn.commit()
            print("✅ Cơ sở dữ liệu SQLite đã sẵn sàng")
    except Exception as e:
        print(f"[init_db error]: {e}")

init_db()



# 限制上传文件大小为160MB
app.config['MAX_CONTENT_LENGTH'] = 160 * 1024 * 1024

# 获取当前目录（假设 index.html 和 assets 在这里）
current_dir = os.path.dirname(os.path.abspath(__file__))

# 处理所有静态资源请求（未来打包用）
@app.route('/assets/<filename>')
def custom_static(filename):
    return send_from_directory(os.path.join(current_dir, 'assets'), filename)

# 处理 favicon.ico 静态资源（未来打包用）
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_dir, 'assets'), 'vite.svg')

@app.route('/vite.svg')
def vite_svg():
    return send_from_directory(os.path.join(current_dir, 'assets'), 'vite.svg')

# （未来打包用）
@app.route('/')
def index():  # put application's code here
    return send_from_directory(current_dir, 'index.html')

import re

def sanitize_filename(filename: str) -> str:
    p = Path(filename)
    stem = p.stem
    ext = p.suffix if p.suffix else ".mp4"
    # Lọc các ký tự cấm trên hệ điều hành nhưng giữ nguyên ký tự Unicode (tiếng Việt, tiếng Anh)
    clean_stem = re.sub(r'[\/\\:*?"<>|]', '_', stem).strip()
    if not clean_stem:
        clean_stem = f"video_{uuid.uuid4().hex[:8]}"
    return f"{clean_stem}{ext}"

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "Không tìm thấy tệp trong yêu cầu"
        }), 400
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "Chưa chọn tệp để tải lên"
        }), 400
    try:
        uuid_v1 = uuid.uuid1()
        original_name = file.filename
        safe_name = sanitize_filename(original_name)
        final_filename = f"{uuid_v1}_{safe_name}"

        video_dir = Path(BASE_DIR / "videoFile")
        video_dir.mkdir(parents=True, exist_ok=True)
        filepath = video_dir / final_filename

        file.save(str(filepath))
        filesize_mb = round(float(os.path.getsize(filepath)) / (1024 * 1024), 2)

        # Tự động ghi vào file_records để hiển thị trong Thư viện tư liệu
        try:
            with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO file_records (filename, filesize, file_path)
                VALUES (?, ?, ?)
                ''', (original_name, filesize_mb, final_filename))
                conn.commit()
        except Exception as dbe:
            print(f"[Record file error]: {dbe}")

        return jsonify({
            "code": 200,
            "msg": "Tải tệp lên thành công",
            "data": final_filename
        }), 200
    except Exception as e:
        print(f"Lỗi khi tải file: {str(e)}")
        return jsonify({"code": 500, "msg": f"Tải lên thất bại: {str(e)}", "data": None}), 500

@app.route('/getFile', methods=['GET'])
def get_file():
    filename = request.args.get('filename')
    if not filename:
        return jsonify({"code": 400, "msg": "Thiếu tham số tên tệp", "data": None}), 400

    if '..' in filename or filename.startswith('/'):
        return jsonify({"code": 400, "msg": "Tên tệp không hợp lệ", "data": None}), 400

    file_dir = str(Path(BASE_DIR / "videoFile"))
    return send_from_directory(file_dir, filename)


@app.route('/uploadSave', methods=['POST'])
def upload_save():
    if 'file' not in request.files:
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "Không tìm thấy tệp trong yêu cầu"
        }), 400

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "Chưa chọn tệp"
        }), 400

    custom_filename = request.form.get('filename', None)
    if custom_filename:
        filename = sanitize_filename(custom_filename + Path(file.filename).suffix)
    else:
        filename = sanitize_filename(file.filename)

    try:
        uuid_v1 = uuid.uuid1()
        final_filename = f"{uuid_v1}_{filename}"
        video_dir = Path(BASE_DIR / "videoFile")
        video_dir.mkdir(parents=True, exist_ok=True)
        filepath = video_dir / final_filename

        file.save(str(filepath))
        filesize_mb = round(float(os.path.getsize(filepath)) / (1024 * 1024), 2)

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO file_records (filename, filesize, file_path)
            VALUES (?, ?, ?)
            ''', (filename, filesize_mb, final_filename))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "Tải tệp và lưu thành công",
            "data": {
                "filename": filename,
                "filepath": final_filename
            }
        }), 200

    except Exception as e:
        print(f"Lỗi tải file lên: {e}")
        return jsonify({
            "code": 500,
            "msg": f"Tải lên thất bại: {e}",
            "data": None
        }), 500


@app.route('/getFiles', methods=['GET'])
def get_all_files():
    try:
        # 使用 with 自动管理数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row  # 允许通过列名访问结果
            cursor = conn.cursor()

            # 查询所有记录
            cursor.execute("SELECT * FROM file_records")
            rows = cursor.fetchall()

            # 将结果转为字典列表，并提取UUID
            data = []
            for row in rows:
                row_dict = dict(row)
                # 从 file_path 中提取 UUID (文件名的第一部分，下划线前)
                if row_dict.get('file_path'):
                    file_path_parts = row_dict['file_path'].split('_', 1)  # 只分割第一个下划线
                    if len(file_path_parts) > 0:
                        row_dict['uuid'] = file_path_parts[0]  # UUID 部分
                    else:
                        row_dict['uuid'] = ''
                else:
                    row_dict['uuid'] = ''
                data.append(row_dict)

            return jsonify({
                "code": 200,
                "msg": "success",
                "data": data
            }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("get file failed!"),
            "data": None
        }), 500


@app.route("/getAccounts", methods=['GET'])
def getAccounts():
    """快速获取所有账号信息，不进行cookie验证"""
    try:
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
            SELECT * FROM user_info''')
            rows = cursor.fetchall()
            rows_list = [list(row) for row in rows]

            print("\n📋 当前数据表内容（快速获取）：")
            for row in rows:
                print(row)

            return jsonify(
                {
                    "code": 200,
                    "msg": None,
                    "data": rows_list
                }), 200
    except Exception as e:
        print(f"获取账号列表时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"获取账号列表失败: {str(e)}",
            "data": None
        }), 500


@app.route("/getValidAccounts",methods=['GET'])
async def getValidAccounts():
    with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT * FROM user_info''')
        rows = cursor.fetchall()
        rows_list = [list(row) for row in rows]
        print("\n📋 当前数据表内容：")
        for row in rows:
            print(row)
        for row in rows_list:
            flag = await check_cookie(row[1],row[2])
            if not flag:
                row[4] = 0
                cursor.execute('''
                UPDATE user_info 
                SET status = ? 
                WHERE id = ?
                ''', (0,row[0]))
                conn.commit()
                print("✅ 用户状态已更新")
        for row in rows:
            print(row)
        return jsonify(
                        {
                            "code": 200,
                            "msg": None,
                            "data": rows_list
                        }),200

@app.route('/deleteFile', methods=['GET'])
def delete_file():
    file_id = request.args.get('id')

    if not file_id or not file_id.isdigit():
        return jsonify({
            "code": 400,
            "msg": "Invalid or missing file ID",
            "data": None
        }), 400

    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询要删除的记录
            cursor.execute("SELECT * FROM file_records WHERE id = ?", (file_id,))
            record = cursor.fetchone()

            if not record:
                return jsonify({
                    "code": 404,
                    "msg": "File not found",
                    "data": None
                }), 404

            record = dict(record)

            # 获取文件路径并删除实际文件
            file_path = Path(BASE_DIR / "videoFile" / record['file_path'])
            if file_path.exists():
                try:
                    file_path.unlink()  # 删除文件
                    print(f"✅ 实际文件已删除: {file_path}")
                except Exception as e:
                    print(f"⚠️ 删除实际文件失败: {e}")
                    # 即使删除文件失败，也要继续删除数据库记录，避免数据不一致
            else:
                print(f"⚠️ 实际文件不存在: {file_path}")

            # 删除数据库记录
            cursor.execute("DELETE FROM file_records WHERE id = ?", (file_id,))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "File deleted successfully",
            "data": {
                "id": record['id'],
                "filename": record['filename']
            }
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("delete failed!"),
            "data": None
        }), 500

@app.route('/deleteAccount', methods=['GET'])
def delete_account():
    account_id = request.args.get('id')

    if not account_id or not account_id.isdigit():
        return jsonify({
            "code": 400,
            "msg": "Invalid or missing account ID",
            "data": None
        }), 400

    account_id = int(account_id)

    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询要删除的记录
            cursor.execute("SELECT * FROM user_info WHERE id = ?", (account_id,))
            record = cursor.fetchone()

            if not record:
                return jsonify({
                    "code": 404,
                    "msg": "account not found",
                    "data": None
                }), 404

            record = dict(record)

            # 删除关联的cookie文件
            if record.get('filePath'):
                cookie_file_path = Path(BASE_DIR / "cookiesFile" / record['filePath'])
                if cookie_file_path.exists():
                    try:
                        cookie_file_path.unlink()
                        print(f"✅ Cookie文件已删除: {cookie_file_path}")
                    except Exception as e:
                        print(f"⚠️ 删除Cookie文件失败: {e}")

            # 删除数据库记录
            cursor.execute("DELETE FROM user_info WHERE id = ?", (account_id,))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "account deleted successfully",
            "data": None
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"delete failed: {str(e)}",
            "data": None
        }), 500


# SSE 登录接口
@app.route('/login')
def login():
    # 1 小红书 2 视频号 3 抖音 4 快手
    type = request.args.get('type')
    # 账号名
    id = request.args.get('id')

    # 模拟一个用于异步通信的队列
    status_queue = Queue()
    active_queues[id] = status_queue

    def on_close():
        print(f"清理队列: {id}")
        del active_queues[id]
    # 启动异步任务线程
    thread = threading.Thread(target=run_async_function, args=(type,id,status_queue), daemon=True)
    thread.start()
    response = Response(sse_stream(status_queue,), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'  # 关键：禁用 Nginx 缓冲
    response.headers['Content-Type'] = 'text/event-stream'
    response.headers['Connection'] = 'keep-alive'
    return response

@app.route('/postVideo', methods=['POST'])
def postVideo():
    # 获取JSON数据
    data = request.get_json()

    if not data:
        return jsonify({"code": 400, "msg": "请求数据不能为空", "data": None}), 400

    # 从JSON数据中提取fileList和accountList
    file_list = data.get('fileList', [])
    account_list = data.get('accountList', [])
    type = data.get('type')
    title = data.get('title')
    tags = data.get('tags')
    category = data.get('category')
    enableTimer = data.get('enableTimer')
    if category == 0:
        category = None
    productLink = data.get('productLink', '')
    productTitle = data.get('productTitle', '')
    thumbnail_path = data.get('thumbnail', '')
    is_draft = data.get('isDraft', False)  # 新增参数：是否保存为草稿

    videos_per_day = data.get('videosPerDay')
    daily_times = data.get('dailyTimes')
    start_days = data.get('startDays')

    link = data.get('link', '')
    board = data.get('board', '')
    is_reel = data.get('isReel', True)
    playlist = data.get('playlist', '')
    visibility = data.get('visibility', 'public')

    # Parameters validation
    post_type = data.get('postType', 'video') # 'text', 'image', 'video'
    if post_type != 'text' and not file_list:
        return jsonify({"code": 400, "msg": "Danh sách tệp không được để trống khi đăng kèm ảnh/video", "data": None}), 400
    if not account_list:
        return jsonify({"code": 400, "msg": "Danh sách tài khoản không được để trống", "data": None}), 400
    if not type:
        return jsonify({"code": 400, "msg": "Loại nền tảng không được để trống", "data": None}), 400
    if not title:
        return jsonify({"code": 400, "msg": "Tiêu đề không được để trống", "data": None}), 400

    platform_names = {
        1: "Xiaohongshu",
        2: "WeChat Channels",
        3: "Douyin",
        4: "Kuaishou",
        5: "Facebook",
        6: "Instagram",
        7: "Twitter / X",
        8: "Threads",
        9: "Pinterest",
        10: "Zalo",
        11: "YouTube",
        12: "TikTok",
    }

    try:
        platform_type = int(type)
        match platform_type:
            case 1:
                post_video_xhs(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times, start_days)
            case 2:
                post_video_tencent(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times, start_days, is_draft)
            case 3:
                post_video_DouYin(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times, start_days, thumbnail_path, productLink, productTitle)
            case 4:
                post_video_ks(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times, start_days)
            case 5:
                post_video_facebook(title, file_list, tags, account_list, enableTimer, videos_per_day, daily_times, start_days, is_reel)
            case 6:
                post_video_instagram(title, file_list, tags, account_list, enableTimer, videos_per_day, daily_times, start_days)
            case 7:
                post_video_twitter(title, file_list, tags, account_list, enableTimer, videos_per_day, daily_times, start_days)
            case 8:
                post_video_threads(title, file_list, tags, account_list, enableTimer, videos_per_day, daily_times, start_days)
            case 9:
                post_video_pinterest(title, file_list, tags, account_list, enableTimer, videos_per_day, daily_times, start_days, link, board)
            case 10:
                post_video_zalo(title, file_list, tags, account_list, enableTimer, videos_per_day, daily_times, start_days, category or "")
            case 11:
                post_video_youtube(title, file_list, tags, account_list, enableTimer, videos_per_day, daily_times, start_days, thumbnail_path, playlist, visibility)
            case 12:
                post_video_tiktok(title, file_list, tags, account_list, enableTimer, videos_per_day, daily_times, start_days)
            case _:
                return jsonify({"code": 400, "msg": f"Không hỗ trợ loại nền tảng: {type}", "data": None}), 400

        # Save to publish history
        try:
            with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO publish_history (title, platform_type, platform_name, account_count, file_count, status)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (f"[{post_type.upper()}] {title}", platform_type, platform_names.get(platform_type, "Unknown"), len(account_list), len(file_list), 'Success'))
                conn.commit()
        except Exception as db_err:
            print(f"[Record publish history error]: {db_err}")

        return jsonify({
            "code": 200,
            "msg": f"Nhiệm vụ đăng bài ({post_type}) đã được gửi thành công",
            "data": None
        }), 200
    except Exception as e:
        print(f"Lỗi khi đăng bài: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"Đăng bài thất bại: {str(e)}",
            "data": None
        }), 500


@app.route('/getPublishHistory', methods=['GET'])
def get_publish_history():
    """Lấy danh sách lịch sử đăng bài gần đây"""
    try:
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM publish_history ORDER BY id DESC LIMIT 50")
            rows = cursor.fetchall()
            return jsonify({
                "code": 200,
                "msg": "success",
                "data": [dict(r) for r in rows]
            }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"Lấy lịch sử thất bại: {e}",
            "data": []
        }), 500



@app.route('/updateUserinfo', methods=['POST'])
def updateUserinfo():
    # 获取JSON数据
    data = request.get_json()

    # 从JSON数据中提取 type 和 userName
    user_id = data.get('id')
    type = data.get('type')
    userName = data.get('userName')
    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 更新数据库记录
            cursor.execute('''
                           UPDATE user_info
                           SET type     = ?,
                               userName = ?
                           WHERE id = ?;
                           ''', (type, userName, user_id))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "account update successfully",
            "data": None
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("update failed!"),
            "data": None
        }), 500

@app.route('/postVideoBatch', methods=['POST'])
def postVideoBatch():
    data_list = request.get_json()

    if not isinstance(data_list, list):
        return jsonify({"code": 400, "msg": "Expected a JSON array", "data": None}), 400
    for data in data_list:
        # 从JSON数据中提取fileList和accountList
        file_list = data.get('fileList', [])
        account_list = data.get('accountList', [])
        type = data.get('type')
        title = data.get('title')
        tags = data.get('tags')
        category = data.get('category')
        enableTimer = data.get('enableTimer')
        if category == 0:
            category = None
        productLink = data.get('productLink', '')
        productTitle = data.get('productTitle', '')
        is_draft = data.get('isDraft', False)

        videos_per_day = data.get('videosPerDay')
        daily_times = data.get('dailyTimes')
        start_days = data.get('startDays')
        # 打印获取到的数据（仅作为示例）
        print("File List:", file_list)
        print("Account List:", account_list)
        match type:
            case 1:
                post_video_xhs(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times, start_days)
            case 2:
                post_video_tencent(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times, start_days, is_draft)
            case 3:
                post_video_DouYin(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times, start_days, productLink, productTitle)
            case 4:
                post_video_ks(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times, start_days)
            case 5:
                post_video_facebook(title, file_list, tags, account_list, enableTimer, videos_per_day, daily_times, start_days)
            case 6:
                post_video_instagram(title, file_list, tags, account_list, enableTimer, videos_per_day, daily_times, start_days)
            case 7:
                post_video_twitter(title, file_list, tags, account_list, enableTimer, videos_per_day, daily_times, start_days)
            case 8:
                post_video_threads(title, file_list, tags, account_list, enableTimer, videos_per_day, daily_times, start_days)
            case 9:
                post_video_pinterest(title, file_list, tags, account_list, enableTimer, videos_per_day, daily_times, start_days)
            case 10:
                post_video_zalo(title, file_list, tags, account_list, enableTimer, videos_per_day, daily_times, start_days)
            case 11:
                post_video_youtube(title, file_list, tags, account_list, enableTimer, videos_per_day, daily_times, start_days)
            case 12:
                post_video_tiktok(title, file_list, tags, account_list, enableTimer, videos_per_day, daily_times, start_days)

    return jsonify({
        "code": 200,
        "msg": "Nhiệm vụ đăng bài hàng loạt đã hoàn tất",
        "data": None
    }), 200

# Cookie文件上传API
@app.route('/uploadCookie', methods=['POST'])
def upload_cookie():
    try:
        if 'file' not in request.files:
            return jsonify({
                "code": 400,
                "msg": "没有找到Cookie文件",
                "data": None
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "code": 400,
                "msg": "Cookie文件名不能为空",
                "data": None
            }), 400

        if not file.filename.endswith('.json'):
            return jsonify({
                "code": 400,
                "msg": "Cookie文件必须是JSON格式",
                "data": None
            }), 400

        # 获取账号信息
        account_id = request.form.get('id')
        platform = request.form.get('platform')

        if not account_id or not platform:
            return jsonify({
                "code": 400,
                "msg": "缺少账号ID或平台信息",
                "data": None
            }), 400

        # 从数据库获取账号的文件路径
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT filePath FROM user_info WHERE id = ?', (account_id,))
            result = cursor.fetchone()

        if not result:
            return jsonify({
                "code": 500,
                "msg": "账号不存在",
                "data": None
            }), 404

        # 保存上传的Cookie文件到对应路径
        cookie_file_path = Path(BASE_DIR / "cookiesFile" / result['filePath'])
        cookie_file_path.parent.mkdir(parents=True, exist_ok=True)

        file.save(str(cookie_file_path))

        # 更新数据库中的账号信息（可选，比如更新更新时间）
        # 这里可以根据需要添加额外的处理逻辑

        return jsonify({
            "code": 200,
            "msg": "Cookie文件上传成功",
            "data": None
        }), 200

    except Exception as e:
        print(f"上传Cookie文件时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"上传Cookie文件失败: {str(e)}",
            "data": None
        }), 500


# Cookie文件下载API
@app.route('/downloadCookie', methods=['GET'])
def download_cookie():
    try:
        file_path = request.args.get('filePath')
        if not file_path:
            return jsonify({
                "code": 500,
                "msg": "缺少文件路径参数",
                "data": None
            }), 400

        # 验证文件路径的安全性，防止路径遍历攻击
        cookie_file_path = Path(BASE_DIR / "cookiesFile" / file_path).resolve()
        base_path = Path(BASE_DIR / "cookiesFile").resolve()

        if not cookie_file_path.is_relative_to(base_path):
            return jsonify({
                "code": 500,
                "msg": "非法文件路径",
                "data": None
            }), 400

        if not cookie_file_path.exists():
            return jsonify({
                "code": 500,
                "msg": "Cookie文件不存在",
                "data": None
            }), 404

        # 返回文件
        return send_from_directory(
            directory=str(cookie_file_path.parent),
            path=cookie_file_path.name,
            as_attachment=True
        )

    except Exception as e:
        print(f"下载Cookie文件时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"下载Cookie文件失败: {str(e)}",
            "data": None
        }), 500


@app.route('/addAccountManual', methods=['POST'])
def add_account_manual():
    data = request.get_json()
    if not data:
        return jsonify({"code": 400, "msg": "Dữ liệu không được để trống", "data": None}), 400

    account_name = data.get('name')
    platform_type = data.get('type')
    if not account_name or not platform_type:
        return jsonify({"code": 400, "msg": "Thiếu tên tài khoản hoặc loại nền tảng", "data": None}), 400

    try:
        uuid_v1 = uuid.uuid1()
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(parents=True, exist_ok=True)
        file_path = f"{uuid_v1}.json"

        # Tạo file cookie rỗng hoặc lưu file nếu có
        cookie_file = cookies_dir / file_path
        if not cookie_file.exists():
            cookie_file.write_text("{}", encoding="utf-8")

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO user_info (type, filePath, userName, status)
            VALUES (?, ?, ?, ?)
            ''', (int(platform_type), file_path, account_name, 0))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "Thêm tài khoản thành công",
            "data": {
                "filePath": file_path,
                "name": account_name,
                "type": platform_type
            }
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"Thêm tài khoản thất bại: {e}",
            "data": None
        }), 500


# 包装函数：在线程中运行异步函数
def run_async_function(type, id, status_queue):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        match str(type):
            case '1':
                loop.run_until_complete(xiaohongshu_cookie_gen(id, status_queue))
            case '2':
                loop.run_until_complete(get_tencent_cookie(id, status_queue))
            case '3':
                loop.run_until_complete(douyin_cookie_gen(id, status_queue))
            case '4':
                loop.run_until_complete(get_ks_cookie(id, status_queue))
            case '5':
                loop.run_until_complete(get_facebook_cookie(id, status_queue))
            case '6':
                loop.run_until_complete(get_instagram_cookie(id, status_queue))
            case '7':
                loop.run_until_complete(get_twitter_cookie(id, status_queue))
            case '8':
                loop.run_until_complete(get_threads_cookie(id, status_queue))
            case '9':
                loop.run_until_complete(get_pinterest_cookie(id, status_queue))
            case '10':
                loop.run_until_complete(get_zalo_cookie(id, status_queue))
            case '11':
                loop.run_until_complete(get_youtube_cookie(id, status_queue))
            case '12':
                loop.run_until_complete(get_tiktok_cookie(id, status_queue))
            case _:
                status_queue.put("500")
    except Exception as e:
        print(f"[run_async_function error]: {e}")
        status_queue.put("500")
    finally:
        loop.close()

# SSE 流生成器函数
def sse_stream(status_queue):
    while True:
        if not status_queue.empty():
            msg = status_queue.get()
            yield f"data: {msg}\n\n"
        else:
            # 避免 CPU 占满
            time.sleep(0.1)

if __name__ == '__main__':
    app.run(host='0.0.0.0' ,port=5409)

