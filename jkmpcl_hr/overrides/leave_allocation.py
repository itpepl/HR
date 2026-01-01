import frappe
from frappe import _
from frappe.utils import formatdate
from hrms.hr.doctype.leave_allocation.leave_allocation import LeaveAllocation
from hrms.hr.doctype.leave_allocation.leave_allocation import OverlapError


def custom_validate_allocation_overlap(self):
		if frappe.db.get_value("Leave Type", self.leave_type, "is_compensatory"):
			return

		leave_allocation = frappe.db.sql(
			"""
			SELECT
				name
			FROM `tabLeave Allocation`
			WHERE
				employee=%s AND leave_type=%s
				AND name <> %s AND docstatus=1
				AND to_date >= %s AND from_date <= %s""",
			(self.employee, self.leave_type, self.name, self.from_date, self.to_date),
		)

		if leave_allocation:
			frappe.msgprint(
				_("{0} already allocated for Employee {1} for period {2} to {3}").format(
					self.leave_type, self.employee, formatdate(self.from_date), formatdate(self.to_date)
				)
			)

			frappe.throw(
				_("Reference")
				+ f': <a href="/app/Form/Leave Allocation/{leave_allocation[0][0]}">{leave_allocation[0][0]}</a>',
				OverlapError,
			)
