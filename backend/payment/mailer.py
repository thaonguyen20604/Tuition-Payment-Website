import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart  # <- thêm dòng này
import config

def send_otp_email(to_email: str, otp_code: str):
    # Plain text fallback
    body = f"Mã OTP thanh toán của bạn: {otp_code}\nHiệu lực trong 5 phút."

    # HTML version
    html = f"""\
<!doctype html>
<html lang="vi">
  <body style="margin:0;padding:0;background:#f6f7f9;font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#111;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f6f7f9;padding:24px 0;">
      <tr>
        <td align="center">
          <table role="presentation" width="560" cellspacing="0" cellpadding="0" style="background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e9ecf1;">
            <tr>
              <td style="padding:24px 28px;">
                <h2 style="margin:0 0 12px 0;font-size:20px;">OTP xác nhận thanh toán</h2>
                <p style="margin:0 0 16px 0;line-height:1.6;">Mã OTP thanh toán của bạn:</p>
                <div style="display:inline-block;padding:12px 20px;border-radius:10px;background:#111;color:#fff;font-weight:700;font-size:24px;letter-spacing:4px;">
                  {otp_code}
                </div>
                <p style="margin:16px 0 0 0;color:#555;line-height:1.6;">Mã có hiệu lực trong <strong>5 phút</strong>. Không chia sẻ mã này cho bất kỳ ai.</p>
              </td>
            </tr>
          </table>
          <p style="color:#8a94a6;font-size:12px;margin:12px 0 0 0;">Email tự động – vui lòng không trả lời.</p>
        </td>
      </tr>
    </table>
  </body>
</html>
"""

    # multipart/alternative
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "OTP xác nhận thanh toán"
    msg["From"] = config.MAIL_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    # Dev mode
    if not config.SMTP_USER or not config.SMTP_PASS:
        print(f"[MAILER:DEV] To: {to_email} | OTP: {otp_code}")
        print("[MAILER:DEV][HTML PREVIEW]")
        print(html)
        return

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASS)
        server.send_message(msg)


def send_payment_success_email(to_email: str, payment_info: dict):
    """
    Gửi email xác nhận thanh toán thành công kèm thông tin hóa đơn
    """
    # Plain text fallback
    body = f"""
Xác nhận thanh toán thành công!

Chi tiết hóa đơn:
------------------------
Mã đơn hàng: {payment_info['order_id']}
Số tiền: {payment_info['amount']:,.0f} VND
Thời gian: {payment_info['payment_date']}
Nội dung: {payment_info['description']}

Cảm ơn quý khách đã sử dụng dịch vụ.
""".strip()

    # HTML version
    html = f"""\
<!doctype html>
<html lang="vi">
  <body style="margin:0;padding:0;background:#f6f7f9;font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#111;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f6f7f9;padding:24px 0;">
      <tr>
        <td align="center">
          <table role="presentation" width="560" cellspacing="0" cellpadding="0" style="background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e9ecf1;">
            <tr>
              <td style="padding:24px 28px;">
                <h2 style="margin:0 0 8px 0;">Thanh toán thành công</h2>
                <p style="margin:0 0 16px 0;color:#2e7d32;font-weight:600;">Cảm ơn bạn đã sử dụng dịch vụ.</p>
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:separate;border-spacing:0 8px;">
                  <tr>
                    <td style="width:180px;color:#555;">Mã đơn hàng</td>
                    <td style="font-weight:600;">{payment_info['order_id']}</td>
                  </tr>
                  <tr>
                    <td style="color:#555;">Số tiền</td>
                    <td style="font-weight:700;">{payment_info['amount']:,.0f} VND</td>
                  </tr>
                  <tr>
                    <td style="color:#555;">Thời gian</td>
                    <td>{payment_info['payment_date']}</td>
                  </tr>
                  <tr>
                    <td style="color:#555;">Nội dung</td>
                    <td>{payment_info['description']}</td>
                  </tr>
                </table>
                <div style="margin-top:16px;padding:12px;border-radius:10px;background:#f1f5f9;color:#334155;">
                  Đây là email xác nhận tự động. Vui lòng lưu lại để đối chiếu khi cần.
                </div>
              </td>
            </tr>
          </table>
          <p style="color:#8a94a6;font-size:12px;margin:12px 0 0 0;">Email tự động – vui lòng không trả lời.</p>
        </td>
      </tr>
    </table>
  </body>
</html>
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Xác nhận thanh toán thành công - Đơn hàng #{payment_info['order_id']}"
    msg["From"] = config.MAIL_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    if not config.SMTP_USER or not config.SMTP_PASS:
        print(f"[MAILER:DEV] Payment success email to: {to_email}")
        print(body)
        print("[MAILER:DEV][HTML PREVIEW]")
        print(html)
        return

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASS)
        server.send_message(msg)



def send_payer_receipt_email(to_email: str, payment_info: dict):
    """
    Gửi email biên nhận cho người thanh toán kèm chi tiết giao dịch
    """
    # Plain text fallback
    body = f"""
Thanh toán thành công!

Chi tiết giao dịch:
------------------------
Mã giao dịch: {payment_info['order_id']}
Số tiền đã thanh toán: {payment_info['amount']:,.0f} VND
Thời gian: {payment_info['payment_date']}
Người thanh toán: {payment_info.get('payer_user', 'Không có thông tin')}
Thanh toán học phí cho: {payment_info.get('student_user', 'Không có thông tin')}


Nội dung: {payment_info['description']}

Email này là biên nhận điện tử cho giao dịch của bạn.
Vui lòng lưu giữ để đối chiếu khi cần thiết.

Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi.
""".strip()

    # HTML version
    html = f"""\
<!doctype html>
<html lang="vi">
  <body style="margin:0;padding:0;background:#f6f7f9;font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#111;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f6f7f9;padding:24px 0;">
      <tr>
        <td align="center">
          <table role="presentation" width="560" cellspacing="0" cellpadding="0" style="background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e9ecf1;">
            <tr>
              <td style="padding:24px 28px;">
                <h2 style="margin:0 0 8px 0;">Biên nhận thanh toán</h2>
                <p style="margin:0 0 16px 0;color:#475569;">Đây là biên nhận điện tử cho giao dịch của bạn.</p>
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:separate;border-spacing:0 8px;">
                  <tr>
                    <td style="width:200px;color:#555;">Mã giao dịch</td>
                    <td style="font-weight:600;">{payment_info['order_id']}</td>
                  </tr>
                  <tr>
                    <td style="color:#555;">Số tiền đã thanh toán</td>
                    <td style="font-weight:700;">{payment_info['amount']:,.0f} VND</td>
                  </tr>
                  <tr>
                    <td style="color:#555;">Thời gian</td>
                    <td>{payment_info['payment_date']}</td>
                  </tr>
                  <tr>
                    <td style="color:#555;">Người thanh toán</td>
                    <td>{payment_info.get('payer_user', 'Không có thông tin')}</td>
                  </tr>
                  <tr>
                    <td style="color:#555;">Người được thanh toán</td>
                    <td>{payment_info.get('student_user', 'Không có thông tin')}</td>
                  </tr>

                  <tr>
                    <td style="color:#555;">Nội dung</td>
                    <td>{payment_info['description']}</td>
                  </tr>
                </table>
                <div style="margin-top:16px;padding:12px;border-radius:10px;background:#f1f5f9;color:#334155;">
                  Vui lòng lưu email này để đối chiếu khi cần thiết.
                </div>
              </td>
            </tr>
          </table>
          <p style="color:#8a94a6;font-size:12px;margin:12px 0 0 0;">Email tự động – vui lòng không trả lời.</p>
        </td>
      </tr>
    </table>
  </body>
</html>
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Biên nhận thanh toán - Giao dịch #{payment_info['order_id']}"
    msg["From"] = config.MAIL_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    if not config.SMTP_USER or not config.SMTP_PASS:
        print(f"[MAILER:DEV] Payer receipt email to: {to_email}")
        print(body)
        print("[MAILER:DEV][HTML PREVIEW]")
        print(html)
        return

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASS)
        server.send_message(msg)

