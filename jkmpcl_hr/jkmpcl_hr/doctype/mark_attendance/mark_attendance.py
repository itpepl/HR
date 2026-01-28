# Copyright (c) 2026, SanskarTechnolab and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from jkmpcl_hr.py.scheduler_method import run_attendance_for_my_branch

# class MarkAttendance(Document):
# 	pass

class MarkAttendance(Document):

    @frappe.whitelist()
    def mark_attendance_now(self):
        if not self.attendance_date:
            frappe.throw("Please select Attendance Date first")

        # Call scheduler logic manually
        run_attendance_for_my_branch(att_date=self.attendance_date)

        return {
            "success": True,
            "message": f"Attendance processed for {self.attendance_date}"
        }
        
    