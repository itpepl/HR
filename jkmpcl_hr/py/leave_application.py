import frappe
from frappe import _
from frappe.utils import getdate, add_years
from jkmpcl_hr.overrides.attendance_request import revert_penalty_leave
from jkmpcl_hr.py.utils import send_notification_email


def validate(doc, method):
    leave_details = get_leave_type(doc.leave_type)
    if not leave_details.is_compensatory:
        return
    
    # 1️⃣ Enforce single day
    if doc.from_date != doc.to_date:
        frappe.throw(_("For Compensatory Off, From Date and To Date must be the same."))

    # 2️⃣ Ensure linkage exists
    # if not doc.custom_off_day_work_request:
    #     frappe.throw(_("Comp-Off must be linked to an Off-Day Work Request"))

    # 3️⃣ Set total leave days to 1.0
    if leave_details.custom_applied_once:
        doc.total_leave_days = 1.0


def on_update(doc, method):
    handle_workflow_notification(doc)

def handle_workflow_notification(doc):

        recipients,notification_name = get_notification_recipients(doc)

        notification_doc = frappe.get_doc("Notification", notification_name)
        if notification_doc:

            # Call your custom notification function
            send_notification_email(
                recipients=recipients,
                doctype=doc.doctype,
                docname=doc.name,
                notification_name=notification_name,
                send_link=False,
                fallback_subject=f"Leave Application for {doc.from_date} to {doc.to_date})",
                fallback_message=f"Leave Application for { doc.from_date } to {doc.to_date} is now in '{ doc.workflow_state }' state.",
                enabled=notification_doc.enabled,
                send_system_notification=notification_doc.send_system_notification,
                channel=notification_doc.channel
            )

def get_notification_recipients(doc):
        recipients = []
        approver_user = None
        notification_name = "Leave Application Approval"

        if doc.workflow_state == "Pending":
            approver = frappe.db.get_list(
                "Approver",
                filters={
                    "parent": doc.employee,
                    "effective_from": ["<=", frappe.utils.now_datetime()],
                    "parentfield": "custom_reporting_manager"
                },
                fields=["name"],
                order_by="effective_from desc",
                ignore_permissions=True,
                limit=1
            )

            if approver:
                approver_user = frappe.db.get_value("Approver", approver[0].name, "user")

        elif doc.workflow_state == "Approved by Reporting Manager":

            approver = frappe.db.get_list(
                "Approver",
                filters={
                    "parent": doc.employee,
                    "effective_from": ["<=", frappe.utils.now_datetime()],
                    "parentfield": "custom_review_manager"
                },
                fields=["name"],
                order_by="effective_from desc",
                ignore_permissions=True,
                limit=1
            )

            if approver:
                approver_user = frappe.db.get_value("Approver", approver[0].name, "user")

        elif doc.workflow_state == "Approved by Review Manager":

            approver = frappe.db.get_list(
                "Approver",
                filters={
                    "parent": doc.employee,
                    "effective_from": ["<=", frappe.utils.now_datetime()],
                    "parentfield": "custom_hr_manager"
                },
                fields=["name"],
                order_by="effective_from desc",
                ignore_permissions=True,
                limit=1
            )

            if approver:
                approver_user = frappe.db.get_value("Approver", approver[0].name, "user")

        elif doc.workflow_state == "Approved by HR":
            users = frappe.get_all("Has Role", filters={"role": "CEO"}, pluck="parent") or []

            ceo_users = frappe.get_all(
                "User",
                filters=[
                    ["User", "name", "in", users],
                    ["User", "enabled", "=", 1],
                    ["User", "name", "!=", "Administrator"]
                ],
                pluck="name"
            )
            recipients.extend(ceo_users)
            
        elif doc.workflow_state in ["Final Approved", "Rejected", "Rejected by Reporting Manager", "Rejected by Review Manager", "Rejected by HR"]:
            approver_user = frappe.db.get_value("Employee", doc.employee, "user_id")
            if doc.workflow_state == "Final Approved":
                notification_name = "Leave Application Approved"
            else:
                notification_name = "Leave Application Rejected"

        if approver_user:
            recipients.append(approver_user)

        return recipients, notification_name


def on_submit(doc, method):
    attendance_name = frappe.db.get_value(
        "Attendance",
        {
            "employee": doc.employee,
            "attendance_date": doc.from_date
        },
        "name"
    )
    if attendance_name:
        revert_penalty_leave(attendance_name)
    leave_details = get_leave_type(doc.leave_type)
    if not leave_details.is_compensatory:
        return
    
    if doc.custom_off_day_work_request:
        frappe.db.set_value(
            "Off-Day Work Request",
            doc.custom_off_day_work_request,
            "leave_application",
            doc.name
        )
    
 
def before_submit(doc, method):
    doc.status = "Approved"
        
    
@frappe.whitelist()
def get_leave_type(leave_type):
    return frappe.db.get_value("Leave Type", {"name": leave_type}, ["name", "is_compensatory", "custom_applied_once", "custom_leave_type"], as_dict=True)


@frappe.whitelist()
def get_valid_comp_off(employee, leave_date, leave_type_name):
    leave_date = getdate(leave_date)

    """
    Rules:
    - Comp-Off must be created
    - Must not be expired
    - Must not be already used in Leave Application
    - Leave date must fall within validity window
    """

    leave_allocation = frappe.db.get_all(
        "Leave Allocation",
        filters={
            "employee": employee,
            "leave_type": leave_type_name,
            "docstatus": 1,
            "from_date": ["<=", leave_date],
            "to_date": [">=", leave_date]
        },
        fields=["name"],
        order_by="from_date asc",
    )

    if not leave_allocation:
        return None
    
    for allocation in leave_allocation:
        record = frappe.db.get_value(
            "Off-Day Work Request",
            {
                "employee": employee,
                "comp_off_created": 1,
                "leave_allocation": allocation.name,
                "leave_application": ["is", "not set"],
                "docstatus": 1
            },
            ["name", "date"],
            as_dict=True
        )
        
        if record:
            return record
    
    if not record:
        return None

    return record   


@frappe.whitelist()
def get_open_leave_types(employee=None):
    """
    Returns open leave types allowed for Leave Application dropdown
    Ignores user permissions intentionally (controlled data)
    """
    
    only_for_female_leave_types = ["Maternity Leave", "Child Adoption Leave"]
    
    is_female = True if frappe.db.get_value("Employee", employee, "gender") == "Female" else False
    
    joining_date = frappe.db.get_value("Employee", employee, "date_of_joining")
    
    
        # only_for_female_leave_types.append("Special Maternity Leave")
        
    if is_female:
        if joining_date and getdate() <= add_years(joining_date, 2):
            return frappe.get_all(
                "Leave Type",
                filters={
                    "custom_is_open_leave": 1,
                },
                pluck="name",
                ignore_permissions=True
            )
        else:
            return frappe.get_all(
                "Leave Type",
                filters={
                    "custom_is_open_leave": 1,
                    "name": ["not in", ["Special Maternity Leave"]]
                },
                pluck="name",
                ignore_permissions=True
            )
        
    return frappe.get_all(
        "Leave Type",
        filters={
            "custom_is_open_leave": 1,
            "name": ["not in", ["Maternity Leave", "Child Adoption Leave", "Special Maternity Leave"]]
        },
        pluck="name",
        ignore_permissions=True
    )