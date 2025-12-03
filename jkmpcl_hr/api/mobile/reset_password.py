import frappe

@frappe.whitelist(allow_guest=True)
def reset_password_with_otp(email, new_password, confirm_password):

    if new_password != confirm_password:
        return {
            "success": False,
            "message": "Passwords do not match"
        }

    if not frappe.db.exists("User", email):
        return {
            "success": False,
            "message": "User not found"
        }

    otp_exists = frappe.db.exists(
        "Password Reset OTP",
        {
            "email": email,
            "is_used": 1
        }
    )

    if not otp_exists:
        return {
            "success": False,
            "message": "OTP not verified. Please verify OTP first."
        }

    try:
        # 4️⃣ Set new password
        user = frappe.get_doc("User", email)
        user.new_password = new_password
        user.save(ignore_permissions=True)

        # 5️⃣ Invalidate all OTPs after reset
        frappe.db.sql("""
            UPDATE `tabPassword Reset OTP`
            SET is_used = 1
            WHERE email = %s
        """, email)

        frappe.db.commit()

        return {
            "success": True,
            "message": "Password reset successful. You can login now."
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Reset Password Error")
        return {
            "success": False,
            "message": "Something went wrong while resetting password",
            "error": str(e)
        }
