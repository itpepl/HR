import frappe
from frappe import _
from frappe.utils import formatdate, flt, getdate, add_days
from hrms.hr.doctype.leave_allocation.leave_allocation import LeaveAllocation, get_carry_forwarded_leaves, show_expire_leave_dialog
from hrms.hr.doctype.leave_allocation.leave_allocation import OverlapError
from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import (
	create_leave_ledger_entry,
	expire_allocation,
	process_expired_allocation,
)



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
		

	def create_leave_ledger_entry(self, submit=True):
		if self.unused_leaves:
			expiry_days = frappe.db.get_value(
				"Leave Type", self.leave_type, "expire_carry_forwarded_leaves_after_days"
			)
			end_date = add_days(self.from_date, expiry_days - 1) if expiry_days else self.to_date
			args = dict(
				leaves=self.unused_leaves,
				from_date=self.from_date,
				to_date=min(getdate(end_date), getdate(self.to_date)),
				is_carry_forward=1,
			)
			create_leave_ledger_entry(self, args, submit)
			if submit and getdate(end_date) < getdate():
				show_expire_leave_dialog(self.unused_leaves, self.leave_type)

		args = dict(
			leaves=self.new_leaves_allocated + (self.custom_opening_balance or 0),
			from_date=self.from_date,
			to_date=self.to_date,
			is_carry_forward=0,
		)
		create_leave_ledger_entry(self, args, submit)