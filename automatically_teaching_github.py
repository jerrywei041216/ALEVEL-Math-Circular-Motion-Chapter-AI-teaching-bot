import imaplib
import email
import base64
import subprocess
from email.header import decode_header
from openai import OpenAI


# ========== 配置区域（你需要改这里） ==========

IMAP_SERVER = "imap.gmail.com"   # 你的邮箱 IMAP 服务器
EMAIL_ADDRESS = "Your_email_address"
EMAIL_PASSWORD = "Your_email_IMAP"

OPENAI_API_KEY = "Your_OpenAI_Key # 
OPENAI_MODEL = "gpt-5.1"                   # 我们要用的模型

# 是否从本地图片测试（True = 用本地图片，不连邮箱）
USE_LOCAL_IMAGE = False
LOCAL_IMAGE_PATH = "question.png"          # 本地图片路径（当 USE_LOCAL_IMAGE=True 时生效）


# ========== 初始化 OpenAI 客户端 ==========

client = OpenAI(api_key=OPENAI_API_KEY)


# ========== 工具函数：从邮箱或本地获取图片 ==========

def fetch_latest_question_image_from_email():
    """
    从邮箱中获取最新一封由特定发件人发送的邮件，并提取图片附件。
    返回: (image_bytes, image_name)
    """
    print("[INFO] 正在连接 IMAP 服务器...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)

    # 登录邮箱
    try:
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    except Exception as e:
        raise RuntimeError(f"登入 IMAP 失败: {e}")

    # 选中收件箱
    status, _ = mail.select("INBOX")
    if status != "OK":
        mail.logout()
        raise RuntimeError("无法选中 INBOX")

    # ========= 你要筛选的发件人 =========
    SENDER_FILTER = "sender_email_address"
    # =================================

    print(f"[INFO] 搜索发件人为 {SENDER_FILTER} 的邮件...")
    status, data = mail.search(None, f'(FROM "{SENDER_FILTER}")')

    if status != "OK":
        mail.close()
        mail.logout()
        raise RuntimeError("IMAP 搜索邮件失败")

    msg_ids = data[0].split()

    if not msg_ids:
        mail.close()
        mail.logout()
        raise RuntimeError(f"未找到来自 {SENDER_FILTER} 的邮件")

    latest_id = msg_ids[-1]
    print(f"[INFO] 找到最新邮件 ID: {latest_id.decode()}")

    # 获取邮件内容
    status, msg_data = mail.fetch(latest_id, "(RFC822)")
    if status != "OK":
        mail.close()
        mail.logout()
        raise RuntimeError("邮件内容获取失败")

    raw_email = msg_data[0][1]
    msg = email.message_from_bytes(raw_email)

    image_bytes = None
    image_name = None

    # 遍历所有 MIME 部分找图片
    for part in msg.walk():
        content_disposition = str(part.get("Content-Disposition") or "")
        content_type = part.get_content_type()

        if "attachment" in content_disposition and content_type in [
            "image/jpeg",
            "image/png",
            "image/jpg",
        ]:
            image_bytes = part.get_payload(decode=True)
            image_name = part.get_filename()
            break

    mail.close()
    mail.logout()

    if image_bytes is None:
        raise RuntimeError("找到邮件但没有可用的图片附件，请确认图片是 JPG 或 PNG")

    if not image_name:
        image_name = "question.png"

    print(f"[INFO] 已成功读取图片附件: {image_name}")
    return image_bytes, image_name


def load_image_from_local(path: str):
    """
    从本地文件读取图片。用于测试，不通过邮箱。
    """
    print(f"[INFO] 正在从本地读取图片: {path}")
    with open(path, "rb") as f:
        image_bytes = f.read()
    return image_bytes, path


# ========== 核心：用 gpt-5.1 读图 + 生成讲解稿和 Manim 代码 ==========

def generate_solution_from_image(image_bytes: bytes) -> str:
    """
    调用 gpt-5.1：
    - 看题目截图
    - 写详细讲解稿（SCRIPT_TEXT）
    - 生成可运行的 Manim 代码（MANIM_CODE）
    输出统一放在一个字符串里，用标题分块。
    """
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    image_url = f"data:image/png;base64,{b64_image}"

    prompt = """
你是一名 A-level 数学/物理老师，同时也是 Manim 专家。

现有一张试题的截图。请你完成两件事情，并严格按指定格式输出：

1️⃣ SCRIPT_TEXT（详细讲解稿）
- 面向学生，尽量详细、分步骤讲解这道题。
- 每一步说明“做了什么、为什么这么做、用了什么物理/数学原理”。
- 可以包含“常见错误提醒”“思路总结”。
- 建议结构：
  Step 1: ...
  Step 2: ...
  Step 3: ...
  最终答案: ...

2️⃣ MANIM_CODE（可直接运行的 Manim 代码）
- 使用 Manim Community 版本语法。
- 必须以:  from manim import *  开头。
- 定义场景类名:  SolutionScene(Scene)
- 在 construct 中：
  - 左侧绘制必要的示意图（例如几何、受力图、曲线等）。
  - 右侧使用 Text / MathTex 以 Step 1, Step 2, Step 3... 的形式展示关键推导公式。
- 代码要尽量简洁清晰，但能够正常渲染讲解过程。
- 代码必须是一个完整的 Python 脚本，可以直接用命令：
    manim -pqm solution_scene.py SolutionScene
  渲染成功。
- 请不要在代码外面包裹 ```python 或 ``` 之类的标记。

- 使用 ArcBetweenPoints(start, end) 时：
  - start 和 end 必须是点坐标（例如 dot.get_center()）。
  - 通常不要显式指定 radius 参数，让 Manim 使用默认半径即可。
  - 如果一定要指定 radius，必须保证 radius 不小于两点间距离的一半。

- 每一个step过渡期间至少wait 5秒，为学生理解答案保留时间
⚠️ 非常重要：输出格式必须严格如下（包含这些标题）：

### SCRIPT_TEXT
(在这里输出完整的文字讲解稿)

### MANIM_CODE
(在这里输出可直接运行的 Manim Python 代码)
"""

    print("[INFO] 正在调用 gpt-5.1 解析图片并生成讲解 + 代码...")
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
    )

    full_text = resp.choices[0].message.content
    return full_text


def split_outputs(full_text: str):
    """
    将模型输出按 ### SCRIPT_TEXT / ### MANIM_CODE 切成两部分。
    返回: (script_text, code_text)
    """
    if "### SCRIPT_TEXT" not in full_text or "### MANIM_CODE" not in full_text:
        raise RuntimeError("模型输出格式不符合预期，缺少 ### SCRIPT_TEXT 或 ### MANIM_CODE 标记")

    script_part = full_text.split("### SCRIPT_TEXT", 1)[1].split("### MANIM_CODE", 1)[0].strip()
    code_part = full_text.split("### MANIM_CODE", 1)[1].strip()

    return script_part, code_part


# ========== 总控：生成讲解稿 + Manim 文件 + 渲染视频 ==========

def build_video_and_script():
    # 1. 获取图片
    if USE_LOCAL_IMAGE:
        image_bytes, image_name = load_image_from_local(LOCAL_IMAGE_PATH)
    else:
        image_bytes, image_name = fetch_latest_question_image_from_email()

    # 2. 调 gpt-5.1 得到讲解 + 代码
    full_output = generate_solution_from_image(image_bytes)
    script_text, code_text = split_outputs(full_output)

    # 3. 写讲解稿
    with open("solution_script.txt", "w", encoding="utf-8") as f:
        f.write(script_text)
    print("[INFO] 已生成详细讲解稿: solution_script.txt")

    # 4. 写 Manim 代码
    with open("solution_scene.py", "w", encoding="utf-8") as f:
        f.write(code_text)
    print("[INFO] 已生成 Manim 代码文件: solution_scene.py")

    # 5. 调用 Manim 渲染视频
    print("[INFO] 正在调用 manim 渲染视频，请稍候...")
    subprocess.run(
        ["manim", "-pqm", "solution_scene.py", "SolutionScene"],
        check=True
    )
    print("[INFO] 视频渲染完成！请查看弹出的播放器窗口或 media/videos 目录。")


if __name__ == "__main__":
    build_video_and_script()
