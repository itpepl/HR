import frappe



#leave type list api
@frappe.whitelist()
def get_leave_types():
    try:
        leave_types = frappe.get_all(
            "Leave Type",
            pluck="name"
        )

    except Exception as e:
        frappe.log_error("Error While Getting Leave Types", str(e))
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success": False,
            "message": f"Error while fetching leave types: {str(e)}",
            "data": None
        }

    else:
        frappe.local.response["message"] = {
            "success": True,
            "message": "Leave types fetched successfully",
            "data": leave_types
        }
        
        
@frappe.whitelist()
def list(
    filters=None,
    or_filters=None,
    fields=["name","employee","leave_type","from_date","to_date","status","total_leave_days","workflow_state"],
    order_by=None,
    limit_page_length=0,
    limit_start=0,
):
    try:
        # 🔐 Get employee linked with logged-in user
        employee = frappe.db.get_value(
            "Employee",
            {"user_id": frappe.session.user},
            "name"
        )

        if not employee:
            frappe.throw("Employee not linked with current user")

        employee_list = [employee]

        # --- Parse filters ---
        filters = frappe.parse_json(filters) if filters else []

        if isinstance(filters, dict):
            filters = [[k, "=", v] for k, v in filters.items()]

        # Enforce employee filter
        filters.append(["employee", "in", employee_list])

        parsed_fields = frappe.parse_json(fields)

        if "employee" not in parsed_fields:
            parsed_fields.append("employee")

        leave_application_list_raw = frappe.get_list(
            "Leave Application",
            filters=filters,
            or_filters=or_filters,
            fields=parsed_fields,
            order_by=order_by,
            limit_page_length=limit_page_length,
            limit_start=limit_start
        )

        total_count = len(leave_application_list_raw)

    except Exception as e:
        frappe.log_error("Error While Getting Leave Application List", str(e))
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success": False,
            "message": str(e),
            "data": None
        }

    else:
        frappe.local.response["message"] = {
            "success": True,
            "message": "Leave Application List Loaded Successfully!",
            "data": leave_application_list_raw,
            "count": total_count
        }
