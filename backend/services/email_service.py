import os
import aiosmtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "NutriSmart")

async def send_email(to_email: str, subject: str, html_content: str):
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("SMTP credentials not configured. Skipping email sending.")
        return

    message = EmailMessage()
    message["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(html_content, subtype="html")

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            start_tls=True,
            username=SMTP_USERNAME,
            password=SMTP_PASSWORD,
        )
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

async def send_signup_otp(email: str, name: str, otp: str):
    subject = "Verify Your NutriSmart Account"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #ff5722;">NutriSmart Verification</h2>
        <p>Hi {name},</p>
        <p>Your verification code is: <strong style="font-size: 24px; color: #333;">{otp}</strong></p>
        <p>This code will expire in 10 minutes. Please do not share this code with anyone.</p>
        <p>If you didn't request this, please ignore this email.</p>
    </div>
    """
    await send_email(email, subject, html_content)

async def send_password_reset_otp(email: str, otp: str):
    subject = "Reset Your NutriSmart Password"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #ff5722;">NutriSmart Password Reset</h2>
        <p>Hi there,</p>
        <p>You requested to reset your password. Here is your verification code:</p>
        <p><strong style="font-size: 24px; color: #333;">{otp}</strong></p>
        <p>This code will expire in 10 minutes. Please enter it in the app to reset your password.</p>
        <p>If you didn't request a password reset, you can safely ignore this email.</p>
    </div>
    """
    await send_email(email, subject, html_content)
