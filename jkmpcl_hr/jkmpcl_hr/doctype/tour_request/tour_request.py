# import frappe
# from frappe import _
# from frappe.model.document import Document
# from frappe.utils import date_diff, add_days,formatdate
# from jkmpcl_hr.jkmpcl_hr.doctype.attendance_lock.attendance_lock import AttendanceLock

# class TourRequest(Document):
    
#     def validate(self):
#         # Mandatory field validation
#         if not self.from_date:
#             frappe.throw(_("From Date is mandatory"))

#         if not self.to_date:
#             frappe.throw(_("To Date is mandatory"))

#         if not self.purpose_of_travel:
#             frappe.throw(_("Purpose of Travel is mandatory"))

#         # To Date cannot be earlier than From Date
#         if self.to_date < self.from_date:
#             frappe.throw(_("To Date cannot be earlier than From Date"))

#         # Calculate No. of Days
#         self.no_of_days = date_diff(self.to_date, self.from_date) + 1

#         # Check overlapping Tour Request
#         existing_tour = frappe.db.sql("""
#             SELECT name
#             FROM `tabTour Request`
#             WHERE employee = %s
#                 AND name != %s
#                 AND docstatus != 2
#                 AND from_date <= %s
#                 AND to_date >= %s
#             LIMIT 1
#         """, (
#             self.employee,
#             self.name or "",
#             self.to_date,
#             self.from_date
#         ), as_dict=True)

#         if existing_tour:
#             frappe.throw(
#                 _("Tour Request already exists for this date range: {0}").format(
#                     existing_tour[0].name
#                 )
#             )

#         # Attendance Lock Validation for Travel Request Date
#         if self.travel_request_date:
#             lock_name = AttendanceLock.is_attendance_locked(
#                 self.travel_request_date,
#                 self.employee
#             )

#             if lock_name:
#                 month = frappe.db.get_value(
#                     "Attendance Lock",
#                     lock_name,
#                     "month"
#                 )

#                 if not month:
#                     month = formatdate(
#                         self.travel_request_date,
#                         "MMMM yyyy"
#                     )

#                 frappe.throw(
#                     _("Attendance is locked for {0}. Travel Request Date is not allowed.").format(month),
#                     title=_("Attendance Lock")
#                 )

#         # Attendance Lock Validation for Tour Period
#         for i in range(date_diff(self.to_date, self.from_date) + 1):
#             att_date = add_days(self.from_date, i)

#             lock_name = AttendanceLock.is_attendance_locked(
#                 att_date,
#                 self.employee
#             )

#             if lock_name:
#                 month = frappe.db.get_value(
#                     "Attendance Lock",
#                     lock_name,
#                     "month"
#                 )

#                 if not month:
#                     month = formatdate(
#                         att_date,
#                         "MMMM yyyy"
#                     )

#                 frappe.throw(
#                     _("Attendance is locked for {0}. Tour Request cannot be created or updated for this period.").format(month),
#                     title=_("Attendance Lock")
#                 )

                
#     def on_submit(self):
#         if self.workflow_state != "Approved by HR":
#             return
        
#         total_days = date_diff(self.to_date, self.from_date) + 1
        
#         for i in range(total_days):
#             att_date = add_days(self.from_date, i)
            
#             if frappe.db.exists(
#                 "Attendance",
#                 {
#                     "employee": self.employee,
#                     "attendance_date": att_date
#                 }
#             ):
#                 continue
            
#             employee_details = frappe.db.get_value(
#                 "Employee",
#                 self.employee,
#                 ["employee_name", "department", "company", "branch"],
#                 as_dict=True
#             )
            
#             att = frappe.get_doc({
#                 "doctype": "Attendance",
#                 "employee": self.employee,
#                 "employee_name": employee_details.employee_name,
#                 "department": employee_details.department,
#                 "company": employee_details.company,
#                 "attendance_date": att_date,
#                 "status": "Present",
#                 "custom_branch": employee_details.branch,
#                 "custom_remark": "On Duty"
#             })
            
#             att.insert(ignore_permissions=True)
#             att.submit()
    

#     def on_cancel(self):
#         self.db_set("workflow_state", "Cancelled")
#         total_days = date_diff(self.to_date, self.from_date) + 1

#         employee_doc = frappe.get_doc("Employee", self.employee)

#         for i in range(total_days):
#             att_date = add_days(self.from_date, i)

#             attendance_list = frappe.get_all(
#                 "Attendance",
#                 filters={
#                     "employee": self.employee,
#                     "attendance_date": att_date,
#                     "custom_remark": "On Duty",
#                     "docstatus": 1
#                 },
#                 pluck="name"
#             )

#             for att_name in attendance_list:
#                 old_att = frappe.get_doc("Attendance", att_name)

#                 company = old_att.company
#                 branch = old_att.custom_branch
#                 shift = old_att.shift

#                 # Cancel and delete On Duty attendance
#                 old_att.cancel()
#                 old_att.delete(ignore_permissions=True)

#                 # Check if attendance already exists
#                 if not frappe.db.exists(
#                     "Attendance",
#                     {
#                         "employee": self.employee,
#                         "attendance_date": att_date
#                     }
#                 ):
#                     # Create Absent Attendance
#                     new_att = frappe.new_doc("Attendance")
#                     new_att.employee = self.employee
#                     new_att.employee_name = employee_doc.employee_name
#                     new_att.attendance_date = att_date
#                     new_att.company = company
#                     new_att.custom_branch = branch
#                     new_att.shift = shift
#                     new_att.status = "Absent"

#                     # Penalty fields
#                     new_att.custom_is_penalize = 1
#                     new_att.custom_penalty_leave_type = "Leave Without Pay"
#                     new_att.custom_penalty_leave_count = -1
#                     new_att.custom_remark = "Tour Request Cancel"

#                     new_att.insert(ignore_permissions=True)
#                     new_att.submit()

#                     # Create Leave Ledger Entry
#                     lle = frappe.new_doc("Leave Ledger Entry")
#                     lle.employee = self.employee
#                     lle.employee_name = employee_doc.employee_name
#                     lle.leave_type = "Leave Without Pay"
#                     lle.from_date = att_date
#                     lle.to_date = att_date
#                     lle.company = company
#                     lle.custom_branch = branch
#                     lle.transaction_type = "Leave Application"
#                     lle.leaves = -1
#                     lle.is_leave_without_pay = 1
#                     lle.custom_is_penalty = 1
#                     lle.custom_attendance = new_att.name

#                     lle.insert(ignore_permissions=True)
#                     lle.submit()

#         frappe.db.commit()



import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, add_days, formatdate, today
from jkmpcl_hr.jkmpcl_hr.doctype.attendance_lock.attendance_lock import AttendanceLock

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

        # Calculate No. of Days
        self.no_of_days = date_diff(self.to_date, self.from_date) + 1

        # Validate travel duration is at least 2 days
        if self.no_of_days < 2:
            frappe.throw(_("Travel request cannot be less than 2 days."))

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

        # Attendance Lock Validation for Travel Request Date
        if self.travel_request_date:
            lock_name = AttendanceLock.is_attendance_locked(
                self.travel_request_date,
                self.employee
            )

            if lock_name:
                month = frappe.db.get_value(
                    "Attendance Lock",
                    lock_name,
                    "month"
                )

                if not month:
                    month = formatdate(
                        self.travel_request_date,
                        "MMMM yyyy"
                    )

                frappe.throw(
                    _("Attendance is locked for {0}. Travel Request Date is not allowed.").format(month),
                    title=_("Attendance Lock")
                )

        # Attendance Lock Validation for Tour Period
        for i in range(date_diff(self.to_date, self.from_date) + 1):
            att_date = add_days(self.from_date, i)

            lock_name = AttendanceLock.is_attendance_locked(
                att_date,
                self.employee
            )

            if lock_name:
                month = frappe.db.get_value(
                    "Attendance Lock",
                    lock_name,
                    "month"
                )

                if not month:
                    month = formatdate(
                        att_date,
                        "MMMM yyyy"
                    )

                frappe.throw(
                    _("Attendance is locked for {0}. Tour Request cannot be created or updated for this period.").format(month),
                    title=_("Attendance Lock")
                )

                
    def on_submit(self):
        if self.workflow_state != "Approved by HR":
            return
        
        total_days = date_diff(self.to_date, self.from_date) + 1
        today_date = today()
        
        for i in range(total_days):
            att_date = add_days(self.from_date, i)
            
            # Check if attendance already exists
            existing_att = frappe.db.get_value(
                "Attendance",
                {
                    "employee": self.employee,
                    "attendance_date": att_date
                },
                ["name", "custom_is_penalize", "status"],
                as_dict=True
            )
            
            if existing_att:
                # If it's a past date and has penalty, remove the penalty
                if att_date <= today_date and existing_att.custom_is_penalize == 1:
                    try:
                        # Get and delete Leave Ledger Entry
                        lle = frappe.db.get_value(
                            "Leave Ledger Entry",
                            {
                                "employee": self.employee,
                                "from_date": att_date,
                                "to_date": att_date,
                                "custom_attendance": existing_att.name,
                                "docstatus": 1
                            },
                            "name"
                        )
                        
                        if lle:
                            lle_doc = frappe.get_doc("Leave Ledger Entry", lle)
                            if lle_doc.docstatus == 1:
                                lle_doc.cancel()
                            lle_doc.delete(ignore_permissions=True)
                            frappe.db.commit()
                        
                        # Update attendance - remove penalty flags
                        frappe.db.set_value(
                            "Attendance",
                            existing_att.name,
                            {
                                "custom_is_penalize": 0,
                                "custom_penalty_leave_type": None,
                                "custom_penalty_leave_count": 0,
                                "custom_remark": "On Duty"
                            }
                        )
                        frappe.db.commit()
                        
                    except Exception as e:
                        frappe.log_error(f"Error removing penalty for attendance {existing_att.name}: {str(e)}", "Tour Submit")
                
                continue
            
            # No attendance exists, create new Present attendance
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
            frappe.db.commit()
    

    def on_cancel(self):
        # Set workflow state to Cancelled
        self.db_set("workflow_state", "Cancelled")
        
        total_days = date_diff(self.to_date, self.from_date) + 1
        employee_doc = frappe.get_doc("Employee", self.employee)

        for i in range(total_days):
            att_date = add_days(self.from_date, i)

            # Get all On Duty attendance records
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
                old_att = frappe.get_doc("Attendance", att_name)
                
                company = old_att.company
                branch = old_att.custom_branch
                shift = old_att.shift

                # Get and delete related Leave Ledger Entries if any
                leave_ledger_entries = frappe.get_all(
                    "Leave Ledger Entry",
                    filters={
                        "employee": self.employee,
                        "from_date": att_date,
                        "to_date": att_date,
                        "custom_attendance": att_name,
                        "docstatus": 1
                    },
                    pluck="name"
                )

                # Cancel and delete Leave Ledger Entries
                for lle_name in leave_ledger_entries:
                    try:
                        lle = frappe.get_doc("Leave Ledger Entry", lle_name)
                        if lle.docstatus == 1:
                            lle.cancel()
                        lle.delete(ignore_permissions=True)
                        frappe.db.commit()
                    except Exception as e:
                        frappe.log_error(f"Error deleting LLE {lle_name}: {str(e)}", "Tour Cancel")

                # Cancel and delete On Duty attendance
                old_att.cancel()
                old_att.delete(ignore_permissions=True)
                frappe.db.commit()

                # Check if attendance already exists
                if not frappe.db.exists(
                    "Attendance",
                    {
                        "employee": self.employee,
                        "attendance_date": att_date
                    }
                ):
                    # Create Absent Attendance
                    new_att = frappe.new_doc("Attendance")
                    new_att.employee = self.employee
                    new_att.employee_name = employee_doc.employee_name
                    new_att.attendance_date = att_date
                    new_att.company = company
                    new_att.custom_branch = branch
                    new_att.shift = shift
                    new_att.status = "Absent"

                    # Penalty fields
                    new_att.custom_is_penalize = 1
                    new_att.custom_penalty_leave_type = "Leave Without Pay"
                    new_att.custom_penalty_leave_count = -1
                    new_att.custom_remark = "Tour Request Cancel"

                    new_att.insert(ignore_permissions=True)
                    new_att.submit()
                    frappe.db.commit()

                    # Create Leave Ledger Entry
                    lle = frappe.new_doc("Leave Ledger Entry")
                    lle.employee = self.employee
                    lle.employee_name = employee_doc.employee_name
                    lle.leave_type = "Leave Without Pay"
                    lle.from_date = att_date
                    lle.to_date = att_date
                    lle.company = company
                    lle.custom_branch = branch
                    lle.transaction_type = "Leave Application"
                    lle.leaves = -1
                    lle.is_leave_without_pay = 1
                    lle.custom_is_penalty = 1
                    lle.custom_attendance = new_att.name

                    lle.insert(ignore_permissions=True)
                    lle.submit()
                    frappe.db.commit()

        # Final commit
        frappe.db.commit()
        frappe.msgprint(_("Tour Request cancelled successfully. Attendance and Leave Ledger entries have been updated."))