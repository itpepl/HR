import frappe
from frappe import _
from frappe.utils import getdate, add_days
from hrms.hr.doctype.shift_request.shift_request import ShiftRequest
from hrms.hr.utils import share_doc_with_approver, validate_active_employee

from jkmpcl_hr.py.utils import get_emp_reporting_manager


class CustomShiftRequest(ShiftRequest):
    def validate(self):
        validate_active_employee(self.employee)
        self.validate_from_to_dates("from_date", "to_date")
        # self.validate_overlapping_shift_requests()
        self.validate_approver()
        self.validate_default_shift()
    
    
    def validate_approver(self):
        department = frappe.get_value("Employee", self.employee, "department")
        shift_approver = frappe.get_value("Employee", self.employee, "shift_request_approver")
        
        custom_approver = get_emp_reporting_manager(self.employee)
        
        approvers = frappe.db.sql(
            """select approver from `tabDepartment Approver` where parent= %s and parentfield = 'shift_request_approver'""",
            (department),
        )
        approvers = [approver[0] for approver in approvers]
        approvers.append(shift_approver)
        if custom_approver:
            approvers.append(custom_approver)
            
        if self.approver not in approvers:
            frappe.throw(_("Only Approvers can Approve this Request."))
    
    
    def on_submit(self):
        if self.status not in ["Approved", "Rejected"]:
            frappe.throw(_("Only Shift Request with status 'Approved' and 'Rejected' can be submitted"))
        if self.status == "Approved":
            
            handle_shift_request_submit(self)
            
            assignment_doc = frappe.new_doc("Shift Assignment")
            assignment_doc.company = self.company
            assignment_doc.shift_type = self.shift_type
            assignment_doc.employee = self.employee
            assignment_doc.start_date = self.from_date
            if self.to_date:
                assignment_doc.end_date = self.to_date
            assignment_doc.shift_request = self.name
            assignment_doc.flags.ignore_permissions = 1
            assignment_doc.insert()
            assignment_doc.submit()

            frappe.msgprint(
                ("Shift Assignment: {0} created for Employee: {1}").format(
                    frappe.bold(assignment_doc.name), frappe.bold(self.employee)
                )
            )

def handle_shift_request_submit(doc):
    """Called on submit of Shift Request.
       If status is Approved, adjust the current Shift Assignment by:
       - Closing existing assignment one day before new range
       - Creating a tail assignment from day after new range to old end_date
    """

    from_date = getdate(doc.from_date)
    to_date = getdate(doc.to_date or doc.from_date)

    # 1) Find existing submitted Shift Assignment covering this range
    current_sa = frappe.get_all(
        "Shift Assignment",
        filters={
            "employee": doc.employee,
            "docstatus": 1,
            "start_date": ["<=", from_date],
            "end_date": [">=", to_date],
        },
        fields=[
            "name",
            "employee",
            "shift_type",
            "company",
            "start_date",
            "end_date",
            "custom_branch",
        ],
        order_by="start_date desc",
        limit=1,
    )

    if not current_sa:
        # nothing to split
        return

    current_sa = current_sa[0]
    old_start = getdate(current_sa.start_date)
    old_end = getdate(current_sa.end_date)

    new_end_for_old = add_days(from_date, -1)

    # Only update if this still gives a valid range
    if new_end_for_old >= old_start:
        frappe.db.set_value(
            "Shift Assignment",
            current_sa.name,
            "end_date",
            new_end_for_old,
        )
    else:
        # new shift starts on or before old_start → old "head" is not needed
        # (optionally you could cancel/delete the old assignment here)
        pass

    # 3) Create tail assignment from day after new range up to old_end
    tail_start = add_days(to_date, 1)
    if tail_start <= old_end:
        new_tail = frappe.get_doc({
            "doctype": "Shift Assignment",
            "employee": current_sa.employee,
            "shift_type": current_sa.shift_type,
            "company": current_sa.company,
            "custom_branch": current_sa.custom_branch,
            "start_date": tail_start,
            "end_date": old_end,
        })
        new_tail.insert(ignore_permissions=True)
        new_tail.submit()