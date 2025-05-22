import smtplib
import ssl
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from validate_email import validate_email

def send_summary_email(msg_txt, to_addrs=None, from_addr="kmeek@targetednews.com", subject="Bill Load Summary"):
    smtp_server = "mail2.targetednews.com"
    port = 587
    sender_email = "kmeek@targetednews.com"
    password = "jsfL6Hqa"

    if to_addrs is None:
        to_addrs = ["kmeek@targetednews.com", "bmalota08@gmail.com"]
    elif isinstance(to_addrs, str):
        to_addrs = [to_addrs]

    # Validate all email addresses
    for email in to_addrs:
        if not validate_email(email):
            logging.error(f"Invalid email address: {email}")
            return

    context = ssl.create_default_context()
    try:
        server = smtplib.SMTP(smtp_server, port)
        server.starttls(context=context)
        server.login(sender_email, password)

        msg = MIMEMultipart("alternative")
        msg["From"] = from_addr
        msg["To"] = ", ".join(to_addrs)
        msg["Subject"] = subject
        msg.attach(MIMEText(msg_txt, "plain"))

        server.sendmail(from_addr, to_addrs, msg.as_string())
    except Exception as e:
        logging.error(f"Failed to send summary email: {e}")
    finally:
        server.quit()
