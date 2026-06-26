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
        """
        date = getdate(date) if date else getdate()

        all_assignments = frappe.db.sql("""
            SELECT name, holiday_list, from_date, creation, docstatus
            FROM `tabHoliday List Assignment`
            WHERE applicable_for = 'Employee'
            AND assigned_to = %s
            ORDER BY creation DESC
        """, (employee,), as_dict=True)

        submitted = frappe.db.sql("""
            SELECT name, holiday_list, from_date, creation
            FROM `tabHoliday List Assignment`
            WHERE applicable_for = 'Employee'
            AND assigned_to = %s
            AND docstatus = 1
            ORDER BY creation DESC
        """, (employee,), as_dict=True)

        if not submitted:
            return None

        for asgn in submitted:
            asgn_from = getdate(asgn.from_date) if asgn.from_date else None
            if asgn_from and asgn_from <= getdate(date):
                return asgn.holiday_list

        return submitted[0].holiday_list

    def get_holiday_details(self, employee, date):
        """
        Returns a dict with holiday details for the given date, or None
        if the date is a regular working day.
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

        NOTE: attendance_status is always "Present" for all day types
        when a Tour Request is active. The remark distinguishes the actual
        nature of the day (On Duty / Weekly Off / Restricted Holiday / Holiday).
        """
        holiday = self.get_holiday_details(employee, date)

        if not holiday:
            # Normal working day
            return {
                "status": "Working Day",
                "create_comp_off": False,
                "create_attendance": True,
                "attendance_status": "Present",
                "remark": "On Duty"
            }

        if cint(holiday.get("weekly_off")):
            return {
                "status": "Weekly Off",
                "create_comp_off": True,
                "create_attendance": True,
                "attendance_status": "Weekly Off",
                "remark": "On Duty"
            }

        if cint(holiday.get("custom_is_restricted_holiday")):
            return {
                "status": "Restricted Holiday",
                "create_comp_off": True,
                "create_attendance": True,
                "attendance_status": "Restricted Holiday",
                "remark": "On Duty"
            }

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

            alloc_from = getdate(off_day["date"])
            alloc_to   = add_days(alloc_from, 45)

            leave_allocation.from_date      = alloc_from
            leave_allocation.to_date        = alloc_to

            leave_allocation.new_leaves_allocated       = 1
            leave_allocation.total_leaves_allocated     = 1
            leave_allocation.carry_forward              = 0
            leave_allocation.carry_forwarded_leaves_count = 0

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
        """
        created_allocations = []

        total_days = date_diff(tour_req.to_date, tour_req.from_date) + 1

        for i in range(total_days):
            current_date = add_days(tour_req.from_date, i)

            holiday_list = self.get_employee_holiday_list(tour_req.employee, current_date)

            if not holiday_list:
                frappe.log_error(
                    f"[CompOff] No holiday list found for {tour_req.employee} on {current_date} — skipping.",
                    "CompOff Debug"
                )
                continue

            holiday = frappe.db.get_value(
                "Holiday",
                {
                    "parent": holiday_list,
                    "holiday_date": getdate(current_date)
                },
                ["weekly_off", "custom_is_restricted_holiday", "description"],
                as_dict=True
            )

            if not holiday:
                # Normal working day — no comp off needed
                continue

            if cint(holiday.get("weekly_off")):
                holiday_type = "Weekly Off"
            elif cint(holiday.get("custom_is_restricted_holiday")):
                holiday_type = "Restricted Holiday"
            else:
                holiday_type = "Holiday"

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
                continue

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

            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"[CompOff] FAILED for {tour_req.employee} on {current_date}"
                )

        if created_allocations:
            frappe.db.set_value(self.doctype, self.name, "comp_off_created", 1)

        return created_allocations

    def create_comp_off_allocation_for_tour_requests(self, tour_request_name=None):
        """
        Entry point for Comp Off creation.
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
        On submission of a Tour Request, for EVERY day in the tour range:
          - ALL day types (Working Day, Weekly Off, Holiday, Restricted Holiday)
            → Attendance status = "Present", remark = "On Duty"
          - Holiday / Weekly Off / Restricted Holiday days also get a Comp Off allocation.
          - Any existing LWP penalty on the attendance record is removed.
        """
        # -------------------------------------------------------
        # STEP 1: Create Comp Off for all holiday / weekly-off days
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

            # day_info.status tells us the nature of the day (for comp-off logic);
            # attendance is always created as "Present" regardless of day type.
            day_info = self.get_day_type(self.employee, att_date)

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
                # Attendance already exists — set status to Present, remove any penalty
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

                        # Update attendance — always Present on tour, clear any penalty
                        frappe.db.set_value(
                            "Attendance",
                            existing_att.name,
                            {
                                "status": "Present",
                                "custom_is_penalize": 0,
                                "custom_penalty_leave_type": None,
                                "custom_penalty_leave_count": "",
                                "custom_remark": "On Duty"
                            }
                        )
                        frappe.db.commit()

                    except Exception as e:
                        frappe.log_error(
                            f"Error updating attendance {existing_att.name}: {str(e)}",
                            "Tour Submit"
                        )

                continue

            # No attendance yet — create as Present / On Duty for all tour days
            att = frappe.get_doc({
                "doctype": "Attendance",
                "employee": self.employee,
                "employee_name": employee_details.employee_name,
                "department": employee_details.department,
                "company": employee_details.company,
                "attendance_date": att_date,
                "status": "Present",        # always Present on submit (holiday/WO/RH/working)
                "custom_branch": employee_details.branch,
                "custom_remark": "On Duty"
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

            except Exception as e:
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

                except Exception as e:
                    frappe.db.sql("""
                        DELETE FROM `tabAttendance`
                        WHERE name = %s
                    """, att_name)
                    frappe.db.commit()

            except Exception as e:
                frappe.log_error(f"Error processing attendance {att_name}: {str(e)}", "Tour Cancel")
                continue

        # -------------------------------------------------------
        # STEP 5: Recreate correct Attendance after cancellation
        #
        # Working Day  → Absent + LWP penalty
        # Weekly Off   → Present (status = Weekly Off is NOT used; kept as Present
        #                but without penalty — consistent with on_submit behaviour)
        # RH / Holiday → Present (same reasoning as above)
        # -------------------------------------------------------
        for i in range(total_days):
            att_date = add_days(self.from_date, i)

            try:
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

                new_att = frappe.new_doc("Attendance")

                new_att.employee       = self.employee
                new_att.employee_name  = employee_details.employee_name
                new_att.company        = employee_details.company
                new_att.department     = employee_details.department
                new_att.custom_branch  = employee_details.branch
                new_att.shift          = employee_details.default_shift
                new_att.attendance_date = att_date

                if day_info["status"] == "Working Day":
                    new_att.status                     = "Absent"
                    new_att.custom_is_penalize         = 1
                    new_att.custom_penalty_leave_type  = "Leave Without Pay"
                    new_att.custom_penalty_leave_count = -1
                    new_att.custom_remark              = "Tour Request Cancel"
                elif day_info["status"] == "Weekly Off":
                    new_att.status                     = "Weekly Off"
                    new_att.custom_is_penalize         = 0
                    new_att.custom_penalty_leave_type  = ""
                    new_att.custom_penalty_leave_count = ""
                    new_att.custom_remark              = "On Duty"
                elif day_info["status"] == "Restricted Holiday":
                    new_att.status                     = "Restricted Holiday"
                    new_att.custom_is_penalize         = 0
                    new_att.custom_penalty_leave_type  = ""
                    new_att.custom_penalty_leave_count = ""
                    new_att.custom_remark              = "On Duty"
                elif day_info["status"] == "Holiday":
                    new_att.status                     = "Holiday"
                    new_att.custom_is_penalize         = 0
                    new_att.custom_penalty_leave_type  = ""
                    new_att.custom_penalty_leave_count = ""
                    new_att.custom_remark              = "On Duty"

                new_att.insert(ignore_permissions=True)
                new_att.submit()
                frappe.db.commit()

                # Create LWP Ledger Entry only for working days (Absent)
                if day_info["status"] == "Working Day":
                    fiscal_year_end = self.get_fiscal_year_end_date(
                        employee_details.company,
                        att_date
                    )

                    lle = frappe.new_doc("Leave Ledger Entry")

                    lle.employee       = self.employee
                    lle.employee_name  = employee_details.employee_name
                    lle.leave_type     = "Leave Without Pay"
                    lle.company        = employee_details.company
                    lle.custom_branch  = employee_details.branch

                    lle.from_date      = att_date
                    lle.to_date        = fiscal_year_end

                    lle.transaction_type   = "Leave Application"
                    lle.leaves             = -1

                    lle.is_leave_without_pay = 1
                    lle.custom_is_penalty    = 1
                    lle.custom_attendance    = new_att.name

                    lle.insert(ignore_permissions=True)
                    lle.submit()
                    frappe.db.commit()

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