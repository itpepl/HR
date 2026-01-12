import frappe
from frappe import _
from frappe.utils import formatdate, flt
from hrms.hr.doctype.leave_allocation.leave_allocation import LeaveAllocation, get_carry_forwarded_leaves
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


class CustomLeaveAllocation(LeaveAllocation):
	@frappe.whitelist()
	def set_total_leaves_allocated(self):
		print(f"\n\n  THIS IS overrided \n\n")
		self.unused_leaves = flt(
			get_carry_forwarded_leaves(self.employee, self.leave_type, self.from_date, self.carry_forward),
			self.precision("unused_leaves"),
		)

		self.total_leaves_allocated = flt(
			flt(self.unused_leaves) + flt(self.new_leaves_allocated) + flt(self.custom_opening_balance),
			self.precision("total_leaves_allocated"),
		)

		self.limit_carry_forward_based_on_max_allowed_leaves()

		if self.carry_forward:
			self.set_carry_forwarded_leaves_in_previous_allocation()

		if (
			not self.total_leaves_allocated
			and not frappe.db.get_value("Leave Type", self.leave_type, "is_earned_leave")
			and not frappe.db.get_value("Leave Type", self.leave_type, "is_compensatory")
		):
			frappe.throw(_("Total leaves allocated is mandatory for Leave Type {0}").format(self.leave_type))
		
