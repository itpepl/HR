import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, add_days, formatdate, today, getdate,datetime
from jkmpcl_hr.jkmpcl_hr.doctype.attendance_lock.attendance_lock import AttendanceLock
from jkmpcl_hr.py.utils import get_emp_hr_manager, get_ceo_user, get_emp_review_manager


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
  
    def check_existing_comp_off_allocation(self, employee, date):

        return frappe.db.exists(
            "Leave Allocation",
            {
                "employee": employee,
                "leave_type": "Compensatory Off",
                "from_date": date,
                "docstatus": 1
            }
        )


    def get_holiday_details(self, employee, date):

        holiday_list = frappe.db.get_value(
            "Employee",
            employee,
            "holiday_list"
        )

        if not holiday_list:
            return None

        holiday = frappe.db.get_value(
            "Holiday",
            {
                "parent": holiday_list,
                "holiday_date": date
            },
            [
                "weekly_off",
                "custom_is_restricted_holiday"
            ],
            as_dict=True
        )

        if not holiday:
            return None

        return {
            "weekly_off": bool(holiday.weekly_off),
            "custom_is_restricted_holiday": bool(holiday.custom_is_restricted_holiday)
        }


    def get_day_type(self, employee, date):

        holiday = self.get_holiday_details(
            employee,
            date
        )

        if not holiday:
            return {
                "status": "Absent",
                "create_lwp": True
            }

        if holiday.get("weekly_off"):
            return {
                "status": "Weekly Off",
                "create_lwp": False
            }

        if holiday.get("custom_is_restricted_holiday"):
            return {
                "status": "Restricted Holiday",
                "create_lwp": False
            }

        return {
            "status": "Holiday",
            "create_lwp": False
        }

    def create_leave_allocation_entry(
        self,
        tour_req,
        off_day
    ):

        try:

            employee_doc = frappe.get_doc(
                "Employee",
                tour_req.employee
            )

            leave_allocation = frappe.new_doc(
                "Leave Allocation"
            )

            leave_allocation.naming_series = "HR-LAL-.YYYY.-"

            leave_allocation.employee = tour_req.employee
            leave_allocation.employee_name = employee_doc.employee_name

            leave_allocation.company = employee_doc.company
            leave_allocation.department = employee_doc.department
            leave_allocation.custom_branch = employee_doc.branch

            leave_allocation.leave_type = "Compensatory Off"

            leave_allocation.from_date = getdate(
                off_day["date"]
            )

            leave_allocation.to_date = add_days(
                getdate(off_day["date"]),
                45
            )

            leave_allocation.new_leaves_allocated = 1
            leave_allocation.total_leaves_allocated = 1

            leave_allocation.carry_forward = 0
            leave_allocation.carry_forwarded_leaves_count = 0

            leave_allocation.insert(
                ignore_permissions=True
            )

            leave_allocation.submit()

            return leave_allocation

        except Exception:

            frappe.log_error(
                frappe.get_traceback(),
                "Comp Off Creation Failed"
            )

            return None
   
    def get_holiday_details(self, employee, date):
        """
        Get holiday details for a date.
        """

        holiday_list = frappe.db.get_value(
            "Employee",
            employee,
            "holiday_list"
        )

        if not holiday_list:
            return None

        holiday = frappe.db.get_value(
            "Holiday",
            {
                "parent": holiday_list,
                "holiday_date": date
            },
            [
                "weekly_off",
                "custom_is_restricted_holiday"
            ],
            as_dict=True
        )

        if not holiday:
            return None

        return {
            "weekly_off": bool(holiday.weekly_off),
            "custom_is_restricted_holiday": bool(holiday.custom_is_restricted_holiday)
        }

    def get_day_type(self, employee, date):
        """
        Determine attendance status and whether LWP should be created.
        """

        holiday = self.get_holiday_details(employee, date)

        if not holiday:
            return {
                "status": "Absent",
                "create_lwp": True
            }

        if holiday.get("weekly_off"):
            return {
                "status": "Weekly Off",
                "create_lwp": False
            }

        if holiday.get("custom_is_restricted_holiday"):
            return {
                "status": "Restricted Holiday",
                "create_lwp": False
            }

        return {
            "status": "Holiday",
            "create_lwp": False
        }
    
    def process_tour_request_comp_off(self, tour_req):

        created_allocations = []

        total_days = (
            date_diff(
                tour_req.to_date,
                tour_req.from_date
            ) + 1
        )

        for i in range(total_days):

            current_date = add_days(
                tour_req.from_date,
                i
            )

            holiday = self.get_holiday_details(
                tour_req.employee,
                current_date
            )

            if not holiday:
                continue

            if self.check_existing_comp_off_allocation(
                tour_req.employee,
                current_date
            ):
                continue

            if holiday.get("weekly_off"):
                holiday_type = "Week Off"

            elif holiday.get("custom_is_restricted_holiday"):
                holiday_type = "Restricted Holiday"

            else:
                holiday_type = "Holiday"

            allocation = self.create_leave_allocation_entry(
                tour_req,
                {
                    "date": current_date,
                    "type": holiday_type
                }
            )

            if allocation:
                created_allocations.append(
                    allocation.name
                )

        if created_allocations:

            frappe.db.set_value(
                self.doctype,
                self.name,
                "comp_off_created",
                1
            )

        return created_allocations
    
    def create_comp_off_allocation_for_tour_requests(
        self,
        tour_request_name=None
    ):

        if tour_request_name:

            tour_requests = [
                frappe.get_doc(
                    "Tour Request",
                    tour_request_name
                )
            ]

        else:

            tour_requests = [
                frappe.get_doc(
                    "Tour Request",
                    d.name
                )
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
                    self.process_tour_request_comp_off(
                        tour_req
                    )
                )

            except Exception:

                frappe.log_error(
                    frappe.get_traceback(),
                    f"Tour Request Comp Off Error - {tour_req.name}"
                )

        return created_allocations

    def on_update(doc):
        doc.share_doc()
        
    def share_doc(doc):
        old_doc = doc.get_doc_before_save()
        
        if old_doc and old_doc.workflow_state:
            
            if old_doc.workflow_state != doc.workflow_state: 
            
                if doc.workflow_state == "Approved by Reporting Manager":
                    review_manager = get_emp_review_manager(doc.employee)
                    
                    if review_manager:
                        frappe.share.add_docshare(doc.doctype, doc.name, review_manager, read=1, select=1, write=1, flags={"ignore_share_permission": True})
                
                elif doc.workflow_state == "Approved by Review Manager":
                        hr_manager = get_emp_hr_manager(doc.employee)

                        if hr_manager:
                            frappe.share.add_docshare(doc.doctype, doc.name, hr_manager, read=1, select=1, write=1,submit=1, flags={"ignore_share_permission": True})
                     
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
                if att_date <= getdate(today_date):
                    try:
                        # Get and delete Leave Ledger Entry
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


    def get_day_type(self, employee, date):

        holiday = self.get_holiday_details(
            employee,
            date
        )

        if not holiday:
            return {
                "status": "Absent",
                "create_lwp": True
            }

        if holiday.get("weekly_off"):
            return {
                "status": "Weekly Off",
                "create_lwp": False
            }

        if holiday.get("custom_is_restricted_holiday"):
            return {
                "status": "Restricted Holiday",
                "create_lwp": False
            }

        return {
            "status": "Holiday",
            "create_lwp": False
        }
    
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

                allocation = frappe.get_doc(
                    "Leave Allocation",
                    allocation_name
                )

                if allocation.docstatus == 1:
                    allocation.cancel()

                allocation.delete(
                    ignore_permissions=True
                )

            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"Failed To Delete Comp Off Allocation {allocation_name}"
                )

        
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
                "from_date": (">=", self.to_date)
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
        # STEP 5: Recreate Attendance
        # ============================================

        for i in range(total_days):

            att_date = add_days(self.from_date, i)

            if frappe.db.exists(
                "Attendance",
                {
                    "employee": self.employee,
                    "attendance_date": att_date,
                    "docstatus": 1
                }
            ):
                continue

            try:

                employee_details = frappe.db.get_value(
                    "Employee",
                    self.employee,
                    [
                        "company",
                        "branch",
                        "default_shift",
                        "employee_name"
                    ],
                    as_dict=True
                )

                day_info = self.get_day_type(
                    self.employee,
                    att_date
                )

                new_att = frappe.new_doc("Attendance")

                new_att.employee = self.employee
                new_att.employee_name = employee_doc.employee_name
                new_att.attendance_date = att_date
                new_att.company = employee_details.company
                new_att.custom_branch = employee_details.branch
                new_att.shift = employee_details.default_shift
                new_att.status = day_info["status"]
                new_att.custom_remark = "Tour Request Cancel"

                if day_info["create_lwp"]:

                    new_att.custom_is_penalize = 1
                    new_att.custom_penalty_leave_type = "Leave Without Pay"
                    new_att.custom_penalty_leave_count = -1

                else:

                    new_att.custom_is_penalize = 0
                    new_att.custom_penalty_leave_type = None
                    new_att.custom_penalty_leave_count = ""

                new_att.insert(ignore_permissions=True)
                new_att.submit()

                frappe.db.commit()

                # Create LWP only for Working Days
                if day_info["create_lwp"]:

                    fiscal_year_end = self.get_fiscal_year_end_date(
                        employee_details.company,
                        att_date
                    )

                    lle = frappe.new_doc(
                        "Leave Ledger Entry"
                    )

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

            except Exception:

                frappe.db.rollback()

                frappe.log_error(
                    frappe.get_traceback(),
                    f"Tour Cancel Attendance Recreation Failed : {att_date}"
                )
        frappe.db.commit()
        frappe.msgprint(_("Tour Request cancelled successfully. All Attendance and Leave Ledger entries have been updated."))