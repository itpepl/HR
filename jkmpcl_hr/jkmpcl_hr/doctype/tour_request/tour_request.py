# import frappe
# from frappe import _
# from frappe.model.document import Document
# from frappe.utils import date_diff, add_days, formatdate, today, getdate,datetime,cint
# from jkmpcl_hr.jkmpcl_hr.doctype.attendance_lock.attendance_lock import AttendanceLock
# from jkmpcl_hr.py.utils import get_emp_hr_manager, get_ceo_user, get_emp_review_manager


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
  
#     def check_existing_comp_off_allocation(self, employee, date):

#         return frappe.db.exists(
#             "Leave Allocation",
#             {
#                 "employee": employee,
#                 "leave_type": "Compensatory Off",
#                 "from_date": getdate(date),
#                 "docstatus": ["!=", 2]
#             }
#         )

#     def get_employee_holiday_list(self, employee, date=None):

#         date = getdate(date) if date else getdate()

#         employee_name = frappe.db.get_value(
#             "Employee",
#             employee,
#             "employee_name"
#         )

#         assignment = frappe.db.sql("""
#             SELECT holiday_list
#             FROM `tabHoliday List Assignment`
#             WHERE applicable_for = 'Employee'
#             AND assigned_to = %s
#             AND from_date <= %s
#             AND holiday_list_end >= %s
#             AND docstatus = 1
#             ORDER BY from_date DESC
#             LIMIT 1
#         """, (
#             f"{employee}: {employee_name}",
#             date,
#             date
#         ), as_dict=True)

#         if assignment:
#             return assignment[0].holiday_list

#         return frappe.db.get_value(
#             "Employee",
#             employee,
#             "holiday_list"
#         )
    
#     def get_holiday_details(self, employee, date):

#         holiday_list = self.get_employee_holiday_list(
#             employee,
#             date
#         )

#         if not holiday_list:
#             return None

#         holiday = frappe.db.get_value(
#             "Holiday",
#             {
#                 "parent": holiday_list,
#                 "holiday_date": getdate(date)
#             },
#             [
#                 "holiday_date",
#                 "weekly_off",
#                 "custom_is_restricted_holiday",
#                 "description"
#             ],
#             as_dict=True
#         )

#         if not holiday:
#             return None

#         return {
#             "weekly_off": cint(holiday.weekly_off),
#             "custom_is_restricted_holiday": cint(
#                 holiday.custom_is_restricted_holiday
#             ),
#             "description": holiday.description
#         }
    
#     def get_day_type(self, employee, date):

#         holiday = self.get_holiday_details(
#             employee,
#             date
#         )

#         if not holiday:
#             return {
#                 "status": "Absent",
#                 "create_lwp": True
#             }

#         if holiday.get("weekly_off"):
#             return {
#                 "status": "Weekly Off",
#                 "create_lwp": False
#             }

#         if holiday.get("custom_is_restricted_holiday"):
#             return {
#                 "status": "Restricted Holiday",
#                 "create_lwp": False
#             }

#         return {
#             "status": "Holiday",
#             "create_lwp": False
#         }

#     def create_leave_allocation_entry(
#         self,
#         tour_req,
#         off_day
#     ):

#         try:

#             employee_doc = frappe.get_doc(
#                 "Employee",
#                 tour_req.employee
#             )

#             leave_allocation = frappe.new_doc(
#                 "Leave Allocation"
#             )

#             leave_allocation.naming_series = "HR-LAL-.YYYY.-"

#             leave_allocation.employee = tour_req.employee
#             leave_allocation.employee_name = employee_doc.employee_name

#             leave_allocation.company = employee_doc.company
#             leave_allocation.department = employee_doc.department
#             leave_allocation.custom_branch = employee_doc.branch

#             leave_allocation.leave_type = "Compensatory Off"

#             leave_allocation.from_date = getdate(
#                 off_day["date"]
#             )

#             leave_allocation.to_date = add_days(
#                 getdate(off_day["date"]),
#                 45
#             )

#             leave_allocation.new_leaves_allocated = 1
#             leave_allocation.total_leaves_allocated = 1

#             leave_allocation.carry_forward = 0
#             leave_allocation.carry_forwarded_leaves_count = 0

#             leave_allocation.insert(
#                 ignore_permissions=True
#             )

#             leave_allocation.submit()

#             return leave_allocation

#         except Exception:

#             frappe.log_error(
#                 frappe.get_traceback(),
#                 "Comp Off Creation Failed"
#             )

#             return None
    
#     def process_tour_request_comp_off(self, tour_req):

#         created_allocations = []

#         total_days = (
#             date_diff(
#                 tour_req.to_date,
#                 tour_req.from_date
#             ) + 1
#         )

#         for i in range(total_days):

#             current_date = add_days(
#                 tour_req.from_date,
#                 i
#             )

#             holiday = self.get_holiday_details(
#                 tour_req.employee,
#                 current_date
#             )

#             # Not Holiday
#             if not holiday:
#                 continue

#             if self.check_existing_comp_off_allocation(
#                 tour_req.employee,
#                 current_date
#             ):
#                 continue

#             if cint(holiday.get("weekly_off")):
#                 holiday_type = "Weekly Off"

#             elif cint(
#                 holiday.get("custom_is_restricted_holiday")
#             ):
#                 holiday_type = "Restricted Holiday"

#             else:
#                 holiday_type = "Holiday"

#             try:

#                 allocation = self.create_leave_allocation_entry(
#                     tour_req,
#                     {
#                         "date": current_date,
#                         "type": holiday_type
#                     }
#                 )

#                 if allocation:

#                     created_allocations.append(
#                         allocation.name
#                     )

#                     frappe.logger().info(
#                         f"Comp Off Created : {allocation.name} "
#                         f"Employee={tour_req.employee} "
#                         f"Date={current_date} "
#                         f"Type={holiday_type}"
#                     )

#             except Exception:

#                 frappe.log_error(
#                     frappe.get_traceback(),
#                     f"Comp Off Failed For {current_date}"
#                 )

#         if created_allocations:

#             frappe.db.set_value(
#                 self.doctype,
#                 self.name,
#                 "comp_off_created",
#                 1
#             )

#         return created_allocations
    
#     def create_comp_off_allocation_for_tour_requests(
#         self,
#         tour_request_name=None
#     ):

#         if tour_request_name:

#             tour_requests = [
#                 frappe.get_doc(
#                     "Tour Request",
#                     tour_request_name
#                 )
#             ]

#         else:

#             tour_requests = [
#                 frappe.get_doc(
#                     "Tour Request",
#                     d.name
#                 )
#                 for d in frappe.get_all(
#                     "Tour Request",
#                     filters={
#                         "workflow_state": "Approved by HR",
#                         "docstatus": 1,
#                         "comp_off_created": 0
#                     },
#                     fields=["name"]
#                 )
#             ]

#         created_allocations = []

#         for tour_req in tour_requests:

#             try:

#                 created_allocations.extend(
#                     self.process_tour_request_comp_off(
#                         tour_req
#                     )
#                 )

#             except Exception:

#                 frappe.log_error(
#                     frappe.get_traceback(),
#                     f"Tour Request Comp Off Error - {tour_req.name}"
#                 )

#         return created_allocations



#     def on_update(doc):
#         doc.share_doc()


#     def share_doc(doc):
#         old_doc = doc.get_doc_before_save()
        
#         if old_doc and old_doc.workflow_state:
            
#             if old_doc.workflow_state != doc.workflow_state: 
            
#                 if doc.workflow_state == "Approved by Reporting Manager":
#                     review_manager = get_emp_review_manager(doc.employee)
                    
#                     if review_manager:
#                         frappe.share.add_docshare(doc.doctype, doc.name, review_manager, read=1, select=1, write=1, flags={"ignore_share_permission": True})
                
#                 elif doc.workflow_state == "Approved by Review Manager":
#                         hr_manager = get_emp_hr_manager(doc.employee)

#                         if hr_manager:
#                             frappe.share.add_docshare(doc.doctype, doc.name, hr_manager, read=1, select=1, write=1,submit=1, flags={"ignore_share_permission": True})


#     def on_submit(self):
#         # Create Comp-Off allocations for holidays/weekoffs
#         if self.workflow_state == "Approved by HR" and self.docstatus == 1:
#             self.create_comp_off_allocation_for_tour_requests(self.name)
        
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
#                 if att_date <= getdate(today_date):
#                     try:
#                         # Get and delete Leave Ledger Entry
#                         lle = frappe.db.get_value(
#                             "Leave Ledger Entry",
#                             {
#                                 "employee": self.employee,
#                                 "from_date": att_date,
#                                 "custom_attendance": existing_att.name,
#                                 "docstatus": 1
#                             },
#                             "name"
#                         )
                        
#                         if lle:
#                             lle_doc = frappe.get_doc("Leave Ledger Entry", lle)
#                             if lle_doc.docstatus == 1:
#                                 lle_doc.is_expired = 1
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
#                                 "status": "Present"
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


#     def get_day_type(self, employee, date):

#         holiday = self.get_holiday_details(
#             employee,
#             date
#         )

#         if not holiday:
#             return {
#                 "status": "Absent",
#                 "create_lwp": True
#             }

#         if holiday.get("weekly_off"):
#             return {
#                 "status": "Weekly Off",
#                 "create_lwp": False
#             }

#         if holiday.get("custom_is_restricted_holiday"):
#             return {
#                 "status": "Restricted Holiday",
#                 "create_lwp": False
#             }

#         return {
#             "status": "Holiday",
#             "create_lwp": False
#         }
    
#     def get_fiscal_year_end_date(self, company, date):
#         """Get fiscal year end date"""
#         try:
#             fiscal_year = frappe.db.get_value(
#                 "Fiscal Year",
#                 {
#                     "year_start_date": ("<=", date), 
#                     "year_end_date": (">=", date)
#                 },
#                 "name"
#             )
#             if fiscal_year:
#                 return frappe.db.get_value("Fiscal Year", fiscal_year, "year_end_date")
            
#             fiscal_year = frappe.db.get_value(
#                 "Fiscal Year",
#                 {"company": company},
#                 "name",
#                 order_by="year_start_date ASC"
#             )
#             if fiscal_year:
#                 return frappe.db.get_value("Fiscal Year", fiscal_year, "year_end_date")
            
#             year = datetime.strptime(date, "%Y-%m-%d").year
#             return f"{year}-12-31"
            
#         except Exception as e:
#             frappe.log_error(f"Error getting fiscal year end date: {str(e)}", "Tour Cancel")
#             return date



#     def on_cancel(self):
#         """Cancel Tour Request - Process ALL attendance and LLEs in the date range"""
#         self.db_set("workflow_state", "Cancelled")

#         total_days = date_diff(self.to_date, self.from_date) + 1
#         employee_doc = frappe.get_doc("Employee", self.employee)

#         comp_off_allocations = frappe.get_all(
#             "Leave Allocation",
#             filters={
#                 "employee": self.employee,
#                 "leave_type": "Compensatory Off",
#                 "from_date": ["between", [self.from_date, self.to_date]]
#             },
#             pluck="name"
#         )

#         for allocation_name in comp_off_allocations:

#             try:

#                 allocation = frappe.get_doc(
#                     "Leave Allocation",
#                     allocation_name
#                 )

#                 if allocation.docstatus == 1:
#                     allocation.cancel()

#                 allocation.delete(
#                     ignore_permissions=True
#                 )

#             except Exception:
#                 frappe.log_error(
#                     frappe.get_traceback(),
#                     f"Failed To Delete Comp Off Allocation {allocation_name}"
#                 )

        
#         # ============================================
#         # STEP 1: Get ALL On Duty attendance records in the date range
#         # ============================================
#         all_attendance_list = frappe.get_all(
#             "Attendance",
#             filters={
#                 "employee": self.employee,
#                 "attendance_date": ["between", [self.from_date, self.to_date]],
#                 "docstatus": 1
#             },
#             pluck="name"
#         )
        
#         frappe.log_error(
#             f"Found {len(all_attendance_list)} On Duty attendance records between {self.from_date} and {self.to_date}",
#             "Tour Cancel"
#         )
        
#         # ============================================
#         # STEP 2: Get ALL LLEs in the date range
#         # ============================================
#         all_lle_names = frappe.get_all(
#             "Leave Ledger Entry",
#             filters={
#                 "employee": self.employee,
#                 "docstatus": 1,
#                 "from_date": ["between", [self.from_date, self.to_date]]
#             },
#             pluck="name"
#         )
        
#         # Also get LLEs where to_date is in range
#         lle_by_to_date = frappe.get_all(
#             "Leave Ledger Entry",
#             filters={
#                 "employee": self.employee,
#                 "docstatus": 1,
#                 "to_date": ["between", [self.from_date, self.to_date]]
#             },
#             pluck="name"
#         )
        
#         # Also get LLEs where from_date <= from_date and to_date >= to_date (covering entire range)
#         lle_covering_range = frappe.get_all(
#             "Leave Ledger Entry",
#             filters={
#                 "employee": self.employee,
#                 "docstatus": 1,
#                 "from_date": ("<=", self.from_date),
#                 "from_date": (">=", self.to_date)
#             },
#             pluck="name"
#         )
        
#         # Combine all LLE lists and remove duplicates
#         all_lle_names = list(set(all_lle_names + lle_by_to_date + lle_covering_range))
        
#         frappe.log_error(
#             f"Found {len(all_lle_names)} total LLEs in date range {self.from_date} to {self.to_date}",
#             "Tour Cancel"
#         )
        
#         # ============================================
#         # STEP 3: Process ALL LLEs
#         # ============================================
#         for lle_name in all_lle_names:
#             try:
#                 lle = frappe.get_doc("Leave Ledger Entry", lle_name)
                
#                 # Check if this LLE falls within the tour date range
#                 if lle.from_date > self.to_date or lle.to_date < self.from_date:
#                     continue
                
#                 if lle.docstatus == 1:
#                     # Step 1: Set is_expired = 1
#                     lle.is_expired = 1
#                     lle.save(ignore_permissions=True)
#                     frappe.db.commit()
                    
#                     # Step 2: Cancel the document
#                     lle.cancel()
#                     frappe.db.commit()
                
#                 # Step 3: Delete the document
#                 lle.delete(ignore_permissions=True)
#                 frappe.db.commit()
                
#                 frappe.log_error(f"Processed and deleted LLE {lle_name}", "Tour Cancel")
                
#             except Exception as e:
#                 frappe.log_error(f"Error processing LLE {lle_name}: {str(e)}", "Tour Cancel")
#                 # SQL fallback
#                 try:
#                     frappe.db.sql(f"""
#                         UPDATE `tabLeave Ledger Entry` 
#                         SET is_expired = 1, docstatus = 2 
#                         WHERE name = '{lle_name}'
#                     """)
#                     frappe.db.commit()
                    
#                     frappe.db.sql(f"""
#                         DELETE FROM `tabLeave Ledger Entry` 
#                         WHERE name = '{lle_name}'
#                     """)
#                     frappe.db.commit()
                    
#                     frappe.log_error(f"Force deleted LLE {lle_name} via SQL", "Tour Cancel")
#                 except Exception as sql_e:
#                     frappe.log_error(f"SQL fallback failed for LLE {lle_name}: {str(sql_e)}", "Tour Cancel")
        
#         # ============================================
#         # STEP 4: Process ALL Attendance records
#         # ============================================
#         for att_name in all_attendance_list:
#             try:
#                 old_att = frappe.get_doc("Attendance", att_name)
                
#                 # Remove any remaining links to attendance
#                 frappe.db.sql(f"""
#                     UPDATE `tabLeave Ledger Entry` 
#                     SET custom_attendance = NULL 
#                     WHERE custom_attendance = '{att_name}'
#                 """)
#                 frappe.db.commit()
                
#                 # Cancel and delete attendance
#                 try:
#                     old_att.cancel()
#                     old_att.delete(ignore_permissions=True)
#                     frappe.db.commit()
#                     frappe.log_error(f"Deleted attendance {att_name}", "Tour Cancel")
                    
#                 except Exception as e:
#                     frappe.log_error(f"Error deleting attendance {att_name}: {str(e)}", "Tour Cancel")
#                     # Force delete via SQL
#                     frappe.db.sql(f"""
#                         DELETE FROM `tabAttendance` 
#                         WHERE name = '{att_name}'
#                     """)
#                     frappe.db.commit()
#                     frappe.log_error(f"Force deleted attendance {att_name} via SQL", "Tour Cancel")
                    
#             except Exception as e:
#                 frappe.log_error(f"Error processing attendance {att_name}: {str(e)}", "Tour Cancel")
#                 continue
        
#         # ============================================
#         # STEP 5: Recreate Attendance
#         # ============================================

# # ============================================
# # Recreate Attendance After Tour Cancellation
# # ============================================

#         for i in range(total_days):

#             att_date = add_days(self.from_date, i)

#             try:

#                 # Skip if attendance already exists
#                 if frappe.db.exists(
#                     "Attendance",
#                     {
#                         "employee": self.employee,
#                         "attendance_date": att_date,
#                         "docstatus": 1
#                     }
#                 ):
#                     continue

#                 employee_details = frappe.db.get_value(
#                     "Employee",
#                     self.employee,
#                     [
#                         "employee_name",
#                         "company",
#                         "branch",
#                         "default_shift",
#                         "department"
#                     ],
#                     as_dict=True
#                 )

#                 day_info = self.get_day_type(
#                     self.employee,
#                     att_date
#                 )

#                 frappe.log_error(
#                     f"""
#                     Date: {att_date}
#                     Day Info: {day_info}
#                     Employee: {self.employee}
#                     """,
#                     "Tour Cancel Debug"
#                 )

#                 new_att = frappe.new_doc("Attendance")

#                 new_att.employee = self.employee
#                 new_att.employee_name = employee_details.employee_name
#                 new_att.company = employee_details.company
#                 new_att.department = employee_details.department
#                 new_att.custom_branch = employee_details.branch
#                 new_att.shift = employee_details.default_shift
#                 new_att.attendance_date = att_date
#                 new_att.custom_remark = "Tour Request Cancel"

#                 # Working Day
#                 if day_info["create_lwp"]:

#                     new_att.status = "Absent"
#                     new_att.custom_is_penalize = 1
#                     new_att.custom_penalty_leave_type = "Leave Without Pay"
#                     new_att.custom_penalty_leave_count = -1

#                 else:

#                     # Holiday / Weekly Off / RH
#                     new_att.status = "Present"

#                     new_att.custom_is_penalize = 0
#                     new_att.custom_penalty_leave_type = ""
#                     new_att.custom_penalty_leave_count = ""

#                     if day_info["status"] == "Weekly Off":
#                         new_att.custom_remark = "Weekly Off"

#                     elif day_info["status"] == "Restricted Holiday":
#                         new_att.custom_remark = "Restricted Holiday"

#                     else:
#                         new_att.custom_remark = "Holiday"

#                 new_att.insert(ignore_permissions=True)
#                 new_att.submit()

#                 frappe.db.commit()

#                 frappe.log_error(
#                     f"Attendance Created : {new_att.name}",
#                     "Tour Cancel Debug"
#                 )

#                 # Create LWP Ledger Entry only for Absent
#                 if day_info["create_lwp"]:

#                     fiscal_year_end = self.get_fiscal_year_end_date(
#                         employee_details.company,
#                         att_date
#                     )

#                     lle = frappe.new_doc(
#                         "Leave Ledger Entry"
#                     )

#                     lle.employee = self.employee
#                     lle.employee_name = employee_details.employee_name
#                     lle.leave_type = "Leave Without Pay"
#                     lle.company = employee_details.company
#                     lle.custom_branch = employee_details.branch

#                     lle.from_date = att_date
#                     lle.to_date = fiscal_year_end

#                     lle.transaction_type = "Leave Application"
#                     lle.leaves = -1

#                     lle.is_leave_without_pay = 1
#                     lle.custom_is_penalty = 1
#                     lle.custom_attendance = new_att.name

#                     lle.insert(ignore_permissions=True)
#                     lle.submit()

#                     frappe.db.commit()

#                     frappe.log_error(
#                         f"LWP Created : {lle.name}",
#                         "Tour Cancel Debug"
#                     )

#             except Exception:

#                 frappe.db.rollback()

#                 frappe.log_error(
#                     frappe.get_traceback(),
#                     f"Tour Cancel Attendance Recreation Failed : {att_date}"
#                 )
#         frappe.db.commit()
#         frappe.msgprint(_("Tour Request cancelled successfully. All Attendance and Leave Ledger entries have been updated."))





import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, add_days, formatdate, today, getdate, datetime, cint
from jkmpcl_hr.jkmpcl_hr.doctype.attendance_lock.attendance_lock import AttendanceLock
from jkmpcl_hr.py.utils import get_emp_hr_manager, get_ceo_user, get_emp_review_manager


class TourRequest(Document):

    # =========================================================
    # VALIDATE
    # =========================================================

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

    # =========================================================
    # VALIDATE EMPLOYEE SUSPENSION
    # =========================================================

    def validate_employee_suspension(self):
        """
        Validate that the employee is not suspended before allowing Tour Request creation
        """
        if not self.employee:
            return

        employee_data = frappe.db.get_value(
            "Employee",
            self.employee,
            ["employee_name", "status", "custom_suspended_from_date", "custom_suspended_to_date"],
            as_dict=True
        )

        if not employee_data:
            return

        if employee_data.status == "Suspended":
            frappe.throw(_("Tour Request cannot be created. Employee is currently suspended"))

        if employee_data.custom_suspended_from_date:
            suspended_from = employee_data.get("custom_suspended_from_date")
            suspended_to = employee_data.get("custom_suspended_to_date")

            current_date = today()

            if suspended_from and hasattr(suspended_from, 'strftime'):
                suspended_from = suspended_from.strftime('%Y-%m-%d')
            if suspended_to and hasattr(suspended_to, 'strftime'):
                suspended_to = suspended_to.strftime('%Y-%m-%d')

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

            if self.from_date and self.to_date:
                total_days = date_diff(self.to_date, self.from_date) + 1

                for i in range(total_days):
                    travel_date = add_days(self.from_date, i)

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

    # =========================================================
    # HOLIDAY LIST HELPERS
    # =========================================================

    def get_employee_holiday_list(self, employee, date=None):
        """
        Get the LATEST active Holiday List assigned to the employee
        directly from the Holiday List Assignment doctype.

        Never falls back to the Employee field — always reads from
        Holiday List Assignment only, ordered by creation DESC so
        the most recently created assignment wins when multiple
        assignments exist for the same employee.

        If no assignment is found at all, returns None.
        """
        date = getdate(date) if date else getdate()

        # Step 1: log ALL assignments for this employee so we can debug
        all_assignments = frappe.db.sql("""
            SELECT name, holiday_list, from_date, creation, docstatus
            FROM `tabHoliday List Assignment`
            WHERE applicable_for = 'Employee'
            AND assigned_to = %s
            ORDER BY creation DESC
        """, (employee,), as_dict=True)

        # frappe.log_error(
        #     f"[HolidayList] ALL assignments for {employee}: {all_assignments}",
        #     "CompOff Debug"
        # )

        # Step 2: get ALL submitted assignments for this employee,
        # latest created first — no end-date filter to avoid column errors
        submitted = frappe.db.sql("""
            SELECT name, holiday_list, from_date, creation
            FROM `tabHoliday List Assignment`
            WHERE applicable_for = 'Employee'
            AND assigned_to = %s
            AND docstatus = 1
            ORDER BY creation DESC
        """, (employee,), as_dict=True)

        # frappe.log_error(
        #     f"[HolidayList] Submitted assignments for {employee}: {submitted}",
        #     "CompOff Debug"
        # )

        if not submitted:
            # frappe.log_error(
            #     f"[HolidayList] No submitted assignment found for {employee}",
            #     "CompOff Debug"
            # )
            return None

        # Step 3: from the submitted list pick the first one whose from_date
        # is on or before the requested date (list is already newest-first)
        for asgn in submitted:
            asgn_from = getdate(asgn.from_date) if asgn.from_date else None
            if asgn_from and asgn_from <= getdate(date):
                # frappe.log_error(
                #     f"[HolidayList] Selected: {asgn.name} | "
                #     f"Holiday List: {asgn.holiday_list} | "
                #     f"from_date: {asgn.from_date} | creation: {asgn.creation}",
                #     "CompOff Debug"
                # )
                return asgn.holiday_list

        # Step 4: if no from_date matched, just return the latest submitted one
        # frappe.log_error(
        #     f"[HolidayList] No from_date match — using latest: "
        #     f"{submitted[0].name} | {submitted[0].holiday_list}",
        #     "CompOff Debug"
        # )
        return submitted[0].holiday_list

    def get_holiday_details(self, employee, date):
        """
        Returns a dict with holiday details for the given date, or None
        if the date is a regular working day.
        
        Keys returned:
            weekly_off                  (int 0/1)
            custom_is_restricted_holiday (int 0/1)
            description                 (str)
        """
        holiday_list = self.get_employee_holiday_list(employee, date)

        if not holiday_list:
            return None

        holiday = frappe.db.get_value(
            "Holiday",
            {
                "parent": holiday_list,
                "holiday_date": getdate(date)
            },
            [
                "holiday_date",
                "weekly_off",
                "custom_is_restricted_holiday",
                "description"
            ],
            as_dict=True
        )

        if not holiday:
            return None

        return {
            "weekly_off": cint(holiday.weekly_off),
            "custom_is_restricted_holiday": cint(holiday.custom_is_restricted_holiday),
            "description": holiday.description
        }

    def get_day_type(self, employee, date):
        """
        Returns a dict describing what kind of day this is.

        For every day in a Tour Request:
          - Working Day        → attendance Present (On Duty),          no Comp Off
          - Weekly Off         → attendance Weekly Off,                  + Comp Off
          - Restricted Holiday → attendance Restricted Holiday,          + Comp Off
          - Holiday            → attendance Holiday,                     + Comp Off

        The attendance `status` field value comes from ERPNext allowed values:
          'Present', 'Absent', 'On Leave', 'Half Day', 'Work From Home'
        Weekly Off and Holiday rows are stored as 'Present' in the Attendance
        doctype (ERPNext standard) but the remark distinguishes them clearly.
        """
        holiday = self.get_holiday_details(employee, date)

        if not holiday:
            # Normal working day — Present attendance, no Comp Off
            return {
                "status": "Working Day",
                "create_comp_off": False,
                "create_attendance": True,
                "attendance_status": "Present",
                "remark": "On Duty"
            }

        if cint(holiday.get("weekly_off")):
            # Weekly Off during tour — Weekly Off attendance + Comp Off
            return {
                "status": "Weekly Off",
                "create_comp_off": True,
                "create_attendance": True,
                "attendance_status": "Weekly Off",
                "remark": "On Duty"
            }

        if cint(holiday.get("custom_is_restricted_holiday")):
            # Restricted Holiday during tour — Restricted Holiday attendance + Comp Off
            return {
                "status": "Restricted Holiday",
                "create_comp_off": True,
                "create_attendance": True,
                "attendance_status": "Restricted Holiday",
                "remark": "On Duty"
            }

        # Regular Holiday during tour — Holiday attendance + Comp Off
        return {
            "status": "Holiday",
            "create_comp_off": True,
            "create_attendance": True,
            "attendance_status": "Holiday",
            "remark": "On Duty"
        }

    # =========================================================
    # COMP OFF HELPERS
    # =========================================================

    def check_existing_comp_off_allocation(self, employee, date):
        return frappe.db.exists(
            "Leave Allocation",
            {
                "employee": employee,
                "leave_type": "Compensatory Off",
                "from_date": getdate(date),
                "docstatus": ["!=", 2]
            }
        )

    def create_leave_allocation_entry(self, tour_req, off_day):
        """
        Create a single Compensatory Off Leave Allocation for one
        holiday / weekly-off / restricted-holiday date during the tour.

        Leave Allocation fields used (confirmed from doctype):
            employee, employee_name, company, department, custom_branch
            leave_type      : "Compensatory Off"
            from_date       : the holiday date
            to_date         : holiday date + 45 days (expiry)
            new_leaves_allocated   : 1
            total_leaves_allocated : 1
            carry_forward          : 0
        """
        try:
            employee_doc = frappe.get_doc("Employee", tour_req.employee)

            leave_allocation = frappe.new_doc("Leave Allocation")

            leave_allocation.naming_series  = "HR-LAL-.YYYY.-"
            leave_allocation.employee       = tour_req.employee
            leave_allocation.employee_name  = employee_doc.employee_name
            leave_allocation.company        = employee_doc.company
            leave_allocation.department     = employee_doc.department
            leave_allocation.custom_branch  = employee_doc.branch

            leave_allocation.leave_type     = "Compensatory Off"

            # from_date = the actual holiday date
            # to_date   = 45 days later (leave expires)
            alloc_from = getdate(off_day["date"])
            alloc_to   = add_days(alloc_from, 45)

            leave_allocation.from_date      = alloc_from
            leave_allocation.to_date        = alloc_to

            leave_allocation.new_leaves_allocated       = 1
            leave_allocation.total_leaves_allocated     = 1
            leave_allocation.carry_forward              = 0
            leave_allocation.carry_forwarded_leaves_count = 0

            # frappe.log_error(
            #     f"[CompOff] Inserting Leave Allocation | Employee: {tour_req.employee} "
            #     f"| Date: {alloc_from} | To: {alloc_to} | Type: {off_day.get('type')}",
            #     "CompOff Debug"
            # )

            leave_allocation.insert(ignore_permissions=True)
            leave_allocation.submit()

            frappe.db.commit()

            return leave_allocation

        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"[CompOff] Leave Allocation INSERT FAILED for {tour_req.employee} on {off_day.get('date')}"
            )
            return None

    def process_tour_request_comp_off(self, tour_req):
        """
        Loop over every day in the tour date range.
        For each day that is a Holiday / Weekly Off / Restricted Holiday,
        create a Comp Off Leave Allocation (if one does not already exist).

        Steps:
          1. Get employee's active holiday list for that date
          2. Check if the date is in the holiday list (weekly off / RH / holiday)
          3. If yes and no existing comp off → create Leave Allocation (Compensatory Off)
        """
        created_allocations = []

        total_days = date_diff(tour_req.to_date, tour_req.from_date) + 1

        # frappe.log_error(
        #     f"[CompOff] Starting for {tour_req.name} | Employee: {tour_req.employee} "
        #     f"| From: {tour_req.from_date} | To: {tour_req.to_date} | Days: {total_days}",
        #     "CompOff Debug"
        # )

        for i in range(total_days):
            current_date = add_days(tour_req.from_date, i)

            # Step 1: get holiday list for this employee on this date
            holiday_list = self.get_employee_holiday_list(tour_req.employee, current_date)

            # frappe.log_error(
            #     f"[CompOff] Date: {current_date} | Holiday List: {holiday_list}",
            #     "CompOff Debug"
            # )

            if not holiday_list:
                frappe.log_error(
                    f"[CompOff] No holiday list found for {tour_req.employee} on {current_date} — skipping.",
                    "CompOff Debug"
                )
                continue

            # Step 2: check if this date is a holiday/weekly off/RH in the list
            holiday = frappe.db.get_value(
                "Holiday",
                {
                    "parent": holiday_list,
                    "holiday_date": getdate(current_date)
                },
                ["weekly_off", "custom_is_restricted_holiday", "description"],
                as_dict=True
            )

            # frappe.log_error(
            #     f"[CompOff] Date: {current_date} | Holiday record: {holiday}",
            #     "CompOff Debug"
            # )

            if not holiday:
                # Normal working day — no comp off needed
                continue

            # Determine holiday type
            if cint(holiday.get("weekly_off")):
                holiday_type = "Weekly Off"
            elif cint(holiday.get("custom_is_restricted_holiday")):
                holiday_type = "Restricted Holiday"
            else:
                holiday_type = "Holiday"

            # Step 3: check if comp off already exists for this date
            existing = frappe.db.get_value(
                "Leave Allocation",
                {
                    "employee": tour_req.employee,
                    "leave_type": "Compensatory Off",
                    "from_date": getdate(current_date),
                    "docstatus": ["!=", 2]
                },
                "name"
            )

            if existing:
                # frappe.log_error(
                #     f"[CompOff] Already exists ({existing}) for {tour_req.employee} "
                #     f"on {current_date} — skipping.",
                #     "CompOff Debug"
                # )
                continue

            # Step 4: create the Comp Off Leave Allocation
            try:
                allocation = self.create_leave_allocation_entry(
                    tour_req,
                    {
                        "date": current_date,
                        "type": holiday_type
                    }
                )

                if allocation:
                    created_allocations.append(allocation.name)
                    # frappe.log_error(
                    #     f"[CompOff] Created {allocation.name} | Employee: {tour_req.employee} "
                    #     f"| Date: {current_date} | Type: {holiday_type}",
                    #     "CompOff Debug"
                    # )

            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"[CompOff] FAILED for {tour_req.employee} on {current_date}"
                )

        # frappe.log_error(
        #     f"[CompOff] Finished for {tour_req.name} | Created: {created_allocations}",
        #     "CompOff Debug"
        # )

        if created_allocations:
            frappe.db.set_value(self.doctype, self.name, "comp_off_created", 1)

        return created_allocations

    def create_comp_off_allocation_for_tour_requests(self, tour_request_name=None):
        """
        Entry point for Comp Off creation.
        If tour_request_name is given, process only that one record.
        Otherwise process all approved-but-unprocessed Tour Requests.
        """
        if tour_request_name:
            tour_requests = [frappe.get_doc("Tour Request", tour_request_name)]
        else:
            tour_requests = [
                frappe.get_doc("Tour Request", d.name)
                for d in frappe.get_all(
                    "Tour Request",
                    filters={
                        "workflow_state": "Approved by HR",
                        "docstatus": 1,
                        "comp_off_created": 0
                    },
                    fields=["name"]
                )
            ]

        created_allocations = []

        for tour_req in tour_requests:
            try:
                created_allocations.extend(
                    self.process_tour_request_comp_off(tour_req)
                )
            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"Tour Request Comp Off Error - {tour_req.name}"
                )

        return created_allocations

    # =========================================================
    # ON UPDATE  (workflow state sharing)
    # =========================================================

    def on_update(self):
        self.share_doc()

    def share_doc(self):
        old_doc = self.get_doc_before_save()

        if old_doc and old_doc.workflow_state:

            if old_doc.workflow_state != self.workflow_state:

                if self.workflow_state == "Approved by Reporting Manager":
                    review_manager = get_emp_review_manager(self.employee)

                    if review_manager:
                        frappe.share.add_docshare(
                            self.doctype, self.name, review_manager,
                            read=1, select=1, write=1,
                            flags={"ignore_share_permission": True}
                        )

                elif self.workflow_state == "Approved by Review Manager":
                    hr_manager = get_emp_hr_manager(self.employee)

                    if hr_manager:
                        frappe.share.add_docshare(
                            self.doctype, self.name, hr_manager,
                            read=1, select=1, write=1, submit=1,
                            flags={"ignore_share_permission": True}
                        )

    # =========================================================
    # ON SUBMIT
    # =========================================================

    def on_submit(self):
        """
        On submission of an approved Tour Request:

        For EVERY day in the tour range:
          - Working Day        → Attendance = Present  (remark: On Duty)
                                 Remove any existing LWP penalty if present.
          - Weekly Off         → Attendance = Present  (remark: Weekly Off)   + Comp Off
          - Restricted Holiday → Attendance = Present  (remark: Restricted Holiday) + Comp Off
          - Holiday            → Attendance = Present  (remark: Holiday)      + Comp Off

        Comp Off allocations are created first (for all holiday-type days),
        then attendance is created / updated for every day.
        """
        # -------------------------------------------------------
        # STEP 1: Create Comp Off for all holiday / weekly-off days
        # Always run on submit — workflow_state check removed because at
        # on_submit time the state may still show the previous state.
        # -------------------------------------------------------
        self.create_comp_off_allocation_for_tour_requests(self.name)

        # -------------------------------------------------------
        # STEP 2: Create / update Attendance for every day
        # -------------------------------------------------------
        total_days = date_diff(self.to_date, self.from_date) + 1
        today_date = today()

        employee_details = frappe.db.get_value(
            "Employee",
            self.employee,
            ["employee_name", "department", "company", "branch"],
            as_dict=True
        )

        for i in range(total_days):
            att_date = add_days(self.from_date, i)

            # Determine what kind of day this is
            day_info = self.get_day_type(self.employee, att_date)

            # All day types now create attendance — check for existing record first
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
                # Attendance already exists — update status, remark and remove any penalty
                if att_date <= getdate(today_date):
                    try:
                        # Remove any Leave Ledger Entry (LWP penalty) tied to this attendance
                        lle = frappe.db.get_value(
                            "Leave Ledger Entry",
                            {
                                "employee": self.employee,
                                "from_date": att_date,
                                "custom_attendance": existing_att.name,
                                "docstatus": 1
                            },
                            "name"
                        )

                        if lle:
                            lle_doc = frappe.get_doc("Leave Ledger Entry", lle)
                            if lle_doc.docstatus == 1:
                                lle_doc.is_expired = 1
                                lle_doc.cancel()
                            lle_doc.delete(ignore_permissions=True)
                            frappe.db.commit()

                        # Update attendance — clear penalty, set correct status & remark
                        frappe.db.set_value(
                            "Attendance",
                            existing_att.name,
                            {
                                "custom_is_penalize": 0,
                                "custom_penalty_leave_type": None,
                                "custom_penalty_leave_count": "",
                                "custom_remark": day_info["remark"],
                                "status": day_info["attendance_status"]
                            }
                        )
                        frappe.db.commit()

                    except Exception as e:
                        frappe.log_error(
                            f"Error updating attendance {existing_att.name}: {str(e)}",
                            "Tour Submit"
                        )

                # Attendance already existed — move to next date
                continue

            # No attendance exists yet — create a new one with correct status & remark
            att = frappe.get_doc({
                "doctype": "Attendance",
                "employee": self.employee,
                "employee_name": employee_details.employee_name,
                "department": employee_details.department,
                "company": employee_details.company,
                "attendance_date": att_date,
                "status": day_info["attendance_status"],
                "custom_branch": employee_details.branch,
                "custom_remark": day_info["remark"]
            })

            att.insert(ignore_permissions=True)
            att.submit()
            frappe.db.commit()

    # =========================================================
    # FISCAL YEAR HELPER
    # =========================================================

    def get_fiscal_year_end_date(self, company, date):
        """Get fiscal year end date for the given company and date."""
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
            # frappe.log_error(f"Error getting fiscal year end date: {str(e)}", "Tour Cancel")
            return date

    # =========================================================
    # ON CANCEL
    # =========================================================

    def on_cancel(self):
        """
        Cancel Tour Request — reverse all attendance and Leave Ledger Entries
        in the tour date range, then recreate correct attendance.
        """
        self.db_set("workflow_state", "Cancelled")

        total_days = date_diff(self.to_date, self.from_date) + 1
        employee_doc = frappe.get_doc("Employee", self.employee)

        # -------------------------------------------------------
        # Cancel & delete any Comp Off allocations created for this tour
        # -------------------------------------------------------
        comp_off_allocations = frappe.get_all(
            "Leave Allocation",
            filters={
                "employee": self.employee,
                "leave_type": "Compensatory Off",
                "from_date": ["between", [self.from_date, self.to_date]]
            },
            pluck="name"
        )

        for allocation_name in comp_off_allocations:
            try:
                allocation = frappe.get_doc("Leave Allocation", allocation_name)

                if allocation.docstatus == 1:
                    allocation.cancel()

                allocation.delete(ignore_permissions=True)

            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"Failed To Delete Comp Off Allocation {allocation_name}"
                )

        # -------------------------------------------------------
        # STEP 1: Find all submitted Attendance in the date range
        # -------------------------------------------------------
        all_attendance_list = frappe.get_all(
            "Attendance",
            filters={
                "employee": self.employee,
                "attendance_date": ["between", [self.from_date, self.to_date]],
                "docstatus": 1
            },
            pluck="name"
        )

        # frappe.log_error(
        #     f"Found {len(all_attendance_list)} attendance records between "
        #     f"{self.from_date} and {self.to_date}",
        #     "Tour Cancel"
        # )

        # -------------------------------------------------------
        # STEP 2: Find all Leave Ledger Entries in the date range
        # -------------------------------------------------------
        all_lle_names = frappe.get_all(
            "Leave Ledger Entry",
            filters={
                "employee": self.employee,
                "docstatus": 1,
                "from_date": ["between", [self.from_date, self.to_date]]
            },
            pluck="name"
        )

        lle_by_to_date = frappe.get_all(
            "Leave Ledger Entry",
            filters={
                "employee": self.employee,
                "docstatus": 1,
                "to_date": ["between", [self.from_date, self.to_date]]
            },
            pluck="name"
        )

        all_lle_names = list(set(all_lle_names + lle_by_to_date))

        # frappe.log_error(
        #     f"Found {len(all_lle_names)} LLEs in date range "
        #     f"{self.from_date} to {self.to_date}",
        #     "Tour Cancel"
        # )

        # -------------------------------------------------------
        # STEP 3: Cancel & delete all Leave Ledger Entries
        # -------------------------------------------------------
        for lle_name in all_lle_names:
            try:
                lle = frappe.get_doc("Leave Ledger Entry", lle_name)

                if lle.from_date > getdate(self.to_date) or lle.to_date < getdate(self.from_date):
                    continue

                if lle.docstatus == 1:
                    lle.is_expired = 1
                    lle.save(ignore_permissions=True)
                    frappe.db.commit()
                    lle.cancel()
                    frappe.db.commit()

                lle.delete(ignore_permissions=True)
                frappe.db.commit()

                # frappe.log_error(f"Processed and deleted LLE {lle_name}", "Tour Cancel")

            except Exception as e:
                # frappe.log_error(f"Error processing LLE {lle_name}: {str(e)}", "Tour Cancel")
                try:
                    frappe.db.sql("""
                        UPDATE `tabLeave Ledger Entry`
                        SET is_expired = 1, docstatus = 2
                        WHERE name = %s
                    """, lle_name)
                    frappe.db.commit()

                    frappe.db.sql("""
                        DELETE FROM `tabLeave Ledger Entry`
                        WHERE name = %s
                    """, lle_name)
                    frappe.db.commit()

                    # frappe.log_error(f"Force deleted LLE {lle_name} via SQL", "Tour Cancel")
                except Exception as sql_e:
                    frappe.log_error(
                        f"SQL fallback failed for LLE {lle_name}: {str(sql_e)}",
                        "Tour Cancel"
                    )

        # -------------------------------------------------------
        # STEP 4: Cancel & delete all Attendance records
        # -------------------------------------------------------
        for att_name in all_attendance_list:
            try:
                old_att = frappe.get_doc("Attendance", att_name)

                frappe.db.sql("""
                    UPDATE `tabLeave Ledger Entry`
                    SET custom_attendance = NULL
                    WHERE custom_attendance = %s
                """, att_name)
                frappe.db.commit()

                try:
                    old_att.cancel()
                    old_att.delete(ignore_permissions=True)
                    frappe.db.commit()
                    # frappe.log_error(f"Deleted attendance {att_name}", "Tour Cancel")

                except Exception as e:
                    # frappe.log_error(
                    #     f"Error deleting attendance {att_name}: {str(e)}",
                    #     "Tour Cancel"
                    # )
                    frappe.db.sql("""
                        DELETE FROM `tabAttendance`
                        WHERE name = %s
                    """, att_name)
                    frappe.db.commit()
                    # frappe.log_error(f"Force deleted attendance {att_name} via SQL", "Tour Cancel")

            except Exception as e:
                frappe.log_error(f"Error processing attendance {att_name}: {str(e)}", "Tour Cancel")
                continue

        # -------------------------------------------------------
        # STEP 5: Recreate correct Attendance after cancellation
        # -------------------------------------------------------
        for i in range(total_days):
            att_date = add_days(self.from_date, i)

            try:
                # Skip if attendance already exists (shouldn't happen, but guard anyway)
                if frappe.db.exists(
                    "Attendance",
                    {
                        "employee": self.employee,
                        "attendance_date": att_date,
                        "docstatus": 1
                    }
                ):
                    continue

                employee_details = frappe.db.get_value(
                    "Employee",
                    self.employee,
                    ["employee_name", "company", "branch", "default_shift", "department"],
                    as_dict=True
                )

                day_info = self.get_day_type(self.employee, att_date)

                # frappe.log_error(
                #     f"Date: {att_date} | Day Info: {day_info} | Employee: {self.employee}",
                #     "Tour Cancel Debug"
                # )

                new_att = frappe.new_doc("Attendance")

                new_att.employee = self.employee
                new_att.employee_name = employee_details.employee_name
                new_att.company = employee_details.company
                new_att.department = employee_details.department
                new_att.custom_branch = employee_details.branch
                new_att.shift = employee_details.default_shift
                new_att.attendance_date = att_date
                new_att.custom_remark = "Tour Request Cancel"

                if day_info["status"] == "Working Day":
                    # Normal working day without tour — mark Absent with LWP penalty
                    new_att.status = "Absent"
                    new_att.custom_is_penalize = 1
                    new_att.custom_penalty_leave_type = "Leave Without Pay"
                    new_att.custom_penalty_leave_count = -1
                    new_att.custom_remark = "Tour Request Cancel"
                elif day_info["status"] == "Weekly Off":
                    new_att.status = "Weekly Off"
                    new_att.custom_is_penalize = 0
                    new_att.custom_penalty_leave_type = ""
                    new_att.custom_penalty_leave_count = ""
                    new_att.custom_remark = "On Duty"
                elif day_info["status"] == "Restricted Holiday":
                    new_att.status = "Restricted Holiday"
                    new_att.custom_is_penalize = 0
                    new_att.custom_penalty_leave_type = ""
                    new_att.custom_penalty_leave_count = ""
                    new_att.custom_remark = "On Duty"
                elif day_info["status"] == "Holiday":
                    new_att.status = "Holiday"
                    new_att.custom_is_penalize = 0
                    new_att.custom_penalty_leave_type = ""
                    new_att.custom_penalty_leave_count = ""
                    new_att.custom_remark = "On Duty"

                new_att.insert(ignore_permissions=True)
                new_att.submit()
                frappe.db.commit()

                # frappe.log_error(f"Attendance Created: {new_att.name}", "Tour Cancel Debug")

                # Create LWP Ledger Entry only for Absent (working day without tour)
                if day_info["status"] == "Working Day":
                    fiscal_year_end = self.get_fiscal_year_end_date(
                        employee_details.company,
                        att_date
                    )

                    lle = frappe.new_doc("Leave Ledger Entry")

                    lle.employee = self.employee
                    lle.employee_name = employee_details.employee_name
                    lle.leave_type = "Leave Without Pay"
                    lle.company = employee_details.company
                    lle.custom_branch = employee_details.branch

                    lle.from_date = att_date
                    lle.to_date = fiscal_year_end

                    lle.transaction_type = "Leave Application"
                    lle.leaves = -1

                    lle.is_leave_without_pay = 1
                    lle.custom_is_penalty = 1
                    lle.custom_attendance = new_att.name

                    lle.insert(ignore_permissions=True)
                    lle.submit()
                    frappe.db.commit()

                    # frappe.log_error(f"LWP Created: {lle.name}", "Tour Cancel Debug")

            except Exception:
                frappe.db.rollback()
                frappe.log_error(
                    frappe.get_traceback(),
                    f"Tour Cancel Attendance Recreation Failed: {att_date}"
                )

        frappe.db.commit()
        frappe.msgprint(_(
            "Tour Request cancelled successfully. "
            "All Attendance and Leave Ledger entries have been updated."
        ))