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
    view_type="self",
    filters=None,
    limit_page_length=20,
    limit_start=0
):
    try:

        # -------------------------
        # Parse filters
        # -------------------------
        filters = frappe.parse_json(filters) if filters else []

        filter_dict = {}

        if isinstance(filters, dict):
            filters = [[k, "=", v] for k, v in filters.items()]

        if isinstance(filters, list):
            for item in filters:
                if isinstance(item, (list, tuple)) and len(item) >= 3:
                    field, op, value = item[0], item[1], item[2]

                    if op == "=":
                        filter_dict[field] = value
                    elif op == ">=":
                        filter_dict[field + "_gte"] = value
                    elif op == "<=":
                        filter_dict[field + "_lte"] = value

        # -------------------------
        # Current Employee
        # -------------------------
        current_employee = frappe.db.get_value(
            "Employee",
            {"user_id": frappe.session.user},
            "name"
        )

        if not current_employee:
            return {"success": False, "message": "Employee not found", "data": []}

        # -------------------------
        # TEAM LOGIC
        # -------------------------
        # employee_role_map: for TEAM view, maps each employee -> the set
        # of roles ('reporting' / 'review' / 'hr') the CURRENT logged-in
        # user holds specifically FOR THAT EMPLOYEE. This replaces a
        # single global "current_manager_role" variable, which was wrong:
        # a user can be the reporting manager for one employee and the
        # HR manager for a completely different employee at the same
        # time. Using one global role for the whole request meant rows
        # for employees where you're the reporting manager could
        # incorrectly get evaluated against HR's rules (or vice versa),
        # producing enable=False even on rows that were genuinely your
        # turn to act on.
        # -------------------------
        employee_role_map = {}

        if view_type == "self":
            employee_list = [current_employee]

        elif view_type == "team":
            today = frappe.utils.today()

            # Step 1: Get all employees where current user appears as approver
            candidate_employees = frappe.db.sql("""
                SELECT DISTINCT parent
                FROM `tabApprover`
                WHERE user = %(user)s
                AND effective_from <= %(today)s
                AND parenttype = 'Employee'
                AND parentfield IN (
                    'custom_reporting_manager',
                    'custom_review_manager',
                    'custom_hr_manager'
                )
            """, {
                "user": frappe.session.user,
                "today": today
            }, pluck="parent")

            employee_list = []

            if candidate_employees:
                placeholders = ", ".join(["%s"] * len(candidate_employees))

                # Step 2: Fetch ALL approver rows for candidate employees
                all_entries = frappe.db.sql("""
                    SELECT parent, user, parentfield, effective_from
                    FROM `tabApprover`
                    WHERE parent IN ({placeholders})
                    AND effective_from <= %s
                    AND parenttype = 'Employee'
                    AND parentfield IN (
                        'custom_reporting_manager',
                        'custom_review_manager',
                        'custom_hr_manager'
                    )
                    ORDER BY parent ASC, parentfield ASC, effective_from DESC
                """.format(placeholders=placeholders),
                    tuple(candidate_employees) + (today,),
                    as_dict=True
                )

                # Step 3: Per (employee + parentfield), find the MAX
                # effective_from date. Note: we do NOT pick a single
                # "winner" row here — if two rows share the exact same
                # effective_from (e.g. during a manager handover on the
                # same day), SQL row order for ties is not guaranteed,
                # so blindly keeping "the first row seen" can silently
                # drop the current user's row and keep someone else's
                # instead. Instead we track the max date per group, and
                # in Step 4 treat EVERYONE tied at that max date as a
                # valid current approver.
                max_effective_from = {}
                for entry in all_entries:
                    key = (entry["parent"], entry["parentfield"])
                    if (
                        key not in max_effective_from
                        or entry["effective_from"] > max_effective_from[key]
                    ):
                        max_effective_from[key] = entry["effective_from"]

                # Step 4: For each employee, record EVERY role (parentfield)
                # for which the current user is tied for the most recent
                # effective_from date. An employee can appear with multiple
                # roles if the current user is, e.g., both their reporting
                # manager AND their review manager.
                role_field_map = {
                    "custom_reporting_manager": "reporting",
                    "custom_review_manager": "review",
                    "custom_hr_manager": "hr",
                }

                for entry in all_entries:
                    key = (entry["parent"], entry["parentfield"])
                    if (
                        entry["effective_from"] == max_effective_from[key]
                        and entry["user"] == frappe.session.user
                    ):
                        employee_role_map.setdefault(
                            entry["parent"], set()
                        ).add(role_field_map[entry["parentfield"]])

                employee_list = [
                    emp for emp in employee_role_map
                    if emp != current_employee
                ]

        else:
            return {"success": False, "message": "Invalid view_type"}

        if not employee_list:
            employee_list = ["__none__"]

        # -------------------------
        # Base filters
        # -------------------------
        tour_filters = [
            ["employee", "in", employee_list]
        ]

        # -------------------------
        # Department filter
        # -------------------------
        department = filter_dict.get("department")

        if department and view_type == "team":
            dept_employees = frappe.db.get_list(
                "Employee",
                filters={
                    "reports_to": current_employee,
                    "department": department
                },
                pluck="name",
                ignore_permissions=True
            )

            employee_list = dept_employees or ["__none__"]

            # Direct reports fetched via reports_to imply a reporting-manager
            # relationship, so tag them accordingly for the enable logic.
            for emp in employee_list:
                employee_role_map.setdefault(emp, set()).add("reporting")

            tour_filters = [
                ["employee", "in", employee_list]
            ]

        # -------------------------
        # Employee override
        # -------------------------
        employee_filter = filter_dict.get("employee")

        if employee_filter:
            if view_type == "self" and employee_filter != current_employee:
                return {
                    "success": False,
                    "message": "You can only view your own data"
                }

            tour_filters = [["employee", "=", employee_filter]]

        # -------------------------
        # Status filter
        # -------------------------
        status = filter_dict.get("status")

        if status:
            if status == "Approved":
                tour_filters.append(["docstatus", "=", 1])

            elif status == "Cancelled":
                tour_filters.append(["docstatus", "=", 2])

            elif status in ["Open", "Draft"]:
                tour_filters.append(["docstatus", "=", 0])
                tour_filters.append(["workflow_state", "not like", "%Reject%"])

            elif status == "Rejected":
                tour_filters.append(["docstatus", "=", 0])
                tour_filters.append(["workflow_state", "like", "%Reject%"])

            else:
                tour_filters.append(["workflow_state", "=", status])

        # -------------------------
        # Date filter
        # -------------------------
        from_date = filter_dict.get("from_date") or filter_dict.get("from_date_gte")
        to_date = filter_dict.get("to_date") or filter_dict.get("to_date_lte")

        if from_date:
            tour_filters.append(["to_date", ">=", from_date])

        if to_date:
            tour_filters.append(["from_date", "<=", to_date])

        # -------------------------
        # COUNT
        # -------------------------
        total_records = len(
            frappe.db.get_list(
                "Tour Request",
                filters=tour_filters,
                pluck="name",
                ignore_permissions=True
            )
        )

        # -------------------------
        # DATA
        # -------------------------
        records = frappe.db.get_list(
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
            limit_page_length=int(limit_page_length),
            ignore_permissions=True
        )

        # -------------------------
        # Workflow states
        # ⚠️ Must match the exact "State" values in your Workflow doctype.
        # Verify with:
        #   frappe.db.get_list("Tour Request", pluck="workflow_state", limit_page_length=0)
        # -------------------------
        PENDING_STATE = "Pending"
        REPORTING_MGR_APPROVED_STATE = "Approved by Reporting Manager"
        REVIEW_MGR_APPROVED_STATE = "Approved by Review Manager"

        # -------------------------
        # Build final records with status + enable flag
        # -------------------------
        for row in records:
            row["status"] = get_status(row["workflow_state"], row["docstatus"])

            wf = row["workflow_state"]
            ds = row["docstatus"]
            display_status = row["status"] or ""

            # -------------------------
            # Terminal states are never actionable
            # -------------------------
            # docstatus: 0 = Draft, 1 = Submitted, 2 = Cancelled (Frappe standard)
            # A cancelled document (ds == 2) means the request was withdrawn/
            # cancelled — no approver acted on it at that point, so there is
            # nothing "pending" to enable. Same for a rejected request: the
            # flow has ended, no further action possible.
            #
            # NOTE: we check the *computed* display_status (from get_status())
            # rather than only the raw workflow_state, because get_status()
            # may map several raw workflow_state values onto a "Rejected by
            # ..." label that doesn't literally contain "Reject" itself.
            is_cancelled = ds == 2 or "Cancel" in display_status
            is_rejected = "Reject" in wf or "Reject" in display_status

            if is_cancelled or is_rejected:
                row["enable"] = False

            elif view_type == "team":
                # Look up the role(s) the CURRENT user holds specifically
                # for THIS row's employee (not a single global role).
                roles = employee_role_map.get(row["employee"], set())

                enable = False

                if "reporting" in roles and wf == PENDING_STATE:
                    enable = True

                if "review" in roles and wf == REPORTING_MGR_APPROVED_STATE:
                    enable = True

                if "hr" in roles and wf == REVIEW_MGR_APPROVED_STATE:
                    enable = True

                row["enable"] = enable

            else:
                row["enable"] = False

            row.pop("docstatus", None)

        return {
            "success": True,
            "message": "Tour Requests fetched successfully",
            "total_records": total_records,
            "returned_records": len(records),
            "data": records,
            "view_type": view_type,
            "applied_filters": filter_dict
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Tour API Error")
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