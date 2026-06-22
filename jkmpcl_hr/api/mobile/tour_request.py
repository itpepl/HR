import frappe
from frappe import _
from frappe.utils import getdate, date_diff, today

def get_status(workflow_state, docstatus):
    """
    Helper function to determine status based on workflow_state and docstatus
    """
    workflow_state = (workflow_state or "").lower()
    
    # Check docstatus first
    if docstatus == 2:
        return "Cancelled"
    
    elif docstatus == 1:
        # If docstatus is 1, it's Approved regardless of workflow_state
        return "Approved"
    
    elif docstatus == 0:
        # For Draft/Open status
        if "reject" in workflow_state:
            return "Rejected"
        elif "approved" in workflow_state:
            # Even if workflow_state says "Approved by", but docstatus is 0, it's still in progress
            # So we should return "Open" or "Draft"
            if "draft" in workflow_state:
                return "Draft"
            else:
                # If it's in approval process but not yet fully approved (docstatus=0)
                return "Open"
        elif "draft" in workflow_state:
            return "Draft"
        elif workflow_state:
            # For any other workflow_state with docstatus=0, it's Open
            return "Open"
        else:
            return "Draft"
    
    return "Unknown"

@frappe.whitelist()
def create_tour_request(data):
    try:
        if isinstance(data, str):
            data = frappe.parse_json(data)

        name = data.get("name")
        from_date = data.get("from_date")
        to_date = data.get("to_date")
        purpose_of_travel = data.get("purpose_of_travel")

        # -----------------------------
        # Mandatory Validation
        # -----------------------------
        if not from_date:
            return {
                "success": False,
                "message": "From Date is required",
                "data": None
            }

        if not to_date:
            return {
                "success": False,
                "message": "To Date is required",
                "data": None
            }

        if not purpose_of_travel:
            return {
                "success": False,
                "message": "Purpose of Travel is required",
                "data": None
            }

        from_date = getdate(from_date)
        to_date = getdate(to_date)

        # -----------------------------
        # Date Validation
        # -----------------------------
        if to_date < from_date:
            frappe.throw(
                _("To Date cannot be before From Date.")
            )

        days_diff = date_diff(to_date, from_date)

        if days_diff != 1:
            frappe.throw(
                _("Tour duration must be exactly 1 day. Please select a To Date that is one day after the From Date.")
            )

        # -----------------------------
        # Employee Validation
        # -----------------------------
        employee = frappe.db.get_value(
            "Employee",
            {"user_id": frappe.session.user},
            ["name", "employee_name"],
            as_dict=True
        )

        if not employee:
            frappe.throw(
                _("Employee record not found for the logged-in user.")
            )

        # -----------------------------
        # UPDATE FLOW
        # -----------------------------
        if name:

            if not frappe.db.exists("Tour Request", name):
                return {
                    "success": False,
                    "message": "Tour Request not found",
                    "data": None
                }

            doc = frappe.get_doc("Tour Request", name)

            if doc.employee != employee.name:
                frappe.throw(
                    _("You are not authorized to update this Tour Request.")
                )

            if doc.docstatus != 0:
                frappe.throw(
                    _("Only Draft Tour Requests can be updated.")
                )

            # Check overlapping requests excluding current record
            existing_tour = frappe.db.sql("""
                SELECT name
                FROM `tabTour Request`
                WHERE employee = %s
                    AND name != %s
                    AND docstatus != 2
                    AND from_date <= %s
                    AND to_date >= %s
                LIMIT 1
            """, (
                employee.name,
                name,
                to_date,
                from_date
            ), as_dict=True)

            if existing_tour:
                frappe.throw(
                    _("Tour Request already exists for this date range: {0}")
                    .format(existing_tour[0].name)
                )

            doc.from_date = from_date
            doc.to_date = to_date
            doc.purpose_of_travel = purpose_of_travel

            doc.save(ignore_permissions=True)

            return {
                "success": True,
                "message": "Tour Request updated successfully",
                "data": {
                    "name": doc.name,
                    "employee": doc.employee,
                    "employee_name": doc.employee_name,
                    "status": get_status(
                        doc.workflow_state,
                        doc.docstatus
                    )
                }
            }

        # -----------------------------
        # CREATE FLOW
        # -----------------------------
        else:

            # Check overlapping requests
            existing_tour = frappe.db.sql("""
                SELECT name
                FROM `tabTour Request`
                WHERE employee = %s
                    AND docstatus != 2
                    AND from_date <= %s
                    AND to_date >= %s
                LIMIT 1
            """, (
                employee.name,
                to_date,
                from_date
            ), as_dict=True)

            if existing_tour:
                frappe.throw(
                    _("Tour Request already exists for this date range: {0}")
                    .format(existing_tour[0].name)
                )

            doc = frappe.get_doc({
                "doctype": "Tour Request",
                "employee": employee.name,
                "travel_request_date": today(),
                "from_date": from_date,
                "to_date": to_date,
                "purpose_of_travel": purpose_of_travel
            })

            doc.insert(ignore_permissions=True)

            return {
                "success": True,
                "message": "Tour Request created successfully",
                "data": {
                    "name": doc.name,
                    "employee": doc.employee,
                    "employee_name": doc.employee_name,
                    "status": get_status(
                        doc.workflow_state,
                        doc.docstatus
                    )
                }
            }

    except frappe.ValidationError as e:
        frappe.clear_messages()
        return {
            "success": False,
            "message": str(e),
            "data": None
        }

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Tour Request API Error"
        )

        return {
            "success": False,
            "message": "Unable to process Tour Request. Please contact Administrator.",
            "data": None
        }

@frappe.whitelist()
def get_tour_requests(
    filters=None,
    limit_page_length=20,
    limit_start=0
):
    try:
        # Parse Filters
        filters = frappe.parse_json(filters) if filters else {}
        
        # Extract filter values from the nested array structure
        filter_dict = {}
        if isinstance(filters, list):
            for filter_item in filters:
                if isinstance(filter_item, list) and len(filter_item) >= 3:
                    field = filter_item[0]
                    operator = filter_item[1]
                    value = filter_item[2]
                    
                    # Convert to dictionary format
                    if operator == "=":
                        filter_dict[field] = value
                    elif operator == ">=":
                        filter_dict[field + "_gte"] = value
                    elif operator == "<=":
                        filter_dict[field + "_lte"] = value
        else:
            filter_dict = filters

        # Extract values from filter dictionary
        department = filter_dict.get("department")
        employee = filter_dict.get("employee")
        from_date = filter_dict.get("from_date") or filter_dict.get("from_date_gte")
        to_date = filter_dict.get("to_date") or filter_dict.get("to_date_lte")
        status = filter_dict.get("status")

        tour_filters = {}

        # Department Filter
        if department:
            employees = frappe.get_all(
                "Employee",
                filters={"department": department},
                pluck="name"
            )

            if not employees:
                return {
                    "success": True,
                    "message": "No employees found for this department",
                    "total_records": 0,
                    "page_size": int(limit_page_length),
                    "current_page": 1,
                    "total_pages": 0,
                    "returned_records": 0,
                    "data": []
                }

            tour_filters["employee"] = ["in", employees]

        # Employee Filter
        if employee:
            tour_filters["employee"] = employee

        # Status Filter - Now handling both docstatus and workflow_state
        if status:
            if status == "Approved":
                tour_filters["docstatus"] = 1
            elif status == "Cancelled":
                tour_filters["docstatus"] = 2
            elif status == "Open" or status == "Draft":
                # For Open/Draft, docstatus=0 and not rejected
                tour_filters["docstatus"] = 0
                # Exclude rejected ones if they have docstatus=0
                tour_filters["workflow_state"] = ["not like", "%Reject%"]
            elif status == "Rejected":
                tour_filters["docstatus"] = 0
                tour_filters["workflow_state"] = ["like", "%Reject%"]
            else:
                # For any other status, check workflow_state
                tour_filters["workflow_state"] = status

        # Date Range Filter - Handle from_date and to_date properly
        if from_date and to_date:
            tour_filters["from_date"] = ["<=", to_date]
            tour_filters["to_date"] = [">=", from_date]

        # Total Records
        total_records = frappe.db.count(
            "Tour Request",
            filters=tour_filters
        )

        # Get Records
        records = frappe.get_all(
            "Tour Request",
            filters=tour_filters,
            fields=[
                "name",
                "employee",
                "employee_name",
                "from_date",
                "to_date",
                "purpose_of_travel",
                "workflow_state",
                "docstatus",
                "creation",
            ],
            order_by="creation desc",
            limit_start=int(limit_start),
            limit_page_length=int(limit_page_length)
        )

        # Convert workflow_state to status
        for row in records:
            row["status"] = get_status(
                row.get("workflow_state"),
                row.get("docstatus")
            )

            # Remove only docstatus
            row.pop("docstatus", None)
            
        page_size = int(limit_page_length)
        current_page = (int(limit_start) // page_size) + 1 if page_size else 1
        total_pages = (
            (total_records + page_size - 1) // page_size
            if page_size else 1
        )

        return {
            "success": True,
            "message": "Tour Requests fetched successfully",
            "total_records": total_records,
            "page_size": page_size,
            "current_page": current_page,
            "total_pages": total_pages,
            "returned_records": len(records),
            "data": records,
            "applied_filters": filter_dict  # Optional: return applied filters for debugging
        }

    except Exception as e:
        frappe.log_error(
            frappe.get_traceback(),
            "Get Tour Requests API"
        )

        return {
            "success": False,
            "message": str(e),
            "data": []
        }

@frappe.whitelist(allow_guest=False)
def get_workflow_states(workflow_name):
    """
    Get all workflow states from Workflow child table
    """

    if not workflow_name:
        return {
            "success": False,
            "message": "Workflow name is required"
        }

    if not frappe.db.exists("Workflow", workflow_name):
        return {
            "success": False,
            "message": f"Workflow '{workflow_name}' not found"
        }

    workflow = frappe.get_doc("Workflow", workflow_name)

    states = []

    for row in workflow.states:
        states.append({
            "state": row.state,
            
        })

    return {
        "success": True,
        "workflow_name": workflow.name,
        "total_states": len(states),
        "states": states
    }