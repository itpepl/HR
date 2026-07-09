import frappe


@frappe.whitelist(methods=["POST"])
def save_fcm_token(employee, fcm_token):
    if not employee:
        frappe.throw("Employee is required")

    if not fcm_token:
        frappe.throw("FCM Token is required")

    if not frappe.db.exists("Employee", employee):
        frappe.throw(f"Employee {employee} not found")

    frappe.db.set_value(
        "Employee",
        employee,
        "custom_fcm_token",
        fcm_token,
        update_modified=False
    )

    frappe.db.commit()

    return {
        "success": True,
        "message": "FCM token saved successfully."
    }