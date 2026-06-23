import frappe
from frappe import _
from frappe.utils import getdate, date_diff, today,formatdate,add_days
from jkmpcl_hr.jkmpcl_hr.doctype.attendance_lock.attendance_lock import AttendanceLock
from jkmpcl_hr.py.utils import get_emp_reporting_manager, get_emp_hr_manager, get_ceo_user,get_emp_review_manager

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

        # Calculate No. of Days
        no_of_days = date_diff(to_date, from_date) + 1

        # Validate travel duration is at least 2 days
        if no_of_days < 2:
            frappe.throw(
                _("Travel request cannot be less than 2 days.")
            )

        # -----------------------------
        # Employee Validation
        # -----------------------------
        employee = frappe.db.get_value(
            "Employee",
            {"user_id": frappe.session.user},
            ["name", "employee_name", "status", "custom_suspended_from_date", "custom_suspended_to_date"],
            as_dict=True
        )

        if not employee:
            frappe.throw(
                _("Employee record not found for the logged-in user.")
            )

        # -----------------------------
        # Employee Suspension Validation
        # -----------------------------
        validate_employee_suspension(employee, from_date, to_date)

        # -----------------------------
        # Attendance Lock Validation
        # -----------------------------
        validate_attendance_lock(employee.name, from_date, to_date)

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
            doc.no_of_days = no_of_days

            doc.save(ignore_permissions=True)

            return {
                "success": True,
                "message": "Tour Request updated successfully",
                "data": {
                    "name": doc.name,
                    "employee": doc.employee,
                    "employee_name": doc.employee_name,
                    "no_of_days": doc.no_of_days,
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
                "employee_name": employee.employee_name,
                "travel_request_date": today(),
                "from_date": from_date,
                "to_date": to_date,
                "purpose_of_travel": purpose_of_travel,
                "no_of_days": no_of_days
            })

            doc.insert(ignore_permissions=True)

            return {
                "success": True,
                "message": "Tour Request created successfully",
                "data": {
                    "name": doc.name,
                    "employee": doc.employee,
                    "employee_name": doc.employee_name,
                    "no_of_days": doc.no_of_days,
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

    except Exception as e:
        frappe.log_error(
            f"Error: {str(e)}\nTraceback: {frappe.get_traceback()}",
            "Tour Request API Error"
        )
        
        return {
            "success": False,
            "message": "Unable to process Tour Request. Please contact Administrator.",
            "data": None
        }


def validate_employee_suspension(employee, from_date, to_date):
    """
    Validate that the employee is not suspended before allowing Tour Request creation
    """
    if not employee:
        return
    
    # Check if employee is suspended
    if employee.get("status") == "Suspended":
        frappe.throw(
            _("Tour Request cannot be created. Employee is currently suspended")
        )
    
    suspended_from = employee.get("custom_suspended_from_date")
    suspended_to = employee.get("custom_suspended_to_date")
    
    if not suspended_from:
        return
    
    # Convert suspension dates to string if they are date objects
    if hasattr(suspended_from, 'strftime'):
        suspended_from = suspended_from.strftime('%Y-%m-%d')
    if suspended_to and hasattr(suspended_to, 'strftime'):
        suspended_to = suspended_to.strftime('%Y-%m-%d')
    
    current_date = today()
    
    # Check if current date falls within suspension period
    is_suspended = False
    
    if suspended_from and suspended_to:
        if current_date >= suspended_from and current_date <= suspended_to:
            is_suspended = True
    elif suspended_from and not suspended_to:
        if current_date >= suspended_from:
            is_suspended = True
    
    if is_suspended:
        from_date_str = formatdate(suspended_from) if suspended_from else "N/A"
        to_date_str = formatdate(suspended_to) if suspended_to else "Ongoing"
        
        frappe.throw(
            _("Tour Request cannot be created. Employee {0} is currently suspended from {1} to {2}.").format(
                employee.get("employee_name", ""),
                from_date_str,
                to_date_str
            )
        )
    
    # Also check if any travel date falls within suspension period
    if from_date and to_date:
        total_days = date_diff(to_date, from_date) + 1
        
        for i in range(total_days):
            travel_date = add_days(from_date, i)
            
            # Convert travel date to string if it's a date object
            if hasattr(travel_date, 'strftime'):
                travel_date = travel_date.strftime('%Y-%m-%d')
            
            is_date_suspended = False
            
            if suspended_from and suspended_to:
                if travel_date >= suspended_from and travel_date <= suspended_to:
                    is_date_suspended = True
            elif suspended_from and not suspended_to:
                if travel_date >= suspended_from:
                    is_date_suspended = True
            
            if is_date_suspended:
                from_date_str = formatdate(suspended_from) if suspended_from else "N/A"
                to_date_str = formatdate(suspended_to) if suspended_to else "Ongoing"
                travel_date_str = formatdate(travel_date)
                
                frappe.throw(
                    _("Tour Request cannot be created. Employee {0} is suspended from {1} to {2}. Travel date {3} falls within suspension period.").format(
                        employee.get("employee_name", ""),
                        from_date_str,
                        to_date_str,
                        travel_date_str
                    )
                )


def validate_attendance_lock(employee_name, from_date, to_date):
    """
    Validate attendance lock for travel request date and tour period
    """
    # Check attendance lock for travel request date (today)
    travel_request_date = today()
    
    if travel_request_date:
        lock_name = AttendanceLock.is_attendance_locked(
            travel_request_date,
            employee_name
        )
        
        if lock_name:
            month = frappe.db.get_value(
                "Attendance Lock",
                lock_name,
                "month"
            )
            
            if not month:
                month = formatdate(
                    travel_request_date,
                    "MMMM yyyy"
                )
            
            frappe.throw(
                _("Attendance is locked for {0}. Travel Request Date is not allowed.").format(month),
                title=_("Attendance Lock")
            )
    
    # Check attendance lock for entire tour period
    for i in range(date_diff(to_date, from_date) + 1):
        att_date = add_days(from_date, i)
        
        lock_name = AttendanceLock.is_attendance_locked(
            att_date,
            employee_name
        )
        
        if lock_name:
            month = frappe.db.get_value(
                "Attendance Lock",
                lock_name,
                "month"
            )
            
            if not month:
                month = formatdate(
                    att_date,
                    "MMMM yyyy"
                )
            
            frappe.throw(
                _("Attendance is locked for {0}. Tour Request cannot be created or updated for this period.").format(month),
                title=_("Attendance Lock")
            )


def get_status(workflow_state, docstatus):
    """Helper function to get status"""
    if docstatus == 1:
        return "Submitted"
    elif docstatus == 2:
        return "Cancelled"
    elif workflow_state:
        return workflow_state
    else:
        return "Draft"

@frappe.whitelist()
def get_tour_requests(
    view_type="self",   # self / team
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

        # Get logged-in employee
        current_employee = frappe.db.get_value(
            "Employee",
            {"user_id": frappe.session.user},
            "name"
        )

        if not current_employee:
            return {
                "success": False,
                "message": "Employee not linked with current user",
                "data": []
            }

        # Extract values from filter dictionary
        department = filter_dict.get("department")
        employee_filter = filter_dict.get("employee")
        from_date = filter_dict.get("from_date") or filter_dict.get("from_date_gte")
        to_date = filter_dict.get("to_date") or filter_dict.get("to_date_lte")
        status = filter_dict.get("status")

        tour_filters = {}

        # Apply view_type filter
        if view_type == "self":
            # Only show current user's requests
            tour_filters["employee"] = current_employee
        elif view_type == "team":
            # Show all team members' requests (excluding current user)
            tour_filters["employee"] = ["!=", current_employee]
        else:
            return {
                "success": False,
                "message": "Invalid view_type. Use 'self' or 'team'.",
                "data": []
            }

        # Department Filter (only applies if view_type is team)
        if department and view_type == "team":
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

            # Combine department filter with team filter
            tour_filters["employee"] = ["in", employees]

        # Employee Filter (override if provided and view_type is team)
        if employee_filter and view_type == "team":
            tour_filters["employee"] = employee_filter
        elif employee_filter and view_type == "self":
            # For self view, ignore employee filter or validate it
            if employee_filter != current_employee:
                return {
                    "success": False,
                    "message": "You can only view your own tour requests in self view",
                    "data": []
                }
            tour_filters["employee"] = current_employee

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
            "applied_filters": filter_dict,
            "view_type": view_type 
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