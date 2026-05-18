# import frappe
# from frappe.model.document import Document
# from jkmpcl_hr.py.scheduler_method import run_attendance_for_my_branch, run_daily_attendance


# class MarkAttendance(Document):

#     @frappe.whitelist()
#     def mark_attendance_now(self):

#         if not self.attendance_date:
#             frappe.throw("Please select Attendance Date first")

#         # ✅ STEP 1: Suspended Attendance
#         self.create_suspended_attendance(self.attendance_date)

#         # ✅ STEP 2: Normal Attendance
#         if frappe.session.user != "Administrator":
#             run_attendance_for_my_branch(att_date=self.attendance_date)
#         else:
#             run_daily_attendance(att_date=self.attendance_date)

#         return {
#             "success": True,
#             "message": f"Attendance processed for {self.attendance_date}"
#         }

#     def create_suspended_attendance(self, att_date):

#         suspended_employees = frappe.db.sql("""
#             SELECT DISTINCT employee
#             FROM `tabSuspended Employee Log`
#             WHERE from_date <= %s
#             AND (to_date IS NULL OR to_date >= %s)
#         """, (att_date, att_date), as_dict=True)

#         for row in suspended_employees:
#             employee = row.employee

#             existing = frappe.db.exists("Attendance", {
#                 "employee": employee,
#                 "attendance_date": att_date,
#                 "docstatus": ["!=", 2]
#             })

#             if existing:
#                 # ❗ Only update if not already Suspended
#                 current_status = frappe.db.get_value("Attendance", existing, "status")

#                 if current_status != "Suspended":
#                     frappe.db.set_value(
#                         "Attendance",
#                         existing,
#                         "status",
#                         "Suspended",
#                         update_modified=False
#                     )

#             else:
#                 emp_details = frappe.db.get_value(
#                     "Employee",
#                     employee,
#                     ["employee_name", "department", "company", "branch"],
#                     as_dict=True
#                 )

#                 att = frappe.get_doc({
#                     "doctype": "Attendance",
#                     "employee": employee,
#                     "employee_name": emp_details.employee_name,
#                     "department": emp_details.department,
#                     "company": emp_details.company,
#                     "attendance_date": att_date,
#                     "status": "Suspended",
#                     "custom_branch": emp_details.branch,
#                     "custom_penalty_leave_type": "Leave Without Pay",
#                     "custom_penalty_leave_count": -1.0,
#                     "custom_is_penalize": 1
#                 })

#                 att.insert(ignore_permissions=True)
#                 att.submit()

#         frappe.db.commit()


# import frappe
# from frappe.model.document import Document
# from frappe.utils import formatdate
# from jkmpcl_hr.py.scheduler_method import run_attendance_for_my_branch, run_daily_attendance


# class MarkAttendance(Document):

#     @frappe.whitelist()
#     def mark_attendance_now(self):

#         # ==============================
#         # 🔒 Attendance Lock (MAIN CONTROL)
#         # ==============================
#         # Skip lock check if user has permission
#         if not frappe.has_permission(
#             "Mark Attendance",
#             user=frappe.session.user
#         ):
#             lock_name = frappe.db.get_value(
#                 "Attendance Lock",
#                 {
#                     "from_date": ["<=", self.attendance_date],
#                     "to_date": [">=", self.attendance_date],
#                     "docstatus": ["!=", 2]
#                 }
#             )

#             if lock_name:
#                 month_name = frappe.utils.formatdate(
#                     self.attendance_date,
#                     "MMMM"
#                 )

#                 frappe.throw(
#                     f"Attendance is locked for {month_name}. Cannot process attendance."
#                 )

#         # ==============================
#         # ✅ NORMAL FLOW
#         # ==============================

#         # STEP 1: Suspended Attendance
#         self.create_suspended_attendance(self.attendance_date)

#         # STEP 2: Normal Attendance
#         if frappe.session.user != "Administrator":
#             run_attendance_for_my_branch(att_date=self.attendance_date)
#         else:
#             run_daily_attendance(att_date=self.attendance_date)

#         return {
#             "success": True,
#             "message": f"Attendance processed for {self.attendance_date}"
#         }

#     # ==========================================================
#     # Suspended Attendance
#     # ==========================================================
#     def create_suspended_attendance(self, att_date):

#         suspended_employees = frappe.db.sql("""
#             SELECT DISTINCT employee
#             FROM `tabSuspended Employee Log`
#             WHERE from_date <= %s
#             AND (to_date IS NULL OR to_date >= %s)
#         """, (att_date, att_date), as_dict=True)

#         for row in suspended_employees:
#             employee = row.employee

#             existing = frappe.db.exists("Attendance", {
#                 "employee": employee,
#                 "attendance_date": att_date,
#                 "docstatus": ["!=", 2]
#             })

#             if existing:
#                 current_status = frappe.db.get_value("Attendance", existing, "status")

#                 if current_status != "Suspended":
#                     frappe.db.set_value(
#                         "Attendance",
#                         existing,
#                         "status",
#                         "Suspended",
#                         update_modified=False
#                     )

#             else:
#                 emp_details = frappe.db.get_value(
#                     "Employee",
#                     employee,
#                     ["employee_name", "department", "company", "branch"],
#                     as_dict=True
#                 )

#                 att = frappe.get_doc({
#                     "doctype": "Attendance",
#                     "employee": employee,
#                     "employee_name": emp_details.employee_name,
#                     "department": emp_details.department,
#                     "company": emp_details.company,
#                     "attendance_date": att_date,
#                     "status": "Suspended",
#                     "custom_branch": emp_details.branch,
#                     "custom_penalty_leave_type": "Leave Without Pay",
#                     "custom_penalty_leave_count": -1.0,
#                     "custom_is_penalize": 1
#                 })

#                 att.insert(ignore_permissions=True)
#                 att.submit()

#         frappe.db.commit()

import frappe
from frappe.model.document import Document
from frappe.utils import formatdate
from jkmpcl_hr.py.scheduler_method import (
    run_attendance_for_my_branch,
    run_daily_attendance
)


class MarkAttendance(Document):

    @frappe.whitelist()
    def mark_attendance_now(self):

        try:
            frappe.flags.ignore_permissions = True

            if not self.attendance_date:
                frappe.throw("Please select Attendance Date first")

            # ==================================================
            # 🔒 Attendance Lock Check
            # ==================================================
            lock = frappe.db.get_value(
                "Attendance Lock",
                {
                    "from_date": ["<=", self.attendance_date],
                    "to_date": [">=", self.attendance_date],
                    "docstatus": ["!=", 2]
                },
                ["name", "branch"],
                as_dict=True
            )

            if lock:

                # ==========================================
                # Current User Roles
                # ==========================================
                user_roles = frappe.get_roles(
                    frappe.session.user
                )

                # ==========================================
                # Roles having WRITE permission
                # on Mark Attendance
                # ==========================================
                mark_attendance_roles = frappe.get_all(
                    "Custom DocPerm",
                    filters={
                        "parent": "Mark Attendance",
                        "write": 1
                    },
                    pluck="role"
                )

                # ==========================================
                # User roles which can mark attendance
                # ==========================================
                user_mark_roles = [
                    role for role in user_roles
                    if role in mark_attendance_roles
                ]

                # ==========================================
                # Locked Roles
                # ==========================================
                locked_roles = frappe.get_all(
                    "Attendance Lock Table",
                    filters={
                        "parent": lock.name
                    },
                    pluck="role"
                )

                # ==========================================
                # Available Roles
                # ==========================================
                available_roles = [
                    role for role in user_mark_roles
                    if role not in locked_roles
                ]

                # ==========================================
                # Current User Employee Branch
                # ==========================================
                employee = frappe.db.get_value(
                    "Employee",
                    {
                        "user_id": frappe.session.user
                    },
                    ["name", "branch"],
                    as_dict=True
                )

                user_branch = employee.branch if employee else None

                # ==========================================
                # BLOCK CONDITION
                # ==========================================
                # Block only when:
                # 1. User has no available role
                # 2. User branch matches lock branch
                # ==========================================
                if (
                    not available_roles
                    and lock.branch
                    and user_branch == lock.branch
                ):

                    month_name = formatdate(
                        self.attendance_date,
                        "MMMM"
                    )

                    frappe.throw(
                        f"Attendance is locked for branch {user_branch} in {month_name}. Cannot process attendance."
                    )

            # ==================================================
            # ✅ STEP 1: Suspended Attendance
            # ==================================================
            self.create_suspended_attendance(
                self.attendance_date
            )

            # ==================================================
            # ✅ STEP 2: Normal Attendance
            # ==================================================
            if frappe.session.user != "Administrator":

                run_attendance_for_my_branch(
                    att_date=self.attendance_date
                )

            else:

                run_daily_attendance(
                    att_date=self.attendance_date
                )

            frappe.db.commit()

            frappe.clear_messages()

            return {
                "success": True,
                "message": f"Attendance processed for {self.attendance_date}"
            }

        except frappe.ValidationError:
            raise

        except Exception:

            frappe.log_error(
                frappe.get_traceback(),
                "Mark Attendance Error"
            )

            frappe.throw(
                "Something went wrong while processing attendance."
            )

        finally:

            frappe.flags.ignore_permissions = False

    # ==========================================================
    # Suspended Attendance
    # ==========================================================
    def create_suspended_attendance(self, att_date):

        suspended_employees = frappe.db.sql("""
            SELECT DISTINCT employee
            FROM `tabSuspended Employee Log`
            WHERE from_date <= %s
            AND (to_date IS NULL OR to_date >= %s)
        """, (att_date, att_date), as_dict=True)

        for row in suspended_employees:

            employee = row.employee

            existing = frappe.db.exists(
                "Attendance",
                {
                    "employee": employee,
                    "attendance_date": att_date,
                    "docstatus": ["!=", 2]
                }
            )

            if existing:

                current_status = frappe.db.get_value(
                    "Attendance",
                    existing,
                    "status"
                )

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
                    [
                        "employee_name",
                        "department",
                        "company",
                        "branch"
                    ],
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

                try:

                    att.insert(ignore_permissions=True)
                    att.submit(ignore_permissions=True)

                except Exception:

                    frappe.log_error(
                        frappe.get_traceback(),
                        f"Attendance Submit Error - {employee}"
                    )

                    raise

        frappe.db.commit()