import frappe
from frappe import _
from frappe.utils import cint, flt
from hrms.hr.doctype.leave_application.leave_application import LeaveApplication, get_leave_balance_on, get_number_of_leave_days, is_lwp


def custom_validate_balance_leaves(self):
    precision = cint(frappe.db.get_single_value("System Settings", "float_precision")) or 2
    print(f"\n\n Precision: {precision} \n\n")
    if self.from_date and self.to_date:
        self.total_leave_days = get_number_of_leave_days(
            self.employee,
            self.leave_type,
            self.from_date,
            self.to_date,
            self.half_day,
            self.half_day_date,
        )

        if self.total_leave_days <= 0:
            frappe.throw(
                _(
                    "The day(s) on which you are applying for leave are holidays. You need not apply for leave."
                )
            )

        if not is_lwp(self.leave_type):
            leave_balance = get_leave_balance_on(
                self.employee,
                self.leave_type,
                self.from_date,
                self.to_date,
                consider_all_leaves_in_the_allocation_period=True,
                for_consumption=True,
            )
            
            
            leave_balance_for_consumption = flt(
                leave_balance.get("leave_balance_for_consumption"), precision
            )

            leave_type = frappe.db.get_value("Leave Type", self.leave_type, "custom_leave_type")

            if leave_type not in ["Medical Emergency Leave", "Maternity Leave", "Special Maternity Leave", "Child Adoption Leave"] and self.status != "Rejected" and (
                leave_balance_for_consumption < self.total_leave_days or not leave_balance_for_consumption
            ):
                self.show_insufficient_balance_message(leave_balance_for_consumption)

