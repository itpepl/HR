import frappe
from frappe.utils import getdate, nowdate

# @frappe.whitelist()
# def get_leave_balance(employeeId, as_on_date=None):
#     try:
#         if not employeeId:
#             frappe.throw("Employee is required")

#         as_on_date = getdate(as_on_date or nowdate())
#         data = []

#         leave_types = frappe.get_all("Leave Type", pluck="name")

#         for lt in leave_types:

#             earned = frappe.db.sql("""
#                 SELECT SUM(leaves)
#                 FROM `tabLeave Ledger Entry`
#                 WHERE employee = %s
#                 AND leave_type = %s
#                 AND leaves > 0
#                 AND from_date <= %s
#                 AND to_date >= %s
#             """, (employeeId, lt, as_on_date, as_on_date))[0][0] or 0

#             used = frappe.db.sql("""
#                 SELECT ABS(SUM(leaves))
#                 FROM `tabLeave Ledger Entry`
#                 WHERE employee = %s
#                 AND leave_type = %s
#                 AND leaves < 0
#             """, (employeeId, lt))[0][0] or 0

#             remaining = earned - used

#             data.append({
#                 "leave_type": lt,
#                 "allocated": round(earned, 2),
#                 "used": round(used, 2),
#                 "remaining": round(remaining, 2)
#             })

#     except Exception as e:
#         frappe.log_error("Leave Balance Error", frappe.get_traceback())
#         frappe.clear_messages()
#         frappe.local.response["message"] = {
#             "success": False,
#             "message": str(e),
#             "data": None
#         }

#     else:
#         frappe.local.response["message"] = {
#             "success": True,
#             "message": "Leave balance fetched successfully",
#             "data": {
#                 "employee": employeeId,
#                 "as_on_date": str(as_on_date),
#                 "leave_balance": data
#             }
#         }




@frappe.whitelist()
def get_leave_balance(employeeId, as_on_date=None):
    try:
        if not employeeId:
            frappe.throw("Employee is required")

        as_on_date = getdate(as_on_date or nowdate())

        LEAVE_SEQUENCE = [
            "Compensatory Off",
            "Casual Leave",
            "Sick Leave",
            "Privilege Leave",
            "Medical Emergency Leave",
            # "Leave Without Pay",
            "Maternity Leave",
            "Special Maternity Leave",
            "Child Adoption Leave"
        ]

        FEMALE_ONLY_LEAVES = {
            
            
            "Maternity Leave",
            "Special Maternity Leave",
            "Child Adoption Leave"
        }

        ALLOCATION_REQUIRED = {
            "Medical Emergency Leave",
            # "Leave Without Pay",
            "Maternity Leave",
            "Special Maternity Leave",
            "Child Adoption Leave"
        }

        employee_gender = frappe.db.get_value(
            "Employee", employeeId, "gender"
        )


        allocations = frappe.get_all(
            "Leave Allocation",
            filters={
                "employee": employeeId,
                "docstatus": 1,
                "from_date": ["<=", as_on_date],
                "to_date": [">=", as_on_date]
            },
            fields=["leave_type"]
        )

        allocated_leave_types = {a.leave_type for a in allocations}


        final_leave_types = []

        for leave_type in LEAVE_SEQUENCE:

            if (
                leave_type in FEMALE_ONLY_LEAVES
                and employee_gender != "Female"
            ):
                continue

            if (
                leave_type in ALLOCATION_REQUIRED
                and leave_type not in allocated_leave_types
            ):
                continue

            final_leave_types.append(leave_type)

        result = []

        for lt in final_leave_types:

            earned = frappe.db.sql("""
                SELECT SUM(leaves)
                FROM `tabLeave Ledger Entry`
                WHERE employee = %s
                AND leave_type = %s
                AND leaves > 0
                AND from_date <= %s
                AND to_date >= %s
            """, (employeeId, lt, as_on_date, as_on_date))[0][0] or 0
            print(f"Earned for {lt}: {earned}")
            used = frappe.db.sql("""
                SELECT ABS(SUM(leaves))
                FROM `tabLeave Ledger Entry`
                WHERE employee = %s
                AND leave_type = %s
                AND leaves < 0
                AND from_date <= %s
                AND to_date >= %s
            """, (employeeId, lt, as_on_date, as_on_date))[0][0] or 0
            print(f"Used for {lt}: {used}")
            remaining = earned - used

            row = {
                "leave_type": lt,
                "allocated": round(earned, 2),
                "used": round(used, 2)
            }

            if remaining >= 0:
                row["remaining"] = round(remaining, 2)
            else :
                row["remaining"]= 0

            result.append(row)

        return {
            "success": True,
            "message": "Leave balance fetched successfully",
            "data": {
                "employee": employeeId,
                "gender": employee_gender,
                "as_on_date": str(as_on_date),
                "leave_balance": result
            }
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Leave Balance API Error")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }
