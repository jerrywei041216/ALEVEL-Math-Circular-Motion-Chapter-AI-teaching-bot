import time
import imaplib
import email
from email.header import decode_header
import subprocess

# ========== 配置区域 ==========
IMAP_SERVER = "imap.gmail.com"
EMAIL_ACCOUNT = "receiver_email_address"    
EMAIL_PASSWORD = "receiver_email_address_IMAP"       
TARGET_SENDER = "sender_email_adress"
TARGET_SUBJECT = "specific_subject"

CHECK_INTERVAL = 15  # 每 15 秒检查一次邮件
GENERATE_SCRIPT_CMD = ["python3", "automatically_teaching_github.py"]  
# ↑ 这里写你的视频生成脚本文件名
# =============================


def decode_subject(raw_subject):
    """解码各种编码格式的邮件标题"""
    subject, encoding = decode_header(raw_subject)[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding or "utf-8", errors="ignore")
    return subject


def check_new_teaching_email(latest_uid_seen):
    """
    检查是否有新的邮件：
    来自 TARGET_SENDER 且 Subject = TARGET_SUBJECT。
    如果有，返回最新邮件 UID；否则返回 None。
    """
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    mail.select("INBOX")

    status, data = mail.search(None, "ALL")
    mail_ids = data[0].split()
    mail.logout()

    if not mail_ids:
        return None

    newest_uid = mail_ids[-1]  # 最新邮件 UID

    # 如果最新邮件 UID 和上次一样 → 没新邮件
    if newest_uid == latest_uid_seen:
        return None

    # 检查邮件内容
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    mail.select("INBOX")

    status, msg_data = mail.fetch(newest_uid, "(RFC822)")
    mail.logout()

    raw_email = msg_data[0][1]
    msg = email.message_from_bytes(raw_email)

    sender = msg["From"]
    subject = decode_subject(msg["Subject"])

    print(f"[DEBUG] 最新邮件 From: {sender}, Subject: {subject}")

    # 条件：特定发件人 + 特定主题
    if TARGET_SENDER in sender and subject.strip() == TARGET_SUBJECT:
        print("[INFO] 检测到来自指定发件人的教学邮件！")
        return newest_uid

    return None


def main():
    print("[INFO] 启动 Gmail 邮件监听程序…")
    print(f"监听条件：From={TARGET_SENDER}, Subject={TARGET_SUBJECT}")
    print("每次检查间隔：", CHECK_INTERVAL, "秒\n")

    latest_uid_seen = None

    while True:
        try:
            new_uid = check_new_teaching_email(latest_uid_seen)

            if new_uid:
                print("[INFO] 准备启动教学生成程序 automatically_teaching.py ...")

                subprocess.run(GENERATE_SCRIPT_CMD)
                print("[INFO] 教学视频生成完成。\n")

                latest_uid_seen = new_uid  # 记录最新邮件 UID

            else:
                print("[INFO] 暂无新教学邮件。")

        except Exception as e:
            print("[ERROR] 发生错误：", e)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
