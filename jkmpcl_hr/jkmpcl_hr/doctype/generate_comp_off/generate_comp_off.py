# Copyright (c) 2026, SanskarTechnolab and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from jkmpcl_hr.py.scheduler_method import process_comp_off_scheduler, process_comp_off_by_branch

class GenerateCompOff(Document):
	
	@frappe.whitelist()
	def generate_comp_off(self):
		if not self.generate_for_date:
			frappe.throw("Please select Date first")

		if frappe.session.user != "Administrator":
			process_comp_off_by_branch(comp_off_date=self.generate_for_date)
		else:
			process_comp_off_scheduler(comp_off_date=self.generate_for_date)
	
		return {
            "success": True,
            "message": f"CompOff Generated for {self.generate_for_date}"
        }