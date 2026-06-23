# import frappe
# from frappe import _
# from frappe.model.document import Document
# from frappe.utils import date_diff, add_days, formatdate, today,getdate
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

#         # Validate travel duration is at least 2 days
#         if self.no_of_days < 2:
#             frappe.throw(_("Travel request cannot be less than 2 days."))

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
#         # Validate employee suspension status

#         self.validate_employee_suspension()

#     def validate_employee_suspension(self):
#         """
#         Validate that the employee is not suspended before allowing Tour Request creation
#         """
#         if not self.employee:
#             return
        
#         # Get employee details
#         employee_data = frappe.db.get_value(
#             "Employee",
#             self.employee,
#             ["employee_name", "status", "custom_suspended_from_date", "custom_suspended_to_date"],
#             as_dict=True
#         )
        
#         if not employee_data:
#             return
        
#         # Check if employee is suspended
#         if employee_data.status == "Suspended":
#             frappe.throw("Tour Request cannot be created. Employee is currently suspended")
        
#         if employee_data.custom_suspended_from_date:
#             suspended_from = employee_data.get("custom_suspended_from_date")
#             suspended_to = employee_data.get("custom_suspended_to_date")
            
#             # Convert all dates to string format for comparison
#             current_date = today()
            
#             # Convert suspension dates to string if they are date objects
#             if suspended_from and hasattr(suspended_from, 'strftime'):
#                 suspended_from = suspended_from.strftime('%Y-%m-%d')
#             if suspended_to and hasattr(suspended_to, 'strftime'):
#                 suspended_to = suspended_to.strftime('%Y-%m-%d')
            
#             # Check if current date falls within suspension period
#             is_suspended = False
            
#             if suspended_from and suspended_to:
#                 if current_date >= suspended_from and current_date <= suspended_to:
#                     is_suspended = True
#             elif suspended_from and not suspended_to:
#                 if current_date >= suspended_from:
#                     is_suspended = True
            
#             if is_suspended:
#                 from_date_str = formatdate(suspended_from) if suspended_from else "N/A"
#                 to_date_str = formatdate(suspended_to) if suspended_to else "Ongoing"
                
#                 frappe.throw(
#                     _("Tour Request cannot be created. Employee {0} is currently suspended from {1} to {2}.").format(
#                         employee_data.employee_name,
#                         from_date_str,
#                         to_date_str
#                     )
#                 )
            
#             # Also check if any travel date falls within suspension period
#             if self.from_date and self.to_date:
#                 total_days = date_diff(self.to_date, self.from_date) + 1
                
#                 for i in range(total_days):
#                     travel_date = add_days(self.from_date, i)
                    
#                     # Convert travel date to string if it's a date object
#                     if hasattr(travel_date, 'strftime'):
#                         travel_date = travel_date.strftime('%Y-%m-%d')
                    
#                     is_date_suspended = False
                    
#                     if suspended_from and suspended_to:
#                         if travel_date >= suspended_from and travel_date <= suspended_to:
#                             is_date_suspended = True
#                     elif suspended_from and not suspended_to:
#                         if travel_date >= suspended_from:
#                             is_date_suspended = True
                    
#                     if is_date_suspended:
#                         from_date_str = formatdate(suspended_from) if suspended_from else "N/A"
#                         to_date_str = formatdate(suspended_to) if suspended_to else "Ongoing"
#                         travel_date_str = formatdate(travel_date)
                        
#                         frappe.throw(
#                             _("Tour Request cannot be created. Employee {0} is suspended from {1} to {2}. Travel date {3} falls within suspension period.").format(
#                                 employee_data.employee_name,
#                                 from_date_str,
#                                 to_date_str,
#                                 travel_date_str
#                             )
#                         )            
#     def on_submit(self):
#         if self.workflow_state != "Approved by HR":
#             return
        
#         total_days = date_diff(self.to_date, self.from_date) + 1
#         today_date = today()
        
#         for i in range(total_days):
#             att_date = add_days(self.from_date, i)
            
#             # Check if attendance already exists
#             existing_att = frappe.db.get_value(
#                 "Attendance",
#                 {
#                     "employee": self.employee,
#                     "attendance_date": att_date
#                 },
#                 ["name", "custom_is_penalize", "status"],
#                 as_dict=True
#             )
            
#             if existing_att:
#                 # If it's a past date and has penalty, remove the penalty
#                 # if att_date <= today_date and existing_att.custom_is_penalize == 1:
#                 if att_date <= getdate(today_date) and existing_att.custom_is_penalize == 1:
#                     try:
#                         # Get and delete Leave Ledger Entry
#                         lle = frappe.db.get_value(
#                             "Leave Ledger Entry",
#                             {
#                                 "employee": self.employee,
#                                 "from_date": att_date,
#                                 "to_date": att_date,
#                                 "custom_attendance": existing_att.name,
#                                 "docstatus": 1
#                             },
#                             "name"
#                         )
                        
#                         if lle:
#                             lle_doc = frappe.get_doc("Leave Ledger Entry", lle)
#                             if lle_doc.docstatus == 1:
#                                 lle_doc.cancel()
#                             lle_doc.delete(ignore_permissions=True)
#                             frappe.db.commit()
                        
#                         # Update attendance - remove penalty flags
#                         frappe.db.set_value(
#                             "Attendance",
#                             existing_att.name,
#                             {
#                                 "custom_is_penalize": 0,
#                                 "custom_penalty_leave_type": None,
#                                 "custom_penalty_leave_count": "",
#                                 "custom_remark": "On Duty",
#                                 "status":"Present"
#                             }
#                         )
#                         frappe.db.commit()
                        
#                     except Exception as e:
#                         frappe.log_error(f"Error removing penalty for attendance {existing_att.name}: {str(e)}", "Tour Submit")
                
#                 continue
            
#             # No attendance exists, create new Present attendance
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
#             frappe.db.commit()
    

#     def on_cancel(self):
#         # Set workflow state to Cancelled
#         self.db_set("workflow_state", "Cancelled")
        
#         total_days = date_diff(self.to_date, self.from_date) + 1
#         employee_doc = frappe.get_doc("Employee", self.employee)

#         for i in range(total_days):
#             att_date = add_days(self.from_date, i)

#             # Get all On Duty attendance records
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

#                 # Get and delete related Leave Ledger Entries if any
#                 leave_ledger_entries = frappe.get_all(
#                     "Leave Ledger Entry",
#                     filters={
#                         "employee": self.employee,
#                         "from_date": att_date,
#                         "to_date": att_date,
#                         "custom_attendance": att_name,
#                         "docstatus": 1
#                     },
#                     pluck="name"
#                 )

#                 # Cancel and delete Leave Ledger Entries
#                 for lle_name in leave_ledger_entries:
#                     try:
#                         lle = frappe.get_doc("Leave Ledger Entry", lle_name)
#                         if lle.docstatus == 1:
#                             lle.cancel()
#                         lle.delete(ignore_permissions=True)
#                         frappe.db.commit()
#                     except Exception as e:
#                         frappe.log_error(f"Error deleting LLE {lle_name}: {str(e)}", "Tour Cancel")

#                 # Cancel and delete On Duty attendance
#                 old_att.cancel()
#                 old_att.delete(ignore_permissions=True)
#                 frappe.db.commit()

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
#                     frappe.db.commit()

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
#                     frappe.db.commit()

#         # Final commit
#         frappe.db.commit()
#         frappe.msgprint(_("Tour Request cancelled successfully. Attendance and Leave Ledger entries have been updated."))


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, add_days, formatdate, today, getdate,datetime
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
        # Validate employee suspension status

        self.validate_employee_suspension()

    def validate_employee_suspension(self):
        """
        Validate that the employee is not suspended before allowing Tour Request creation
        """
        if not self.employee:
            return
        
        # Get employee details
        employee_data = frappe.db.get_value(
            "Employee",
            self.employee,
            ["employee_name", "status", "custom_suspended_from_date", "custom_suspended_to_date"],
            as_dict=True
        )
        
        if not employee_data:
            return
        
        # Check if employee is suspended
        if employee_data.status == "Suspended":
            frappe.throw("Tour Request cannot be created. Employee is currently suspended")
        
        if employee_data.custom_suspended_from_date:
            suspended_from = employee_data.get("custom_suspended_from_date")
            suspended_to = employee_data.get("custom_suspended_to_date")
            
            # Convert all dates to string format for comparison
            current_date = today()
            
            # Convert suspension dates to string if they are date objects
            if suspended_from and hasattr(suspended_from, 'strftime'):
                suspended_from = suspended_from.strftime('%Y-%m-%d')
            if suspended_to and hasattr(suspended_to, 'strftime'):
                suspended_to = suspended_to.strftime('%Y-%m-%d')
            
            # Check if current date falls within suspension period
            is_suspended = False
            
            if suspended_from and suspended_to:
                if current_date >= suspended_from and current_date <= suspended_to:
                    is_suspended = True
            elif suspended_from and not suspended_to:
                if current_date >= suspended_from:
                    is_suspended = True
            
            if is_suspended:
                from_date_str = formatdate(suspended_from) if suspended_from else "N/A"
                to_date_str = formatdate(suspended_to) if suspended_to else "Ongoing"
                
                frappe.throw(
                    _("Tour Request cannot be created. Employee {0} is currently suspended from {1} to {2}.").format(
                        employee_data.employee_name,
                        from_date_str,
                        to_date_str
                    )
                )
            
            # Also check if any travel date falls within suspension period
            if self.from_date and self.to_date:
                total_days = date_diff(self.to_date, self.from_date) + 1
                
                for i in range(total_days):
                    travel_date = add_days(self.from_date, i)
                    
                    # Convert travel date to string if it's a date object
                    if hasattr(travel_date, 'strftime'):
                        travel_date = travel_date.strftime('%Y-%m-%d')
                    
                    is_date_suspended = False
                    
                    if suspended_from and suspended_to:
                        if travel_date >= suspended_from and travel_date <= suspended_to:
                            is_date_suspended = True
                    elif suspended_from and not suspended_to:
                        if travel_date >= suspended_from:
                            is_date_suspended = True
                    
                    if is_date_suspended:
                        from_date_str = formatdate(suspended_from) if suspended_from else "N/A"
                        to_date_str = formatdate(suspended_to) if suspended_to else "Ongoing"
                        travel_date_str = formatdate(travel_date)
                        
                        frappe.throw(
                            _("Tour Request cannot be created. Employee {0} is suspended from {1} to {2}. Travel date {3} falls within suspension period.").format(
                                employee_data.employee_name,
                                from_date_str,
                                to_date_str,
                                travel_date_str
                            )
                        )

    def get_holidays_between_dates(self, employee, from_date, to_date):
        """
        Get all holidays (including Restricted Holidays) between two dates
        Fetches the latest holiday list from Holiday List Assignment doctype
        """
        holidays = []
        
        # Get the latest holiday list from Holiday List Assignment doctype
        # Using "applicable_for" as the field name (links to Employee)
        latest_assignment = frappe.get_all(
            "Holiday List Assignment",
            filters={
                "applicable_for": employee
            },
            fields=["holiday_list", "from_date", "holiday_list_start", "holiday_list_end"],
            order_by="creation desc",
            limit=1
        )
        
        holiday_list_name = latest_assignment[0].holiday_list if latest_assignment else None
        
        if not holiday_list_name:
            frappe.log_error(
                f"No holiday list found for employee {employee} in Holiday List Assignment",
                "Tour Request Comp-Off"
            )
            frappe.msgprint(_("No holiday list assigned to employee {0}. Please assign a holiday list.").format(
                frappe.db.get_value("Employee", employee, "employee_name")
            ))
            return holidays
        
        assignment = latest_assignment[0]
        
        # Check if the holiday list is valid for the tour date range
        if assignment.get("holiday_list_start") and assignment.get("holiday_list_end"):
            if from_date < assignment.holiday_list_start or to_date > assignment.holiday_list_end:
                frappe.msgprint(_(
                    "The assigned holiday list is valid from {0} to {1}. "
                    "Some tour dates may fall outside this period."
                ).format(
                    assignment.holiday_list_start,
                    assignment.holiday_list_end
                ), alert=True)
        
        # Get holidays from holiday list
        holiday_entries = frappe.get_all(
            "Holiday",
            filters={
                "parent": holiday_list_name,
                "holiday_date": ["between", [from_date, to_date]]
            },
            fields=["holiday_date", "weekly_off", "description"]
        )
        
        for entry in holiday_entries:
            holiday_date = entry.holiday_date
            
            # Check if it's a Restricted Holiday
            is_rh = frappe.db.exists(
                "Restricted Holiday",
                {
                    "holiday_date": holiday_date,
                    "holiday_list": holiday_list_name
                }
            )
            
            # Skip if already has leave allocation for this date
            if self.check_existing_comp_off_allocation(employee, holiday_date):
                frappe.log_error(
                    f"Compensatory Off already exists for {employee} on {holiday_date}",
                    "Tour Request Comp-Off"
                )
                continue
            
            if is_rh:
                holidays.append({
                    "date": holiday_date,
                    "type": "Restricted Holiday",
                    "description": entry.description or "Restricted Holiday"
                })
            elif entry.weekly_off == 1:
                holidays.append({
                    "date": holiday_date,
                    "type": "Week Off",
                    "description": entry.description or "Weekly Off"
                })
            else:
                holidays.append({
                    "date": holiday_date,
                    "type": "Holiday",
                    "description": entry.description or "Public Holiday"
                })
        
        return holidays
        


    def get_weekoffs_between_dates(self, employee, from_date, to_date):
        """
        Get all weekoffs between two dates (if not already covered by holidays)
        """
        weekoffs = []
        return weekoffs

    def get_employee_company(self, employee):
        """
        Get company for an employee
        """
        employee_doc = frappe.get_doc("Employee", employee)
        return employee_doc.company

    def get_employee_branch(self, employee):
        """
        Get branch/custom_branch for an employee
        """
        employee_doc = frappe.get_doc("Employee", employee)
        return employee_doc.get('branch')

    def check_existing_comp_off_allocation(self, employee, date):
        """
        Check if a Compensatory Off allocation already exists for the employee on given date
        """
        existing = frappe.db.exists(
            "Leave Allocation",
            {
                "employee": employee,
                "leave_type": "Compensatory Off",
                "from_date": date,
                "to_date": date,
                "docstatus": 1
            }
        )
        return existing

    def create_leave_allocation_entry(self, tour_req, off_day):
        """
        Create a Leave Allocation entry for Compensatory Off
        """
        try:
            # Get employee details
            employee_doc = frappe.get_doc("Employee", tour_req.employee)
            company = self.get_employee_company(tour_req.employee)
            branch = self.get_employee_branch(tour_req.employee)
            
            # Get the leave type "Compensatory Off"
            leave_type = frappe.get_value("Leave Type", {"name": "Compensatory Off"}, "name")
            if not leave_type:
                frappe.throw(_("Leave Type 'Compensatory Off' not found. Please create it first."))

            from_date = getdate(off_day["date"])
            to_date = add_days(from_date, 45)
            # Generate naming series for Leave Allocation
            naming_series = "HR-LAL-.YYYY.-"
            
            # Create Leave Allocation document
            leave_allocation = frappe.get_doc({
                "doctype": "Leave Allocation",
                "naming_series": naming_series,
                "employee": tour_req.employee,
                "employee_name": tour_req.employee_name,
                "company": company,
                "department": employee_doc.department,
                "leave_type": "Compensatory Off",
                "from_date": from_date,
                "to_date": to_date,
                "new_leaves_allocated": 1,
                "total_leaves_allocated": 1,
                "carry_forward": 0,
                "carry_forwarded_leaves_count": 0,
                "custom_branch": branch,
            })
            
            # # Add custom fields if they exist
            # if hasattr(leave_allocation, 'custom_tour_reference'):
            #     leave_allocation.custom_tour_reference = tour_req.name
            # if hasattr(leave_allocation, 'custom_off_day_type'):
            #     leave_allocation.custom_off_day_type = off_day["type"]
            
            # Insert the document
            leave_allocation.insert()
            
            # Submit the document
            leave_allocation.submit()
            
            frappe.log_error(
                f"Leave Allocation created: {leave_allocation.name} for {tour_req.employee} on {off_day['date']} ({off_day['type']})",
                "Tour Request Comp-Off Creation"
            )
            
            return leave_allocation
            
        except Exception as e:
            frappe.log_error(
                frappe.get_traceback(),
                f"Error creating Leave Allocation for {tour_req.name} - {off_day['date']}"
            )
            frappe.throw(_("Error creating Compensatory Off allocation: {0}").format(str(e)))
            return None

    def process_tour_request_comp_off(self, tour_req):
        """
        Process a single tour request to create leave allocations for holidays/weekoffs
        """
        created_allocations = []
        
        from_date = getdate(tour_req.from_date)
        to_date = getdate(tour_req.to_date)
        employee = tour_req.employee
        
        # Get all holidays between from_date and to_date
        holidays = self.get_holidays_between_dates(employee, from_date, to_date)
        
        # Get weekoffs between from_date and to_date
        weekoffs = self.get_weekoffs_between_dates(employee, from_date, to_date)
        
        # Combine all off-days
        all_off_days = holidays + weekoffs
        
        if not all_off_days:
            frappe.msgprint(_("No holidays or weekoffs found between the tour dates"))
            return created_allocations
        
        # Create leave allocation for each off-day
        for off_day in all_off_days:
            allocation = self.create_leave_allocation_entry(tour_req, off_day)
            if allocation:
                created_allocations.append(allocation.name)
        
        # Mark comp-off as created in tour request
        tour_req.comp_off_created = 1
        tour_req.save()
        
        if created_allocations:
            frappe.msgprint(_("Created {0} Compensatory Off allocations for {1}").format(
                len(created_allocations), tour_req.employee_name
            ))
        
        return created_allocations

    def create_comp_off_allocation_for_tour_requests(self, tour_request_name=None):
        """
        Creates Leave Allocation (Compensatory Off) for Week-Off, Holiday, or Restricted Holiday
        that fall between From Date and To Date of a Tour Request
        """
        
        if tour_request_name:
            # Process single tour request
            tour_requests = [frappe.get_doc("Tour Request", tour_request_name)]
        else:
            # Process all approved tour requests (if needed)
            tour_requests = frappe.get_all(
                "Tour Request",
                filters={
                    "workflow_state": "Approved by HR",
                    "docstatus": 1,
                    "comp_off_created": 0
                },
                fields=["name"]
            )
            tour_requests = [frappe.get_doc("Tour Request", req.name) for req in tour_requests]
        
        created_allocations = []
        for tour_req in tour_requests:
            try:
                allocations = self.process_tour_request_comp_off(tour_req)
                created_allocations.extend(allocations)
            except Exception as e:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"Tour Request Comp-Off Error - {tour_req.name}"
                )
        
        frappe.db.commit()
        return created_allocations

    def on_submit(self):
        # Create Comp-Off allocations for holidays/weekoffs
        if self.workflow_state == "Approved by HR" and self.docstatus == 1:
            self.create_comp_off_allocation_for_tour_requests(self.name)
        
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
                if att_date <= getdate(today_date) and existing_att.custom_is_penalize == 1:
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
                                "custom_penalty_leave_count": "",
                                "custom_remark": "On Duty",
                                "status": "Present"
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

    def get_fiscal_year_end_date(self, company, date):
        """Get fiscal year end date"""
        try:
            fiscal_year = frappe.db.get_value(
                "Fiscal Year",
                {
                    "year_start_date": ("<=", date), 
                    "year_end_date": (">=", date)
                },
                "name"
            )
            if fiscal_year:
                return frappe.db.get_value("Fiscal Year", fiscal_year, "year_end_date")
            
            fiscal_year = frappe.db.get_value(
                "Fiscal Year",
                {"company": company},
                "name",
                order_by="year_start_date ASC"
            )
            if fiscal_year:
                return frappe.db.get_value("Fiscal Year", fiscal_year, "year_end_date")
            
            year = datetime.strptime(date, "%Y-%m-%d").year
            return f"{year}-12-31"
            
        except Exception as e:
            frappe.log_error(f"Error getting fiscal year end date: {str(e)}", "Tour Cancel")
            return date

    def on_cancel(self):
        """Cancel Tour Request - Process ALL attendance and LLEs in the date range"""
        self.db_set("workflow_state", "Cancelled")
        
        total_days = date_diff(self.to_date, self.from_date) + 1
        employee_doc = frappe.get_doc("Employee", self.employee)
        
        # ============================================
        # STEP 1: Get ALL On Duty attendance records in the date range
        # ============================================
        all_attendance_list = frappe.get_all(
            "Attendance",
            filters={
                "employee": self.employee,
                "attendance_date": ["between", [self.from_date, self.to_date]],
                "docstatus": 1
            },
            pluck="name"
        )
        
        frappe.log_error(
            f"Found {len(all_attendance_list)} On Duty attendance records between {self.from_date} and {self.to_date}",
            "Tour Cancel"
        )
        
        # ============================================
        # STEP 2: Get ALL LLEs in the date range
        # ============================================
        all_lle_names = frappe.get_all(
            "Leave Ledger Entry",
            filters={
                "employee": self.employee,
                "docstatus": 1,
                "from_date": ["between", [self.from_date, self.to_date]]
            },
            pluck="name"
        )
        
        # Also get LLEs where to_date is in range
        lle_by_to_date = frappe.get_all(
            "Leave Ledger Entry",
            filters={
                "employee": self.employee,
                "docstatus": 1,
                "to_date": ["between", [self.from_date, self.to_date]]
            },
            pluck="name"
        )
        
        # Also get LLEs where from_date <= from_date and to_date >= to_date (covering entire range)
        lle_covering_range = frappe.get_all(
            "Leave Ledger Entry",
            filters={
                "employee": self.employee,
                "docstatus": 1,
                "from_date": ("<=", self.from_date),
                "to_date": (">=", self.to_date)
            },
            pluck="name"
        )
        
        # Combine all LLE lists and remove duplicates
        all_lle_names = list(set(all_lle_names + lle_by_to_date + lle_covering_range))
        
        frappe.log_error(
            f"Found {len(all_lle_names)} total LLEs in date range {self.from_date} to {self.to_date}",
            "Tour Cancel"
        )
        
        # ============================================
        # STEP 3: Process ALL LLEs
        # ============================================
        for lle_name in all_lle_names:
            try:
                lle = frappe.get_doc("Leave Ledger Entry", lle_name)
                
                # Check if this LLE falls within the tour date range
                if lle.from_date > self.to_date or lle.to_date < self.from_date:
                    continue
                
                if lle.docstatus == 1:
                    # Step 1: Set is_expired = 1
                    lle.is_expired = 1
                    lle.save(ignore_permissions=True)
                    frappe.db.commit()
                    
                    # Step 2: Cancel the document
                    lle.cancel()
                    frappe.db.commit()
                
                # Step 3: Delete the document
                lle.delete(ignore_permissions=True)
                frappe.db.commit()
                
                frappe.log_error(f"Processed and deleted LLE {lle_name}", "Tour Cancel")
                
            except Exception as e:
                frappe.log_error(f"Error processing LLE {lle_name}: {str(e)}", "Tour Cancel")
                # SQL fallback
                try:
                    frappe.db.sql(f"""
                        UPDATE `tabLeave Ledger Entry` 
                        SET is_expired = 1, docstatus = 2 
                        WHERE name = '{lle_name}'
                    """)
                    frappe.db.commit()
                    
                    frappe.db.sql(f"""
                        DELETE FROM `tabLeave Ledger Entry` 
                        WHERE name = '{lle_name}'
                    """)
                    frappe.db.commit()
                    
                    frappe.log_error(f"Force deleted LLE {lle_name} via SQL", "Tour Cancel")
                except Exception as sql_e:
                    frappe.log_error(f"SQL fallback failed for LLE {lle_name}: {str(sql_e)}", "Tour Cancel")
        
        # ============================================
        # STEP 4: Process ALL Attendance records
        # ============================================
        for att_name in all_attendance_list:
            try:
                old_att = frappe.get_doc("Attendance", att_name)
                
                # Remove any remaining links to attendance
                frappe.db.sql(f"""
                    UPDATE `tabLeave Ledger Entry` 
                    SET custom_attendance = NULL 
                    WHERE custom_attendance = '{att_name}'
                """)
                frappe.db.commit()
                
                # Cancel and delete attendance
                try:
                    old_att.cancel()
                    old_att.delete(ignore_permissions=True)
                    frappe.db.commit()
                    frappe.log_error(f"Deleted attendance {att_name}", "Tour Cancel")
                    
                except Exception as e:
                    frappe.log_error(f"Error deleting attendance {att_name}: {str(e)}", "Tour Cancel")
                    # Force delete via SQL
                    frappe.db.sql(f"""
                        DELETE FROM `tabAttendance` 
                        WHERE name = '{att_name}'
                    """)
                    frappe.db.commit()
                    frappe.log_error(f"Force deleted attendance {att_name} via SQL", "Tour Cancel")
                    
            except Exception as e:
                frappe.log_error(f"Error processing attendance {att_name}: {str(e)}", "Tour Cancel")
                continue
        
        # ============================================
        # STEP 5: Create new Absent attendance for each day
        # ============================================
        for i in range(total_days):
            att_date = add_days(self.from_date, i)
            
            # Check if attendance already exists
            if frappe.db.exists(
                "Attendance", 
                {
                    "employee": self.employee, 
                    "attendance_date": att_date, 
                    "docstatus": 1
                }
            ):
                frappe.log_error(f"Attendance already exists for {att_date}, skipping creation", "Tour Cancel")
                continue
            
            try:
                # Get company details from employee
                employee_details = frappe.db.get_value(
                    "Employee",
                    self.employee,
                    ["company", "branch", "shift", "employee_name"],
                    as_dict=True
                )
                
                # Create Absent Attendance
                new_att = frappe.new_doc("Attendance")
                new_att.employee = self.employee
                new_att.employee_name = employee_doc.employee_name
                new_att.attendance_date = att_date
                new_att.company = employee_details.company
                new_att.custom_branch = employee_details.branch
                new_att.shift = employee_details.shift
                new_att.status = "Absent"
                new_att.custom_is_penalize = 1
                new_att.custom_penalty_leave_type = "Leave Without Pay"
                new_att.custom_penalty_leave_count = -1
                new_att.custom_remark = "Tour Request Cancel"
                new_att.insert(ignore_permissions=True)
                new_att.submit()
                frappe.db.commit()
                frappe.log_error(f"Created Absent attendance {new_att.name} for {att_date}", "Tour Cancel")
                
                # Create LLE with fiscal year end date
                fiscal_year_end = self.get_fiscal_year_end_date(employee_details.company, att_date)
                lle = frappe.new_doc("Leave Ledger Entry")
                lle.employee = self.employee
                lle.employee_name = employee_doc.employee_name
                lle.leave_type = "Leave Without Pay"
                lle.from_date = att_date
                lle.to_date = fiscal_year_end
                lle.company = employee_details.company
                lle.custom_branch = employee_details.branch
                lle.transaction_type = "Leave Application"
                lle.leaves = -1
                lle.is_leave_without_pay = 1
                lle.custom_is_penalty = 1
                lle.custom_attendance = new_att.name
                lle.insert(ignore_permissions=True)
                lle.submit()
                frappe.db.commit()
                frappe.log_error(
                    f"Created LLE {lle.name} with from_date={att_date} to_date={fiscal_year_end}",
                    "Tour Cancel"
                )
                
            except Exception as e:
                frappe.db.rollback()
                frappe.log_error(f"Error creating records for {att_date}: {str(e)}", "Tour Cancel")
        
        frappe.db.commit()
        frappe.msgprint(_("Tour Request cancelled successfully. All Attendance and Leave Ledger entries have been updated."))