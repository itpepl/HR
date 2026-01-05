import frappe
from frappe.utils import getdate, nowdate

@frappe.whitelist()
def get_leave_balance(employeeId, as_on_date=None):
    try:
        if not employeeId:
            frappe.throw("Employee is required")

        as_on_date = getdate(as_on_date or nowdate())
        data = []

        leave_types = frappe.get_all("Leave Type", pluck="name")

        for lt in leave_types:

            earned = frappe.db.sql("""
                SELECT SUM(leaves)
                FROM `tabLeave Ledger Entry`
                WHERE employee = %s
                AND leave_type = %s
                AND leaves > 0
                AND from_date <= %s
                AND to_date >= %s
            """, (employeeId, lt, as_on_date, as_on_date))[0][0] or 0

            used = frappe.db.sql("""
                SELECT ABS(SUM(leaves))
                FROM `tabLeave Ledger Entry`
                WHERE employee = %s
                AND leave_type = %s
                AND leaves < 0
            """, (employeeId, lt))[0][0] or 0

            remaining = earned - used

            data.append({
                "leave_type": lt,
                "allocated": round(earned, 2),
                "used": round(used, 2),
                "remaining": round(remaining, 2)
            })

    except Exception as e:
        frappe.log_error("Leave Balance Error", frappe.get_traceback())
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success": False,
            "message": str(e),
            "data": None
        }

    else:
        frappe.local.response["message"] = {
            "success": True,
            "message": "Leave balance fetched successfully",
            "data": {
                "employee": employeeId,
                "as_on_date": str(as_on_date),
                "leave_balance": data
            }
        }
