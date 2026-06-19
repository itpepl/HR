import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, add_days

class TourRequest(Document):
    
    def validate(self):
        # Mandatory field validation
        if not self.from_date:
            frappe.throw(_("From Date is mandatory"))
        
        if not self.to_date:
            frappe.throw(_("To Date is mandatory"))
        
        if not self.purpose_of_travel:
            frappe.throw(_("Purpose of Travel is mandatory"))
        
        # To Date cannot be earlier than From Date
        if self.to_date < self.from_date:
            frappe.throw(_("To Date cannot be earlier than From Date"))
        
        # Travel duration must be exactly 1 day
        days_diff = date_diff(self.to_date, self.from_date)
        
        if days_diff != 1:
            frappe.throw(
                _("Travel duration must be exactly 1 day. To Date should be one day after From Date.")
            )
        
        # Check overlapping Tour Request
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
            self.employee,
            self.name or "",
            self.to_date,
            self.from_date
        ), as_dict=True)
        
        if existing_tour:
            frappe.throw(
                _("Tour Request already exists for this date range: {0}").format(
                    existing_tour[0].name
                )
            )
    
    def on_submit(self):
        if self.workflow_state != "Approved by HR":
            return
        
        total_days = date_diff(self.to_date, self.from_date) + 1
        
        for i in range(total_days):
            att_date = add_days(self.from_date, i)
            
            if frappe.db.exists(
                "Attendance",
                {
                    "employee": self.employee,
                    "attendance_date": att_date
                }
            ):
                continue
            
            employee_details = frappe.db.get_value(
                "Employee",
                self.employee,
                ["employee_name", "department", "company", "branch"],
                as_dict=True
            )
            
            att = frappe.get_doc({
                "doctype": "Attendance",
                "employee": self.employee,
                "employee_name": employee_details.employee_name,
                "department": employee_details.department,
                "company": employee_details.company,
                "attendance_date": att_date,
                "status": "Present",
                "custom_branch": employee_details.branch,
                "custom_remark": "On Duty"
            })
            
            att.insert(ignore_permissions=True)
            att.submit()
    
    def on_cancel(self):
        total_days = date_diff(self.to_date, self.from_date) + 1
        
        for i in range(total_days):
            att_date = add_days(self.from_date, i)
            
            attendance_list = frappe.get_all(
                "Attendance",
                filters={
                    "employee": self.employee,
                    "attendance_date": att_date,
                    "custom_remark": "On Duty",
                    "docstatus": 1
                },
                pluck="name"
            )
            
            for att_name in attendance_list:
                att = frappe.get_doc("Attendance", att_name)
                att.cancel()
                att.delete(ignore_permissions=True)
        
        frappe.db.commit()