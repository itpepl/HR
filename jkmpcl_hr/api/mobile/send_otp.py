import frappe
import random
from frappe.utils import add_to_date, now
from jkmpcl_hr.api.mobile.sms_setting import *
from frappe.utils import now_datetime

@frappe.whitelist(allow_guest=True)
def send_reset_otp(email):

    if not email:
        return {
            "success": False,
            "message": "Email is required"
        }

    if not frappe.db.exists("User", email):
        return {
            "success": False,
            "message": "User not found"
        }

    # 🔥 STEP 1: Invalidate old unused OTPs
    frappe.db.sql("""
        UPDATE `tabPassword Reset OTP`
        SET is_used = 1
        WHERE email = %s
        AND is_used = 0
        AND expires_on >= NOW()
    """, email)

    # 🔥 STEP 2: Generate new OTP
    otp = random.randint(1000, 9999)

    # OTP expiry (10 minutes)
    expiry = add_to_date(now(), minutes=10)

    # 🔥 STEP 3: Save new OTP
    doc = frappe.new_doc("Password Reset OTP")
    doc.email = email
    doc.otp = str(otp)
    doc.expires_on = expiry
    doc.is_used = 0
    doc.insert(ignore_permissions=True)

    frappe.db.commit()

    # 🔥 STEP 4: Send email
    frappe.sendmail(
        recipients=[email],
        subject="Your OTP to Reset Password",
        message=f"""
        Hello,

        Your OTP for password reset is: <b>{otp}</b><br><br>
        This OTP will expire in 10 minutes.
        """,
        delayed=False
    )

    response = {
        "success": True,
        "message": f"OTP sent successfully to {email[:3]}****{email.split('@')[1]}"
    }

    # ✅ Return OTP only in developer mode
    if frappe.conf.get("developer_mode"):
        response["otp"] = str(otp)

    return response

@frappe.whitelist(allow_guest=True)
def verify_reset_otp(email, otp):

    record = frappe.get_all(
        "Password Reset OTP",
        filters={
            "email": email,
            "otp": otp,
            "is_used": 0
        },
        fields=["name", "expires_on"],
        order_by="creation desc",
        limit=1
    )

    if not record:
        return {
            "success": False,
            "message": "Invalid OTP"
        }

    otp_doc = frappe.get_doc("Password Reset OTP", record[0].name)

    # Check expiry
    if otp_doc.expires_on < now_datetime():
        return {
            "success": False,
            "message": "OTP has expired"
        }

    # Mark as used
    otp_doc.is_used = 1
    otp_doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "message": "OTP verified successfully. You can change password now."
    }