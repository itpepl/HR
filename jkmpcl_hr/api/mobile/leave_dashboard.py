import frappe

@frappe.whitelist()
def get_leave_balance(employeeId):
    try:
        if not employeeId:
            frappe.throw("Employee is required")

        data = []

        leave_types = frappe.get_all(
            "Leave Type",
            pluck="name"
        )

        for lt in leave_types:
            ledger = frappe.db.sql("""
                SELECT SUM(leaves) AS balance
                FROM `tabLeave Ledger Entry`
                WHERE employee = %s
                AND leave_type = %s
            """, (employeeId, lt), as_dict=True)

            balance = ledger[0].balance or 0

            allocated = frappe.db.sql("""
                SELECT SUM(total_leaves_allocated)
                FROM `tabLeave Allocation`
                WHERE employee = %s
                AND leave_type = %s
                AND docstatus = 1
            """, (employeeId, lt))[0][0] or 0

            used = allocated - balance

            data.append({
                "leave_type": lt,
                "allocated": allocated,
                "used": used,
                "remaining": balance
            })

    except Exception as e:
        # ❌ ERROR RESPONSE
        frappe.log_error("Error While Getting Leave Balance", str(e))
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success": False,
            "message": f"Error while fetching leave balance: {str(e)}",
            "data": None
        }

    else:
        # ✅ SUCCESS RESPONSE
        frappe.local.response["message"] = {
            "success": True,
            "message": "Leave balance fetched successfully",
            "data": {
                "employee": employeeId,
                "leave_balance": data
            }
        }
