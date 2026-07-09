
import frappe
from jkmpcl_hr.api.mobile.firebase import send_fcm_notification


MANAGER_LEVEL_PARENTFIELD = {
    "reporting": "custom_reporting_manager",
    "review": "custom_review_manager",
    "hr": "custom_hr_manager",
}


def workflow_notification(doc, method):
    frappe.logger().info(
        f"workflow_notification called for {doc.doctype} {doc.name}"
    )

    previous = doc.get_doc_before_save()
    old_state = getattr(previous, "workflow_state", None) if previous else None
    new_state = getattr(doc, "workflow_state", None)
    is_new_submission = previous is None

    if previous:
        frappe.logger().info(f"Workflow State Changed: {old_state} -> {new_state}")
        if old_state == new_state:
            frappe.logger().info("Workflow state not changed.")
            return

    status = new_state or getattr(doc, "status", "Updated")

    # --- 1. Notify the applicant/owner employee ---
    # Skip on the very first submission — the applicant just submitted it
    # themselves, they don't need a "your request is Pending" push.
    # Notify them only on later transitions (Approved/Rejected/etc).
    if is_new_submission:
        frappe.logger().info(
            "Initial submission — skipping applicant notification, "
            "notifying approver only."
        )
    else:
        notify_applicant(doc, status)

    # --- 2. Notify whichever manager level needs to act next ---
    notify_next_approver(doc, status)

    frappe.logger().info("Notification function completed.")


def notify_applicant(doc, status):
    if not getattr(doc, "employee", None):
        frappe.logger().info("Employee not found in document.")
        return

    employee = frappe.get_doc("Employee", doc.employee)

    frappe.logger().info(
        f"Employee: {employee.name}, Token: {employee.custom_fcm_token}"
    )

    if not employee.custom_fcm_token:
        frappe.log_error(
            f"FCM token not found for Employee {employee.name}",
            "Workflow Notification"
        )
        return

    frappe.logger().info(f"Sending applicant notification. Status: {status}")

    send_fcm_notification(
        token=employee.custom_fcm_token,
        title=f"{doc.doctype} {status}",
        body=f"Your {doc.doctype} ({doc.name}) has been {status.lower()}.",
        data={
            "doctype": doc.doctype,
            "docname": doc.name,
            "status": status,
            "body": f"Your {doc.doctype} ({doc.name}) has been {status.lower()}.",
            "title": f"{doc.doctype} {status}",
        },
    )


# =====================================================================
# Resolve "which manager level acts next" — one resolver per doctype,
# built from the same state sets / conditions your list APIs already use.
# =====================================================================

def notify_next_approver(doc, status):
    if not getattr(doc, "employee", None):
        frappe.logger().info("No employee on doc, skipping approver notification.")
        return

    resolver = NEXT_LEVEL_RESOLVERS.get(doc.doctype)

    if not resolver:
        frappe.logger().info(f"No approver resolver configured for {doc.doctype}.")
        return

    manager_level = resolver(doc)

    if not manager_level:
        frappe.logger().info(
            f"No pending manager level for {doc.doctype} {doc.name} "
            f"(state: {getattr(doc, 'workflow_state', None)}) — likely final state."
        )
        return

    send_to_manager_level(doc, manager_level, status)

def send_to_manager_level(doc, manager_level, status):
    parentfield = MANAGER_LEVEL_PARENTFIELD[manager_level]
    today = frappe.utils.today()

    approver = frappe.db.sql("""
        SELECT user
        FROM `tabApprover`
        WHERE parent = %(employee)s
        AND parenttype = 'Employee'
        AND parentfield = %(parentfield)s
        AND effective_from <= %(today)s
        ORDER BY effective_from DESC
        LIMIT 1
    """, {
        "employee": doc.employee,
        "parentfield": parentfield,
        "today": today,
    }, as_dict=True)

    if not approver:
        frappe.logger().info(
            f"No approver found in '{parentfield}' for employee {doc.employee}."
        )
        return

    approver_user_email = approver[0].user

    approver_employee = frappe.db.get_value(
        "Employee",
        {"user_id": approver_user_email},
        ["name", "custom_fcm_token"],
        as_dict=True,
    )

    if not approver_employee or not approver_employee.custom_fcm_token:
        frappe.logger().info(f"No FCM token for approver user {approver_user_email}.")
        return

    frappe.logger().info(
        f"Sending {manager_level} manager notification to {approver_user_email} "
        f"(Employee {approver_employee.name}). Status: {status}"
    )

    notification_title = f"{doc.doctype} Pending"
    notification_body = (
        f"{getattr(doc, 'employee_name', doc.name)}'s {doc.doctype} is now "
        f"{status.lower()} and awaiting your action."
    )

    send_fcm_notification(
        token=approver_employee.custom_fcm_token,
        title=notification_title,
        body=notification_body,
        data={
            "doctype": doc.doctype,
            "docname": doc.name,
            "status": status,
            "manager_level": manager_level,
            "title": notification_title,
            "body": notification_body,   # <-- was missing
        },
    )

# ---------------------------------------------------------------------
# Leave Application / Tour Request — same 3-tier states as in your
# list.py / get_tour_requests, so we reuse those sets directly.
# ---------------------------------------------------------------------

REPORTING_MGR_APPROVED_STATES = {
    "Pending Review Manager Approval",
    "Approved by Reporting Manager",
    "Approved by Review Manager",
    "Pending HR Approval",
    "Approved by HR Manager",
    "Approved",
}

REVIEW_MGR_APPROVED_STATES = {
    "Approved by Review Manager",
    "Pending HR Approval",
    "Approved by HR Manager",
    "Approved",
}

FINAL_STATES_3TIER = {"Approved", "Rejected"}  # extend if you have more reject variants


def resolve_3tier(doc):
    wf = getattr(doc, "workflow_state", None) or ""

    if wf in FINAL_STATES_3TIER or "Reject" in wf:
        return None

    if wf not in REPORTING_MGR_APPROVED_STATES:
        return "reporting"

    if wf not in REVIEW_MGR_APPROVED_STATES:
        return "review"

    return "hr"


# ---------------------------------------------------------------------
# Attendance Request — has conditional branching depending on
# reason / punch type / note, exactly as in get_manual_punches.
# ---------------------------------------------------------------------

ATTENDANCE_FINAL_STATES = {
    "Final Approved",
    "Rejected",
    "Rejected by Reporting Manager",
    "Rejected by Review Manager",
    "Rejected by HR",
}


def is_hr_direct_path(reason, punch_type, note):
    return reason == "Miss Punch" and (punch_type == "Both" or bool(note))


def is_review_path(reason, punch_type, note):
    return (
        reason == "Miss Punch" and punch_type != "Both" and not note
    ) or reason == "System Error"


def resolve_attendance_request(doc):
    wf = getattr(doc, "workflow_state", None) or ""

    if wf in ATTENDANCE_FINAL_STATES:
        return None

    reason = getattr(doc, "reason", "") or ""
    punch_type = getattr(doc, "custom_punch_type", "") or ""
    note = getattr(doc, "custom_note", "") or ""

    if wf == "Pending":
        return "reporting"

    if wf == "Approved by Reporting Manager":
        if is_hr_direct_path(reason, punch_type, note):
            return "hr"
        if is_review_path(reason, punch_type, note):
            return "review"
        return None

    if wf == "Approved by Review Manager":
        if is_review_path(reason, punch_type, note):
            return "hr"
        return None

    if wf == "Approved by HR":
        # only CEO-final-approval left; not one of your 3 manager levels
        return None

    return None


# ---------------------------------------------------------------------
# Off-Day Work Request — single-step: Pending -> Approved / Rejected.
# ⚠️ CONFIRM: which single level approves this — reporting manager?
# Defaulting to "reporting" below.
# ---------------------------------------------------------------------

def resolve_off_day_work_request(doc):
    wf = getattr(doc, "workflow_state", None) or ""

    if wf in {"Approved", "Rejected"}:
        return None

    return "reporting"  # confirm this is correct for your workflow


NEXT_LEVEL_RESOLVERS = {
    "Leave Application": resolve_3tier,
    "Tour Request": resolve_3tier,
    "Attendance Request": resolve_attendance_request,
    "Off-Day Work Request": resolve_off_day_work_request,
}