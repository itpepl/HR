import frappe
from frappe.utils import getdate,formatdate


@frappe.whitelist()
def create_employee_advance(**args):
    """
    API to create Employee Advance
    """

    employee = args.get("employee")
    from_date = args.get("custom_from_date")
    to_date = args.get("custom_to_date")
    places = args.get("custom_places_to_be_visited")
    purpose = args.get("purpose")
    claim_amount = args.get("custom_claim_amount")
    # advance_amount = args.get("advance_amount")

    # Mandatory Validation
    mandatory_fields = {
        "employee": employee,
        # "custom_from_date": from_date,
        # "custom_to_date": to_date,
        # "purpose": purpose,
        "custom_claim_amount": claim_amount,
    }

    # for field, value in mandatory_fields.items():
    #     if not value:
    #         frappe.throw(f"{field.replace('_', ' ').title()} is mandatory.")

    from_date = getdate(from_date)
    to_date = getdate(to_date)

    if to_date < from_date:
        frappe.throw("To Date cannot be earlier than From Date.")

    doc = frappe.new_doc("Employee Advance")
    doc.employee = employee
    doc.custom_from_date = from_date
    doc.custom_to_date = to_date
    doc.custom_places_to_be_visited = places
    doc.purpose = purpose
    doc.custom_claim_amount = claim_amount
    doc.advance_amount = claim_amount

    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "message": "Employee Advance created successfully.",
        "name": doc.name
    }

@frappe.whitelist()
def employee_advance_list(
    view_type="self",   # self / team
    filters=None,
    fields=None,
    order_by="creation desc",
    limit_page_length=None,
    limit_start=0,
):
    try:
        user = frappe.session.user
 
        employee = frappe.db.get_value(
            "Employee",
            {"user_id": user},
            "name"
        )
 
        if not employee:
            frappe.throw("Employee not linked with current user")
 
        # ---- Parse filters ----
        filters = frappe.parse_json(filters) if filters else []
 
        if isinstance(filters, dict):
            filters = [[k, "=", v] for k, v in filters.items()]
 
        # Convert status filter to workflow_state, same as your LTA API
        for f in filters:
            if isinstance(f, list) and len(f) >= 3 and f[0] == "status":
                f[0] = "workflow_state"
 
        if view_type == "self":
            filters.append(["employee", "=", employee])
 
        elif view_type == "team":
            filters.append(["employee", "!=", employee])
 
        else:
            frappe.throw("Invalid view_type. Use 'self' or 'team'.")
 
        advance_list = frappe.get_list(
            "Employee Advance",
            filters=filters,
            fields=fields or [
                "name", "employee", "employee_name",
                "custom_hq", "department", "custom_designation",
                "custom_from_date", "custom_to_date",
                "custom_places_to_be_visited", "purpose",
                "custom_claim_amount", "advance_amount",
                "workflow_state", "status", "docstatus",
                "posting_date",
            ],
            order_by=order_by,
            limit_page_length=limit_page_length,
            limit_start=limit_start,
        )
 
        total_records = frappe.get_list(
            "Employee Advance",
            filters=filters
        )
 
        # ---- Workflow state constants (verify against your Workflow) ----
        PENDING = "Pending"
        REP_MGR_APPROVED = "Approved by Reporting Manager"
        PIC_APPROVED = "Approve By PIC"
        CEO_GAO_PENDING = "CEO/GAO Approval"
        FINAL_APPROVED = "Final Approved"
        TERMINAL_STATES = {
            FINAL_APPROVED,
            "Rejected by Reporting Manager",
            "Rejected By PIC",
            "Rejected",
        }
 
        reporting_manager_map = {}
        user_roles = set()
 
        if view_type == "team":
            today_date = frappe.utils.today()
            user_roles = set(frappe.get_roles(user))
 
            employees_in_list = [*{row["employee"] for row in advance_list if row.get("employee")}]
 
            if employees_in_list:
                # Same tabApprover pattern used in your Leave/LTA APIs.
                # Assumes Employee Advance reporting-manager approval also
                # routes through the Approver child table on Employee with
                # parentfield 'custom_reporting_manager'. Confirm this is
                # actually how it's wired -- if reporting manager is instead
                # a plain field (e.g. Employee.reports_to), swap this block
                # for a simple frappe.db.get_value lookup per employee.
                role_rows = frappe.db.sql("""
                    SELECT parent AS employee
                    FROM `tabApprover`
                    WHERE user = %(user)s
                    AND effective_from <= %(today)s
                    AND parenttype = 'Employee'
                    AND parentfield = 'custom_reporting_manager'
                    AND parent IN %(employees)s
                """, {
                    "user": user,
                    "today": today_date,
                    "employees": employees_in_list
                }, as_dict=True)
 
                reporting_manager_map = {r["employee"]: True for r in role_rows}
 
        for row in advance_list:
            wf = row.get("workflow_state") or ""
            ds = row.get("docstatus", 0)
            emp = row.get("employee")
 
            enable = False
 
            if view_type == "team" and wf not in TERMINAL_STATES and ds != 1:
                if wf == PENDING:
                    # Reporting manager acts first
                    enable = reporting_manager_map.get(emp, False)
 
                elif wf == REP_MGR_APPROVED:
                    # PIC acts second (Approve -> "Approve By PIC" / Reject)
                    enable = "PIC" in user_roles
 
                elif wf == PIC_APPROVED:
                    # PIC acts again: Approve straight to Final (<10000)
                    # or Send for Approval to CEO/GAO (>=10000)
                    enable = "PIC" in user_roles
 
                elif wf == CEO_GAO_PENDING:
                    # Either CEO or GAO can close it out
                    enable = "CEO" in user_roles or "GAO" in user_roles
 
            row["enable"] = False
 
        advance_list = sorted(advance_list, key=lambda r: not r["enable"])
 
        data = []
        for d in advance_list:
            data.append({
                "name": d.get("name"),
                "employee": d.get("employee"),
                "employee_name": d.get("employee_name"),
                "custom_hq": d.get("custom_hq"),
                "department": d.get("department"),
                "custom_designation": d.get("custom_designation"),
                "from_date": formatdate(d.get("custom_from_date"), "dd-MM-yyyy") if d.get("custom_from_date") else "",
                "to_date": formatdate(d.get("custom_to_date"), "dd-MM-yyyy") if d.get("custom_to_date") else "",
                "places_to_be_visited": d.get("custom_places_to_be_visited"),
                "purpose": d.get("purpose"),
                "claim_amount": d.get("custom_claim_amount"),
                "advance_amount": d.get("advance_amount"),
                "status": d.get("workflow_state") or d.get("status"),
                "workflow_state": d.get("workflow_state"),
                "posting_date": formatdate(d.get("posting_date"), "dd-MM-yyyy") if d.get("posting_date") else "",
                "enable": False,
            })
 
        return {
            "success": True,
            "message": "Employee Advance list fetched successfully.",
            "data": data,
            "count": len(data),
            "total_records": len(total_records),
        }
 
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Employee Advance List API Error")
        return {
            "success": False,
            "message": str(frappe.get_traceback())
        }