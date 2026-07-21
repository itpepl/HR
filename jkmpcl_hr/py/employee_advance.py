import frappe
from frappe import _
from frappe.utils import getdate, today
# from jkmpcl_hr.py.utils import  get_emp_hr_manager, get_ceo_user, get_emp_review_manager

def before_insert(doc, method):
    # Only applies to the very first save (new doc)
    doc.advance_amount = doc.custom_claim_amount

def validate(doc, method):
    validate_dates_not_in_past(doc)
    doc.advance_account = "Debtors - JKMPCL"

def validate_dates_not_in_past(doc):
    today_date = getdate(today())

    if doc.get("custom_from_date") and getdate(doc.custom_from_date) < today_date:
        frappe.throw(_("From Date cannot be a date in the past."))

    if doc.get("custom_to_date") and getdate(doc.custom_to_date) < today_date:
        frappe.throw(_("To Date cannot be a date in the past."))

def get_role_users(role):
    return [
        d.user
        for d in frappe.get_all(
            "Has Role",
            filters={
                "role": role,
                "parenttype": "User",
            },
            fields=["parent as user"],
        )
    ]

BRANCH_ROLE_MAP = {
    "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu": "CEO",
    "Jammu and Kashmir Milk Producers Co-operative Ltd Cheshmashahi Srinagar": "GAO",
}

def get_branch(doc):
    return frappe.db.get_value("Employee", doc.employee, "branch")

def get_role_users_by_branch(role, branch):
    """Users with the given role, restricted to the given branch."""
    role_users = get_role_users(role)
    return set(frappe.get_all(
        "User",
        filters={"name": ["in", role_users], "custom_branch": branch},
        pluck="name",
    ))

def get_approver_users(doc):
    """Users who should approve, based on the employee's branch."""
    branch = get_branch(doc)
    role = BRANCH_ROLE_MAP.get(branch)

    if not role:
        frappe.log_error(
            title="Advance Approval: Unmapped Branch",
            message=f"No CEO/GAO role mapped for branch '{branch}' on {doc.doctype} {doc.name}",
        )
        return set()

    role_users = get_role_users(role)

    # keep this filter in case a role has users spread across branches
    filtered_users = frappe.get_all(
        "User",
        filters={"name": ["in", role_users], "custom_branch": branch},
        pluck="name",
    )
    return set(filtered_users)

def share_with_users(doc, users):
    for user in users:
        frappe.share.add_docshare(
            doc.doctype,
            doc.name,
            user,
            read=1,
            write=1,
            select=1,
            submit=1,
            share=1,
            flags={"ignore_share_permission": True},
        )

def share_advance_doc(doc, method=None):
    old_doc = doc.get_doc_before_save()
    if not (old_doc and old_doc.workflow_state):
        return
    if old_doc.workflow_state == doc.workflow_state:
        return
    if frappe.session.user == "Administrator":
        return

    users = set()
    branch = get_branch(doc)

    if doc.workflow_state == "Approved by Reporting Manager":
        # PIC needs to review next - restrict to PIC users of this employee's branch
        if branch:
            users.update(get_role_users_by_branch("PIC", branch))
        else:
            frappe.log_error(
                title="Advance Approval: Missing Branch",
                message=f"No branch found for employee on {doc.doctype} {doc.name}",
            )
            frappe.error_log(
                title="Advance Approval: Missing Branch",
                message=f"No branch found for employee on {doc.doctype} {doc.name}",
            )

    elif doc.workflow_state == "Approve By PIC":
        # Already approved by PIC - if amount crosses threshold, CEO/GAO also need access
        if doc.advance_amount >= 10000:
            users.update(get_approver_users(doc))

    if users:
        share_with_users(doc, users)