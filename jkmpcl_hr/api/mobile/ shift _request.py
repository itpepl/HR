import frappe

@frappe.whitelist()
def get_shift_requests(employeeId=None, start_date=None, end_date=None):
    """
    Fetch shift requests based on optional filters: employee, start_date, and end_date.
    If no date filters are passed, results are shown in LIFO (latest first).
    """
    try:
        filters = {}

        # Filter by employee
        if employeeId:
            filters["employee"] = employeeId

        # Optional date range filter
        if start_date and end_date:
            filters["from_date"] = [">=", start_date]
            filters["to_date"] = ["<=", end_date]

        # Default LIFO order
        order_by = "from_date desc"

        shift_requests = frappe.get_all(
            "Shift Request",
            filters=filters,
            fields=["shift_type", "employee", "approver", "from_date", "to_date", "name"],
            order_by=order_by
        )

        # SUCCESS RESPONSE
        return {
            "success": True,
            "message": "Shift requests fetched successfully",
            "data": shift_requests
        }

    except Exception as e:
        error_message = f"Error fetching shift requests: {str(e)}"
        frappe.log_error(error_message, "Shift Request API Error")

        # ERROR RESPONSE
        return {
            "success": False,
            "message": error_message,
            "data": None
        }



@frappe.whitelist()
def create_shift_request(employee, shift_type, from_date, to_date):
    """
    Create a new shift request.
    """
    try:
        shift_request = frappe.get_doc({
            "doctype": "Shift Request",
            "employee": employee,
            "shift_type": shift_type,
            "from_date": from_date,
            "to_date": to_date,
            # "approver": approver
        })

        shift_request.insert()
        frappe.db.commit()

        return {
            "success": True,
            "message": "Shift request created successfully",
            "data": {
                "name": shift_request.name
            }
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
            filters["branch"] = branch

 
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
