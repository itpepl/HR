import frappe
from frappe import _
from frappe.utils import getdate
from jkmpcl_hr.overrides.attendance_request import revert_penalty_leave
def validate(doc, method):
    leave_details = get_leave_type(doc.leave_type)
    if not leave_details.is_compensatory:
        return
    
    # 1️⃣ Enforce single day
    if doc.from_date != doc.to_date:
        frappe.throw(_("For Compensatory Off, From Date and To Date must be the same."))

    # 2️⃣ Ensure linkage exists
    if not doc.custom_off_day_work_request:
        frappe.throw(_("Comp-Off must be linked to an Off-Day Work Request"))

    # 3️⃣ Set total leave days to 1.0
    if leave_details.custom_applied_once:
        doc.total_leave_days = 1.0
        

def on_submit(doc, method):
    leave_details = get_leave_type(doc.leave_type)
    if not leave_details.is_compensatory:
        return
    
    # Link Leave Application to Off-Day Work Request
    if doc.custom_off_day_work_request:
        frappe.db.set_value(
            "Off-Day Work Request",
            doc.custom_off_day_work_request,
            "leave_application",
            doc.name
        )
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