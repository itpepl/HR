import frappe
from frappe.model.document import Document
from jkmpcl_hr.py.scheduler_method import run_attendance_for_my_branch, run_daily_attendance


class MarkAttendance(Document):

    @frappe.whitelist()
    def mark_attendance_now(self):

        if not self.attendance_date:
            frappe.throw("Please select Attendance Date first")

        # ✅ STEP 1: Suspended Attendance
        self.create_suspended_attendance(self.attendance_date)

        # ✅ STEP 2: Normal Attendance
        if frappe.session.user != "Administrator":
            run_attendance_for_my_branch(att_date=self.attendance_date)
        else:
            run_daily_attendance(att_date=self.attendance_date)

        return {
            "success": True,
            "message": f"Attendance processed for {self.attendance_date}"
        }

    def create_suspended_attendance(self, att_date):

        suspended_employees = frappe.db.sql("""
            SELECT DISTINCT employee
            FROM `tabSuspended Employee Log`
            WHERE from_date <= %s
            AND (to_date IS NULL OR to_date >= %s)
        """, (att_date, att_date), as_dict=True)

        for row in suspended_employees:
            employee = row.employee

            existing = frappe.db.exists("Attendance", {
                "employee": employee,
                "attendance_date": att_date,
                "docstatus": ["!=", 2]
            })

            if existing:
                # ❗ Only update if not already Suspended
                current_status = frappe.db.get_value("Attendance", existing, "status")

                if current_status != "Suspended":
                    frappe.db.set_value(
                        "Attendance",
                        existing,
                        "status",
                        "Suspended",
                        update_modified=False
                    )

            else:
                emp_details = frappe.db.get_value(
                    "Employee",
                    employee,
                    ["employee_name", "department", "company", "branch"],
                    as_dict=True
                )

                att = frappe.get_doc({
                    "doctype": "Attendance",
                    "employee": employee,
                    "employee_name": emp_details.employee_name,
                    "department": emp_details.department,
                    "company": emp_details.company,
                    "attendance_date": att_date,
                    "status": "Suspended",
                    "custom_branch": emp_details.branch,
                    "custom_penalty_leave_type": "Leave Without Pay",
                    "custom_penalty_leave_count": -1.0,
                    "custom_is_penalize": 1
                })

                att.insert(ignore_permissions=True)
                att.submit()

        frappe.db.commit()