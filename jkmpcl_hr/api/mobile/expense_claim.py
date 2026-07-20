import traceback

import frappe
from frappe.utils import getdate, now_datetime, strip_html
from frappe.utils.file_manager import save_file
from datetime import timedelta


# =====================================================
# Workflow / Role Constants
# =====================================================
PENDING_STATE = "Pending"
APPROVED_BY_RM_STATE = "Approved by Reporting Manager"
REJECTED_BY_RM_STATE = "Rejected by Reporting Manager"
APPROVED_BY_HR_STATE = "Approved by HR"
REJECTED_BY_HR_STATE = "Rejected by HR"
FINAL_APPROVED_STATE = "Final Approved"
REJECTED_STATE = "Rejected"

# Final stage (Approved by HR -> Final Approved) is role-gated, not
# employee-approver-gated, per the Workflow "Allowed" column.
FINAL_APPROVER_ROLES = {"CEO", "PCI", "GAO"}

LTA_CLAIM_TYPE = "LTA"


def get_latest_approver_map(employees, parentfield):
    if not employees:
        return {}

    rows = frappe.db.sql("""
        SELECT parent AS employee, user, effective_from
        FROM `tabApprover`
        WHERE parenttype = 'Employee'
        AND parentfield = %(parentfield)s
        AND parent IN %(employees)s
        AND effective_from <= %(now)s
        ORDER BY effective_from DESC
    """, {
        "parentfield": parentfield,
        "employees": employees,
        "now": now_datetime(),
    }, as_dict=True)

    approver_map = {}
    for row in rows:
        # First hit per employee is the latest, since sorted DESC.
        if row.employee not in approver_map:
            approver_map[row.employee] = row.user

    return approver_map


def get_single_employee_approver(employee, parentfield):
    return frappe.db.get_value(
        "Approver",
        {
            "parent": employee,
            "parenttype": "Employee",
            "parentfield": parentfield,
            "effective_from": ["<=", now_datetime()],
        },
        "user",
        order_by="effective_from desc",
    )



def compute_enable_flag(user, workflow_state, docstatus, reporting_manager=None, hr_manager=None, user_roles=None):
    if docstatus == 1:
        # Final Approved - nothing left to do.
        return False

    user_roles = user_roles or set()

    if workflow_state == PENDING_STATE:
        # Reporting Manager acts first.
        return reporting_manager == user

    elif workflow_state == APPROVED_BY_RM_STATE:
        # HR acts second, only after Reporting Manager has approved.
        return hr_manager == user

    elif workflow_state == APPROVED_BY_HR_STATE:
        # Final approver acts last - role based (CEO / PCI / GAO).
        return bool(user_roles & FINAL_APPROVER_ROLES)

    # REJECTED_BY_RM_STATE / REJECTED_BY_HR_STATE / REJECTED_STATE /
    # FINAL_APPROVED_STATE (or anything unrecognized) -> terminal.
    return False



@frappe.whitelist()
def get_leave_breakdown(employee, custom_period_of_leave_from, custom_period_of_leave_to):
    try:
        if not employee:
            frappe.throw("Please Fill Employee")
        if not custom_period_of_leave_from or not custom_period_of_leave_to:
            frappe.throw("Please Fill Period Of Leave From and To")

        period_from = getdate(custom_period_of_leave_from)
        period_to = getdate(custom_period_of_leave_to)

        if period_from > period_to:
            frappe.throw("Period Of Leave From date cannot be after the To date.")

        # Reuse the existing helper - do not re-implement the streak logic here.
        from jkmpcl_hr.py.expense_claim import compute_lta_day_breakdown

        employee_doc = frappe.get_doc("Employee", employee)
        breakdown = compute_lta_day_breakdown(employee_doc, period_from, period_to)

        sanctioned_days = frappe.db.get_single_value(
            "HR Settings", "custom_lta_sanctioned_days"
        )

        return {
            "success": True,
            "message": "Leave Breakdown Fetched Successfully!",
            "data": {
                "custom_cl": breakdown["cl_count"],
                "custom_pl": breakdown["pl_count"],
                "custom_ph": breakdown["ph_count"],
                "custom_wo": breakdown["wo_count"],
                "custom_total": breakdown["total_days"],
                "custom_availed_or_sanctioned_no_of_days": sanctioned_days,
            },
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "LTA Leave Breakdown API Error")
        return {
            "success": False,
            "message": str(e),
            "data": None,
        }


# =====================================================
# Whitelisted: List LTA Expense Claims (self / team)
# =====================================================
@frappe.whitelist()
def list(
    view_type="self",   # self / team
    filters=None,
    fields=None,
    order_by="creation desc",
    limit_page_length=None,
    limit_start=0,
):
    try:
        user = frappe.session.user

        filters = frappe.parse_json(filters) if filters else []

        if isinstance(filters, dict):
            filters = [[k, "=", v] for k, v in filters.items()]

        # Convert status filter to workflow_state
        for f in filters:
            if len(f) >= 3 and f[0] == "status":
                f[0] = "workflow_state"

        employee = frappe.db.get_value(
            "Employee",
            {"user_id": user},
            "name"
        )

        if not employee:
            frappe.throw("Employee not linked with current user")

        # Restrict this API to LTA claims only.
        filters.append(["custom_expense_claim_type", "=", LTA_CLAIM_TYPE])

        if view_type == "self":
            filters.append(["employee", "=", employee])

        elif view_type == "team":
            filters.append(["employee", "!=", employee])

        else:
            frappe.throw("Invalid view_type. Use 'self' or 'team'.")

        claim_list = frappe.get_list(
            "Expense Claim",
            filters=filters,
            fields=fields or [
                "name", "employee", "employee_name",
                "custom_expense_claim_type",
                "custom_period_of_leave_from", "custom_period_of_leave_to",
                "custom_lta_period_from", "custom_lta_period_to",
                "custom_period_of_last_lta_availed_from",
                "custom_period_of_last_lta_availed_to",
                "custom_availed_or_sanctioned_no_of_days",
                "custom_cl", "custom_pl", "custom_ph", "custom_wo", "custom_total",
                "total_claimed_amount", "total_sanctioned_amount",
                "status", "workflow_state", "posting_date",
                "docstatus","custom_total_distance_travelled","custom_actual_journey_expenses_incurred_rs",
                "department","custom_head_quarter",
            ],
            order_by=order_by,
            limit_page_length=limit_page_length,
            limit_start=limit_start
        )

        total_records = frappe.get_list(
            "Expense Claim",
            filters=filters
        )

        reporting_manager_map = {}
        hr_manager_map = {}
        user_roles = set()

        if view_type == "team":
            employees_in_list = [*{row["employee"] for row in claim_list if row.get("employee")}]

            if employees_in_list:
                reporting_manager_map = get_latest_approver_map(
                    employees_in_list, "custom_reporting_manager"
                )
                hr_manager_map = get_latest_approver_map(
                    employees_in_list, "custom_hr_manager"
                )
                user_roles = set(frappe.get_roles(user))

        for row in claim_list:
            enable = False

            if view_type == "team":
                emp = row.get("employee")
                enable = compute_enable_flag(
                    user,
                    row.get("workflow_state") or "",
                    row.get("docstatus"),
                    reporting_manager=reporting_manager_map.get(emp),
                    hr_manager=hr_manager_map.get(emp),
                    user_roles=user_roles,
                )

            row["enable"] = False

        claim_list = sorted(claim_list, key=lambda r: not r["enable"])

        for row in claim_list:
            if not fields or "docstatus" not in fields:
                row.pop("docstatus", None)

        return {
            "success": True,
            "message": "LTA Expense Claim List Loaded Successfully!",
            "data": claim_list,
            "count": len(claim_list),
            "total_records": len(total_records)
        }

    except Exception:
        frappe.log_error(frappe.get_traceback(), "LTA Expense Claim List API Error")
        return {
            "success": False,
            "message": str(frappe.get_traceback())
        }


# =====================================================
# Whitelisted: Create an LTA Expense Claim
# Only 4 mandatory fields: employee, custom_expense_claim_type,
# custom_period_of_leave_from, custom_period_of_leave_to.
# Everything else (posting_date, expenses, etc.) is optional here and
# is either defaulted below or left to validate() / DocType defaults.
# =====================================================
@frappe.whitelist()
def create(**args):
    try:
        mandatory_fields = {
            "employee": "Employee",
            "custom_period_of_leave_from": "Period Of Leave From",
            "custom_period_of_leave_to": "Period Of Leave To",
        }

        for field, label in mandatory_fields.items():
            if not args.get(field):
                frappe.throw(f"Please Fill {label}", frappe.MandatoryError)

        employee = args.get("employee")
        args["naming_series"] = "HR-LTA-.YYYY.-"
        args["custom_expense_claim_type"] = "LTA"
        # -----------------------------
        # DATE CONVERSION
        # -----------------------------
        args["custom_period_of_leave_from"] = getdate(args.get("custom_period_of_leave_from"))
        args["custom_period_of_leave_to"] = getdate(args.get("custom_period_of_leave_to"))

        if args.get("posting_date"):
            args["posting_date"] = getdate(args.get("posting_date"))
        else:
            args["posting_date"] = getdate()

        # -----------------------------
        # EXPENSE ROWS (optional at creation time - validate() tolerates
        # an empty/zero total_lta_amount, rows can be added later)
        # -----------------------------
        expenses = args.get("expenses")
        if isinstance(expenses, str):
            expenses = frappe.parse_json(expenses)

        normalized_expenses = []
        for row in (expenses or []):
            if not row.get("expense_date"):
                frappe.throw(f"Expense Date is required in expense row {row.get('idx', '')}")
            if row.get("amount") in (None, ""):
                frappe.throw(f"Amount is required in expense row {row.get('idx', '')}")

            normalized_expenses.append({
                "expense_date": getdate(row.get("expense_date")),
                "expense_type": row.get("expense_type") or LTA_CLAIM_TYPE,
                "description": row.get("description"),
                "amount": row.get("amount"),
                "sanctioned_amount":row.get("amount"),
            })

        if normalized_expenses:
            args["expenses"] = normalized_expenses

        # -----------------------------
        # GRAND TOTAL = sum of child table (expenses) amounts
        # Set explicitly rather than relying on core Expense Claim's own
        # calculation, so it's correct regardless of insert flags used.
        # -----------------------------
        total_expense_amount = sum(row["amount"] for row in normalized_expenses)
        args["total_claimed_amount"] = total_expense_amount
        args["grand_total"] = total_expense_amount
        args["currency"] = "INR"
        args["exchange_rate"]= "1"


        # -----------------------------
        # DEFAULTED FIELDS (not mandatory, just filled if missing)
        # -----------------------------
        if not args.get("company"):
            args["company"] = frappe.db.get_value("Employee", employee, "company")

        # Workflow always starts at Pending, regardless of what the client sent.
        args["workflow_state"] = PENDING_STATE

        # -----------------------------
        # OPTIONAL FIELDS
        # -----------------------------
        if args.get("custom_email_cc"):
            args["custom_email_cc"] = frappe.parse_json(args.get("custom_email_cc"))

        # -----------------------------
        # CREATE DOCUMENT
        # (custom validate() hook already registered on Expense Claim
        # re-checks eligibility, suspension overlap, CL/PL/PH/WO breakdown,
        # LTA entitlement and per-year claim count on insert.)
        # -----------------------------
        claim_doc = frappe.get_doc({
            "doctype": "Expense Claim",
            **args,
        })

        claim_doc.insert(ignore_permissions=True)

        # -----------------------------
        # PROOF DOCUMENT UPLOAD (multipart/form-data "file" field(s))
        # Attached synchronously so the response can confirm it right away -
        # this is a single small image/PDF, not worth a background queue.
        # -----------------------------
        attached_files = []
        uploaded_files = frappe.request.files.getlist("file") if frappe.request else []

        for f in uploaded_files:
            file_doc = save_file(
                fname=f.filename,
                content=f.stream.read(),
                dt="Expense Claim",
                dn=claim_doc.name,
                is_private=1,
            )
            attached_files.append(file_doc.file_url)

        # If your Expense Claim has a single-attach field for the proof
        # (e.g. custom_proof_document), populate it with the first upload.
        if attached_files and claim_doc.meta.has_field("custom_proof_document"):
            claim_doc.db_set("custom_proof_document", attached_files[0], update_modified=False)

        # -----------------------------
        # ENABLE FLAG
        # (freshly created claim is always "Pending" - enable reflects
        # whether the CURRENT session user, i.e. the creator, is also
        # that employee's Reporting Manager and can act on it right away)
        # -----------------------------
        current_user = frappe.session.user
        reporting_manager = get_single_employee_approver(employee, "custom_reporting_manager")
        hr_manager = get_single_employee_approver(employee, "custom_hr_manager")
        user_roles = set(frappe.get_roles(current_user))

        enable = compute_enable_flag(
            current_user,
            claim_doc.workflow_state,
            claim_doc.docstatus,
            reporting_manager=reporting_manager,
            hr_manager=hr_manager,
            user_roles=user_roles,
        )

        return {
            "success": True,
            "message": "LTA Expense Claim Created",
            "data": {
                "expense_claim": claim_doc.name,
                "workflow_state": claim_doc.workflow_state,
                "enable": False,
                "attached_files": attached_files,
            },
        }

    except Exception as e:
        error_message = None

        if frappe.local.message_log:
            log = frappe.local.message_log[0]
            error_message = log.get("message") if isinstance(log, dict) else str(log)

        if not error_message:
            error_message = str(e)

        error_message = strip_html(str(error_message))

        frappe.log_error(
            title="LTA Expense Claim API Error",
            message=traceback.format_exc()
        )

        return {
            "success": False,
            "message": error_message,
            "data": None,
        }
    
def get_fiscal_year_bounds(date):
    date = getdate(date)

    if date.month >= 4:
        start = getdate(f"{date.year}-04-01")
        end = getdate(f"{date.year + 1}-03-31")
    else:
        start = getdate(f"{date.year - 1}-04-01")
        end = getdate(f"{date.year}-03-31")

    return start, end


@frappe.whitelist()
def get_lta_fiscal_period(employee_code=None, expense_claim=None):
    try:
        # Get Employee
        if employee_code:
            employee = employee_code
        else:
            employee = frappe.db.get_value(
                "Employee",
                {"user_id": frappe.session.user},
                "name"
            )

            if not employee:
                frappe.throw(("Employee not found for the logged-in user."))

        today = getdate()

        current_start, current_end = get_fiscal_year_bounds(today)
        prev_start, prev_end = get_fiscal_year_bounds(
            current_start - timedelta(days=1)
        )

        response = {
            "employee": employee,
            "lta_period_from": current_start,
            "lta_period_to": current_end,
            "last_availed_from": None,
            "last_availed_to": None,
        }

        conditions = """
            employee = %s
            AND docstatus != 2
            AND custom_period_of_leave_from IS NOT NULL
            AND custom_period_of_leave_to IS NOT NULL
            AND custom_period_of_leave_to BETWEEN %s AND %s
        """

        values = [employee, current_start, current_end]

        if expense_claim:
            conditions += " AND name != %s"
            values.append(expense_claim)

        claim_exists = frappe.db.sql(
            f"""
            SELECT name
            FROM `tabExpense Claim`
            WHERE {conditions}
            LIMIT 1
            """,
            tuple(values),
            as_dict=True,
        )

        if claim_exists:
            response["last_availed_from"] = prev_start
            response["last_availed_to"] = prev_end
        
        return {
            "success": True,
            "message": "LTA fiscal periods fetched successfully.",
            "data": response,
        }
    except:
        return {
            "success": False,
            "message": str(frappe.get_traceback())
        }
