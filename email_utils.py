import smtplib
import ssl
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from validate_email import validate_email

def send_summary_email(msg_txt, to_addr="kmeek@targetednews.com", from_addr="kmeek@targetednews.com", subject="Bill Load Summary"):
    smtp_server = "mail2.targetednews.com"
    port = 587
    sender_email = "kmeek@targetednews.com"
    password = "jsfL6Hqa"

    if not validate_email(to_addr):
        logging.error(f"Invalid email address: {to_addr}")
        return

    context = ssl.create_default_context()
    try:
        server = smtplib.SMTP(smtp_server, port)
        server.starttls(context=context)
        server.login(sender_email, password)

        msg = MIMEMultipart("alternative")
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.attach(MIMEText(msg_txt, "plain"))

        server.sendmail(from_addr, [to_addr], msg.as_string())
    except Exception as e:
        logging.error(f"Failed to send summary email: {e}")
    finally:
        server.quit()
