import frappe

@frappe.whitelist()
def get_shift_requests(employeeId=None, start_date=None, end_date=None):

    try:
        filters = {}

        if employeeId:
            filters["employee"] = employeeId

        if start_date and end_date:
            filters["from_date"] = [">=", start_date]
            filters["to_date"] = ["<=", end_date]

        order_by = "from_date desc"

        shift_requests = frappe.get_all(
            "Shift Request",
            filters=filters,
            fields=["shift_type", "employee", "approver", "from_date", "to_date", "name"],
            order_by=order_by
        )

        return {
            "success": True,
            "message": "Shift requests fetched successfully",
            "data": shift_requests
        }

    except Exception as e:
        error_message = f"Error fetching shift requests: {str(e)}"
        frappe.log_error(error_message, "Shift Request API Error")

        return {
            "success": False,
            "message": error_message,
            "data": None
        }

@frappe.whitelist()
def create_shift_request(data):

    try:
        if isinstance(data, str):
            data = frappe.parse_json(data)

        employee = data.get("employee")
        shift_type = data.get("shift_type")
        from_date = data.get("from_date")
        to_date = data.get("to_date")
        remarks = data.get("remarks")  
        approver=data.get("shift_request_approver")

        if not employee or not shift_type or not from_date or not to_date:
            return {
                "success": False,
                "message": "Missing required fields",
                "data": None
            }

        shift_request = frappe.get_doc({
            "doctype": "Shift Request",
            "employee": employee,
            "shift_type": shift_type,
            "from_date": from_date,
            "to_date": to_date,
            "remarks": remarks,
            "approver": approver
        })

        shift_request.insert(ignore_permissions=True)

        return {
            "success": True,
            "message": "Shift request created successfully",
            "data": {"name": shift_request.name}
        }

    except Exception as e:
        error_message = f"Error creating shift request: {str(e)}"
        frappe.log_error(error_message, "Shift Request Create API Error")

        return {
            "success": False,
            "message": error_message,
            "data": None
        }


@frappe.whitelist()
def shift_type_list(branch=None):

    try:
        filters = {}

        if branch:
            filters["custom_branch"] = branch

 
        shift_types = frappe.get_all(
            "Shift Type",
            filters=filters,
            fields=["name", "start_time", "end_time"],
            order_by="name asc"
        )

        return {
            "success": True,
            "message": "Shift types fetched successfully",
            "data": shift_types
        }

    except Exception as e:
        error_message = f"Error fetching shift types: {str(e)}"
        frappe.log_error(error_message, "Shift Type API Error")

        return {
            "success": False,
            "message": error_message,
            "data": None
        }
