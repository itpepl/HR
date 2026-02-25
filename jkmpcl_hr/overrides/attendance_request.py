import frappe
from frappe import _, cint
from frappe.utils import getdate, get_link_to_form, nowdate, get_datetime
from hrms.hr.doctype.attendance_request.attendance_request import AttendanceRequest as HRMSAttendanceRequest, OverlappingAttendanceRequestError
from datetime import datetime, date,timedelta, time
from jkmpcl_hr.py.scheduler_method import deduct_leave_by_priority ,get_employee_leave_type, create_leave_ledger
from jkmpcl_hr.py.utils import send_notification_email
from erpnext.setup.doctype.employee.employee import is_holiday
from jkmpcl_hr.py.scheduler_method import get_employee_shift,create_or_update_attendance
from jkmpcl_hr.py.utils import get_emp_hr_manager, get_ceo_user


class AttendanceRequest(HRMSAttendanceRequest):

    def validate(self):
        from hrms.hr.utils import validate_active_employee
        validate_active_employee(self.employee)
        self.validate_dates_custom()
        self.validate_request_overlap_custom()
        # self.validate_no_attendance_to_create()
        self.validate_shift_assignment()

    def on_update(self):
        self.handle_workflow_notification()
        self.share_doc()

    def on_submit(self):
        # pass
    #     """Runs when Attendance Request is submitted"""
        self.create_auto_checkin_and_attendance()

    def handle_workflow_notification(self):

        recipients,notification_name = self.get_notification_recipients()

        notification_doc = frappe.get_doc("Notification", notification_name)
        if notification_doc:

            # Call your custom notification function
            send_notification_email(
                recipients=recipients,
                doctype=self.doctype,
                docname=self.name,
                notification_name=notification_name,
                send_link=False,
                fallback_subject=f"Attendance Request for {self.from_date}",
                fallback_message=f"Attendance Request for { self.from_date } is now in '{ self.workflow_state }' state.",
                enabled=notification_doc.enabled,
                send_system_notification=notification_doc.send_system_notification,
                channel=notification_doc.channel
            )


    def validate_shift_assignment(self):
        
        shift = frappe.db.get_list(
            "Shift Assignment",
            filters={
                "employee": self.employee,
                "start_date": ["<=", self.from_date],
                "status": "Active"
            },
            or_filters=[
                {"end_date": [">=", self.from_date]},
                {"end_date": ["is", "not set"]}
            ],
            fields=["shift_type"],
            order_by="start_date desc",
            limit=1
        )

        shift_assignment = shift[0].shift_type if shift else None

        if shift_assignment:
            return

        # fallback to default shift
        default_shift = frappe.db.get_value("Employee", self.employee, "default_shift")

        if not default_shift:
            frappe.throw(
                _("Cannot submit Attendance Request.<br>"
                "No <b>Shift Assignment</b> or <b>Default Shift</b> found for employee "
                "<b>{0}</b> on <b>{1}</b>.").format(
                    self.employee, self.from_date
                )
            )

    def get_notification_recipients(self):
        recipients = []
        approver_user = None
        notification_name = "Attendance Request Approval"

        if self.workflow_state == "Pending":
            approver = frappe.db.get_list(
                "Approver",
                filters={
                    "parent": self.employee,
                    "effective_from": ["<=", frappe.utils.now_datetime()],
                    "parentfield": "custom_reporting_manager"
                },
                fields=["name"],
                order_by="effective_from desc",
                ignore_permissions=True,
                limit=1
            )

            if approver:
                approver_user = frappe.db.get_value("Approver", approver[0].name, "user")

        elif self.workflow_state == "Approved by Reporting Manager":

            approver = frappe.db.get_list(
                "Approver",
                filters={
                    "parent": self.employee,
                    "effective_from": ["<=", frappe.utils.now_datetime()],
                    "parentfield": "custom_hr_manager"
                },
                fields=["name"],
                order_by="effective_from desc",
                ignore_permissions=True,
                limit=1
            )

            if approver:
                approver_user = frappe.db.get_value("Approver", approver[0].name, "user")

        elif self.workflow_state == "Approved by HR":
            users = frappe.get_all("Has Role", filters={"role": "CEO"}, pluck="parent") or []

            ceo_users = frappe.get_all(
                "User",
                filters=[
                    ["User", "name", "in", users],
                    ["User", "enabled", "=", 1],
                    ["User", "name", "!=", "Administrator"]
                ],
                pluck="name"
            )
            recipients.extend(ceo_users)
            
        elif self.workflow_state in ["Final Approved", "Rejected", "Rejected by Reporting Manager", "Rejected by HR"]:
            approver_user = frappe.db.get_value("Employee", self.employee, "user_id")
            if self.workflow_state == "Final Approved":
                notification_name = "Attendance Request Approved"
            else:
                notification_name = "Attendance Request Rejected"

        if approver_user:
            recipients.append(approver_user)

        return recipients, notification_name

    def validate_no_attendance_to_create(self):
        # validate only for single day (self.from_date)
        attendance_warnings = self.get_attendance_warnings(self.from_date)
        # if there are warnings and none allow Overwrite, block
        if attendance_warnings and not any(warning["action"] == "Overwrite" for warning in attendance_warnings):
            frappe.throw(
                title=_("No attendance records to create"),
                msg=_(
                    "Please check if employee is on leave or attendance with the same status exists for the selected day."
                ),
            )

    @frappe.whitelist()
    def get_attendance_warnings(self, attendance_date=None) -> list:
        """
        Return warnings for a single date (defaults to self.from_date).
        Each warning is: {"date": date, "reason": "...", "action": "Skip" | "Overwrite", "record": ... (optional)}
        """
        if attendance_date is None:
            attendance_date = self.from_date

        attendance_warnings = []

        # skip holidays
        if not self.include_holidays and is_holiday(self.employee, attendance_date):
            attendance_warnings.append({"date": attendance_date, "reason": "Holiday", "action": "Skip"})
            print("\n\n\n\n",attendance_warnings," 1 \n\n\n\n")
            return attendance_warnings

        # on leave
        if self.has_leave_record(attendance_date):
            attendance_warnings.append({"date": attendance_date, "reason": "On Leave", "action": "Skip"})
            print("\n\n\n\n",attendance_warnings," 2 \n\n\n\n")
            return attendance_warnings

        # status unchanged
        if self.status_unchanged(attendance_date):
            attendance_warnings.append({"date": attendance_date, "reason": "Attendance status unchanged", "action": "Skip"})
            print("\n\n\n\n",attendance_warnings," 3 \n\n\n\n")
            return attendance_warnings

        # existing attendance record
        attendance = self.get_attendance_doc(attendance_date)
        if attendance:
            attendance_warnings.append({
                "date": attendance_date,
                "reason": "Attendance already marked",
                "record": attendance.name,
                "action": "Overwrite",
            })

        return attendance_warnings


    def share_doc(self):
        old_doc = self.get_doc_before_save()
        
        if old_doc and old_doc.workflow_state:
            if old_doc.workflow_state != self.workflow_state and self.workflow_state == "Approved by Reporting Manager":
                hr_manager = get_emp_hr_manager(self.employee)
                
                if hr_manager:
                    frappe.share.add_docshare(self.doctype, self.name, hr_manager, read=1, select=1, write=1, submit=1, flags={"ignore_share_permission": True})
            
            elif old_doc.workflow_state != self.workflow_state and self.workflow_state == "Approved by HR":
                ceo = get_ceo_user()
                
                if ceo:
                    frappe.share.add_docshare(self.doctype, self.name, ceo, read=1, select=1, write=1, submit=1, flags={"ignore_share_permission": True})
        
    # def create_auto_checkin_and_attendance(self):
    #     if not self.employee or not self.custom_punch_type:
    #         return

    #     try:
    #         if self.custom_punch_type in ["In", "Both"] and self.custom_in_time:
    #             create_checkin(
    #                 self.name,
    #                 self.employee,
    #                 self.custom_in_time,
    #                 "IN",
    #                 self.name,
    #                 self.from_date
    #             )

    #         if self.custom_punch_type in ["Out", "Both"] and self.custom_out_time:
    #             create_checkin(
    #                 self.name,
    #                 self.employee,
    #                 self.custom_out_time,
    #                 "OUT",
    #                 self.name,
    #                 self.from_date
    #             )

    #         if self.custom_in_time and self.custom_out_time:
    #             create_or_update_attendance_from_request(self)
    #         recalculate_attendance_after_manual_log(self.employee, self.from_date)
        
    #     except Exception as e:
    #         frappe.log_error(frappe.get_traceback(), "Attendance Request Error")
    #         frappe.throw(str(e))
    def create_auto_checkin_and_attendance(self):
        if not self.employee or not self.custom_punch_type:
            return

        try:
            # 🔁 Decide datetime fields based on shift type
            if self.custom_shift_type == "Night":
                in_time = self.custom_shift_in_time
                out_time = self.custom_shift_in_out
                is_full_datetime = True
            else:
                in_time = self.custom_in_time
                out_time = self.custom_out_time
                is_full_datetime = False

            # ✅ IN checkin
            if self.custom_punch_type in ["In", "Both"] and in_time:
                create_checkin(
                    self.name,
                    self.employee,
                    in_time,
                    "IN",
                    self.name,
                    request_date=self.from_date,
                    is_full_datetime=is_full_datetime
                )

            # ✅ OUT checkin
            if self.custom_punch_type in ["Out", "Both"] and out_time:
                create_checkin(
                    self.name,
                    self.employee,
                    out_time,
                    "OUT",
                    self.name,
                    request_date=self.from_date,
                    is_full_datetime=is_full_datetime
                )

            # ✅ Attendance
            if in_time or out_time:
                create_or_update_attendance_from_request(self)
                recalculate_attendance_after_manual_log(
                    self.employee,
                    self.from_date
                )


        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                "Attendance Request Error"
            )
            frappe.throw("Failed to create checkin / attendance")


    def validate_dates_custom(self):
        """Custom date validation for Attendance Request."""
        date_of_joining, relieving_date = frappe.db.get_value(
            "Employee", self.employee, ["date_of_joining", "relieving_date"]
        )
        if getdate(self.from_date) > getdate(nowdate()):
            frappe.throw(_("Future dates not allowed"))
        elif date_of_joining and getdate(self.from_date) < getdate(date_of_joining):
            frappe.throw(_("From date can not be less than employee's joining date"))
        elif relieving_date and getdate(self.from_date) > getdate(relieving_date):
            frappe.throw(_("To date can not greater than employee's relieving date"))

    def validate_request_overlap_custom(self):
        if not self.name:
            self.name = "New Attendance Request"

        Request = frappe.qb.DocType("Attendance Request")

        existing_requests = (
            frappe.qb.from_(Request)
            .select(Request.name, Request.custom_punch_type)
            .where(
                (Request.employee == self.employee)
                & (Request.docstatus < 2)
                & (Request.name != self.name)
                & (Request.from_date == self.from_date)
            )
        ).run(as_dict=True)

        if not existing_requests:
            return

        existing_types = {r.custom_punch_type for r in existing_requests}
        new_type = self.custom_punch_type

        # ❌ If BOTH already exists → nothing else allowed
        if "Both" in existing_types:
            self.throw_overlap_error(existing_requests[0].name)

        # ❌ If trying to add BOTH when IN or OUT already exists
        if new_type == "Both" and existing_types:
            self.throw_overlap_error(existing_requests[0].name)

        # ❌ Duplicate IN or OUT
        if new_type in existing_types:
            self.throw_overlap_error(existing_requests[0].name)

        # ❌ If already have IN + OUT → block third entry
        if existing_types == {"In", "Out"}:
            self.throw_overlap_error(existing_requests[0].name)


    def throw_overlap_error(self, overlapping_request: str):
        msg = _("Employee {0} already has an Attendance Request(s) {1} that overlaps with this date").format(
            frappe.bold(self.employee),
            get_link_to_form("Attendance Request", overlapping_request),
        )
        frappe.throw(
            msg,
            title=_("Overlapping Attendance Request"),
            exc=OverlappingAttendanceRequestError
        )


def recalculate_attendance_after_manual_log(employee, date):
    # Fetch all logs for the day
    logs = frappe.db.sql("""
        SELECT 
            MIN(time) AS in_time,
            MAX(time) AS out_time,
            COUNT(*) AS punches
        FROM `tabEmployee Checkin`
        WHERE employee = %s AND DATE(time) = %s
    """, (employee, date), as_dict=True)[0]

    if not logs or not logs.in_time:
        return  # No logs → nothing to update

    # Determine working hours
    if logs.punches == 1:
        in_time = logs.in_time
        out_time = None
        working_hours = 0
    else:
        in_time = logs.in_time
        out_time = logs.out_time
        working_hours = (out_time - in_time).total_seconds() / 3600

    update_attendance_direct_db(employee, date, in_time, out_time, working_hours)


# Updating attendance for HR-EMP-00001 on 2025-12-16 2025-12-16 09:40:00 2025-12-16 11:51:44 2.1955555555555555
# def update_attendance_direct_db(employee, date, in_time, out_time, working_hours):
#     shift_type = frappe.db.get_value("Employee", employee, "default_shift")
    
#     if not shift_type:
#         shift_assignment = frappe.db.get_list(
#             "Shift Assignment",
#             filters={
#                 "employee": employee,
#                 "start_date": ["<=", date],
#                 "status": "Active"
#             },
#             or_filters=[
#                 {"end_date": [">=", date]},
#                 {"end_date": ["is", "not set"]}
#             ],
#             fields=["shift_type"],
#             order_by="start_date desc",
#             limit=1
#         )

#         shift_type = shift_assignment[0].shift_type if shift_assignment else None

#     if shift_type:
#         shift = frappe.db.get_value(
#             "Shift Type",
#             shift_type,
#             ["working_hours_threshold_for_half_day",
#             "working_hours_threshold_for_absent"],
#             as_dict=True
#         )

#     half_day_threshold = float(shift.working_hours_threshold_for_half_day or 8)
#     absent_threshold   = float(shift.working_hours_threshold_for_absent or 3)

#     if working_hours == 0 or working_hours <= absent_threshold:
#         status = "Absent"
#     elif working_hours < half_day_threshold:
#         status = "Half Day"
#     else:
#         status = "Present"

#     attendance_name = frappe.db.get_value(
#         "Attendance",
#         {
#             "employee": employee,
#             "attendance_date": date,
#             "docstatus": ("!=", 2)
#         },
#         "name"
#     )

#     if not attendance_name:
#         return

#     # Update Attendance
#     frappe.db.sql("""
#         UPDATE `tabAttendance`
#         SET in_time=%s, out_time=%s, working_hours=%s, status=%s
#         WHERE name=%s
#     """, (in_time, out_time, working_hours, status, attendance_name))

#     # Always delete old Leave Ledger Entries
#     frappe.db.delete("Leave Ledger Entry", {
#         "employee": employee,
#         "transaction_type": "Attendance",
#         "transaction_name": attendance_name
#     })

#     # Create & submit Leave Ledger only for Half Day
#     if status == "Half Day":
#         leave_type = get_employee_leave_type(employee)
#         if leave_type:
#             lle = frappe.get_doc({
#                 "doctype": "Leave Ledger Entry",
#                 "employee": employee,
#                 "leave_type": leave_type,
#                 "posting_date": date,
#                 "from_date": date,
#                 "to_date": date,
#                 "leaves": -0.5,
#                 "transaction_type": "Attendance",
#                 "transaction_name": attendance_name
#             })
#             lle.insert(ignore_permissions=True)
#             lle.submit()

#     frappe.db.commit()



def update_attendance_direct_db(employee, date, in_time, out_time, working_hours):
    shift_type = frappe.db.get_value("Employee", employee, "default_shift")

    if not shift_type:
        shift_assignment = frappe.db.get_list(
            "Shift Assignment",
            filters={
                "employee": employee,
                "start_date": ["<=", date],
                "status": "Active"
            },
            or_filters=[
                {"end_date": [">=", date]},
                {"end_date": ["is", "not set"]}
            ],
            fields=["shift_type"],
            order_by="start_date desc",
            limit=1
        )
        shift_type = shift_assignment[0].shift_type if shift_assignment else None

    shift = frappe.db.get_value(
        "Shift Type",
        shift_type,
        ["working_hours_threshold_for_half_day",
         "working_hours_threshold_for_absent"],
        as_dict=True
    ) if shift_type else {}

    half_day_threshold = float(shift.get("working_hours_threshold_for_half_day") or 8)
    absent_threshold   = float(shift.get("working_hours_threshold_for_absent") or 3)

    if working_hours == 0 or working_hours <= absent_threshold:
        status = "Absent"
    elif working_hours < half_day_threshold:
        status = "Half Day"
    else:
        status = "Present"

    attendance_name = frappe.db.get_value(
        "Attendance",
        {
            "employee": employee,
            "attendance_date": date,
            "docstatus": ("!=", 2)
        },
        "name"
    )

    if not attendance_name:
        return

    frappe.db.sql("""
        UPDATE `tabAttendance`
        SET in_time=%s, out_time=%s, working_hours=%s, status=%s
        WHERE name=%s
    """, (in_time, out_time, working_hours, status, attendance_name))

    if status == "Present":
        revert_penalty_leave(attendance_name)

    frappe.db.delete(
        "Leave Ledger Entry",
        {
            "employee": employee,
            "transaction_type": "Attendance",
            "transaction_name": attendance_name
        }
    )

    if status in ("Half Day", "Absent"):

        leave_type = get_employee_leave_type(employee)

        if leave_type:
            leave_days = 0.5 if status == "Half Day" else 1

            create_leave_ledger(
                employee=employee,
                leave_type=leave_type,
                date=date,
                status=status,
                attendance=attendance_name,
                leave_days=leave_days,
            )

    frappe.db.commit()


def get_attendance_status(working_hours, shift):
    half_day_threshold = float(shift.working_hours_threshold_for_half_day or 8)
    absent_threshold   = float(shift.working_hours_threshold_for_absent or 3)

    if working_hours <= absent_threshold:
        return "Absent"
    elif working_hours < half_day_threshold:
        return "Half Day"
    return "Present"

def revert_penalty_leave(attendance_name):
    att = frappe.get_doc("Attendance", attendance_name)

    # If attendance was not penalized, nothing to revert
    if not att.custom_is_penalize:
        return

    leave_type = att.custom_penalty_leave_type
    leave_count = att.custom_penalty_leave_count
    attendance_date = att.attendance_date

    # 🔥 Delete related Leave Ledger Entry
    frappe.db.delete(
        "Leave Ledger Entry",
        {
            "employee": att.employee,
            "leave_type": leave_type,
            "from_date": attendance_date,
            "custom_is_penalty": 1,              # ✅ recommended if you have this field
            "custom_attendance": att.name,
        }
    )

    # 🔄 Reset Attendance penalty fields
    att.db_set({
        "custom_penalty_leave_type": None,
        "custom_penalty_leave_count": 0,
        "custom_is_penalize": 0
    })

    # ✅ Recalculate leave balance (important)
    frappe.db.commit()
def create_checkin(
    name,
    employee,
    time_input,
    log_type,
    request_name,
    request_date=None,
    is_full_datetime=False
):
    """
    time_input:
        - datetime
        - string datetime ("2025-11-22 22:00:00")
        - string time ("09:00")
    """

    # ✅ Normalize to datetime
    if is_full_datetime:
        full_datetime = get_datetime(time_input)
    else:
        # time_input like "09:00"
        full_datetime = make_datetime(request_date, time_input)

    if not full_datetime:
        return

    db_datetime = full_datetime.strftime("%Y-%m-%d %H:%M:%S")

    # ✅ Avoid duplicate checkin
    exists = frappe.db.exists(
        "Employee Checkin",
        {
            "employee": employee,
            "time": db_datetime,
            "log_type": log_type
        }
    )
    if exists:
        return f"Checkin already exists: {exists}"

    checkin = frappe.get_doc({
        "doctype": "Employee Checkin",
        "employee": employee,
        "time": db_datetime,
        "log_type": log_type,
        "attendance_request": request_name,
        "custom_attendance_request": name
    })

    checkin.insert(ignore_permissions=True)
    frappe.db.commit()

    return f"Checkin created: {checkin.name}"

# def create_attendance_from_request(doc):
#     """
#     Create Attendance from an Attendance Request and return a user message string.
#     (No frappe.msgprint here)
#     """
#     shift_assignment = frappe.db.get_list(
#         "Shift Assignment",
#         filters={
#             "employee": doc.employee,
#             "start_date": ["<=", doc.from_date],
#             "status": "Active"
#         },
#         or_filters=[
#             {"end_date": [">=", doc.from_date]},
#             {"end_date": ["is", "not set"]}
#         ],
#         fields=["shift_type"],
#         order_by="start_date desc",
#         limit=1
#     )

#     shift_type = shift_assignment[0].shift_type if shift_assignment else None

#     if not shift_type:
#         frappe.throw(f"No Shift found for employee {doc.employee} on {doc.from_date}")

#     shift = frappe.db.get_value(
#         "Shift Type",
#         shift_type,
#         ["working_hours_threshold_for_half_day", "working_hours_threshold_for_absent"],
#         as_dict=True
#     )

#     in_datetime = make_datetime(doc.from_date, doc.custom_in_time)
#     out_datetime = make_datetime(doc.from_date, doc.custom_out_time)

#     if out_datetime < in_datetime:
#         frappe.throw("Out time cannot be less than In time")

#     working_hours = (out_datetime - in_datetime).total_seconds() / 3600
#     half_day_threshold = float(shift.working_hours_threshold_for_half_day or 8)
#     absent_threshold = float(shift.working_hours_threshold_for_absent or 3)

#     if working_hours == 0 or working_hours <= absent_threshold:
#         status = "Absent"
#     elif working_hours < half_day_threshold:
#         status = "Half Day"
#     else:
#         status = "Present"

#     attendance = frappe.get_doc({
#         "doctype": "Attendance",
#         "employee": doc.employee,
#         "attendance_date": doc.from_date,
#         "shift": shift_type,
#         "in_time": in_datetime,
#         "out_time": out_datetime,
#         "working_hours": working_hours,
#         "status": status,
#         "attendance_request": doc.name
#     })

#     attendance.insert(ignore_permissions=True)
#     attendance.submit()

    # if working_hours < half_day_threshold:
    #     deduct_leave_by_priority(doc.employee, doc.from_date, status, attendance.name)

#     message = f"Attendance created: {status} ({round(working_hours, 2)} hrs)"
#     return message

def create_or_update_attendance_from_request(doc):

    frappe.enqueue(
        "jkmpcl_hr.overrides.attendance_request._process_attendance_request",
        queue="long",
        enqueue_after_commit=True,
        doc_name=doc.name
    )

    return "Attendance queued for processing"



def _process_attendance_request(doc_name):
    doc = frappe.get_doc("Attendance Request", doc_name)

    date_val = doc.from_date

    shift_type = get_employee_shift(doc.employee, date_val)
    if not shift_type:
        frappe.throw(f"No Shift found for employee {doc.employee} on {date_val}")

    def parse_datetime(val):
        if isinstance(val, datetime):
            return val
        if isinstance(val, str):
            try:
                return datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
            except Exception:
                frappe.throw(f"Invalid datetime: {val}")
        frappe.throw(f"Invalid datetime: {val}")

    if doc.custom_shift_type == "Night":
        in_datetime = parse_datetime(doc.custom_shift_in_time)
        out_datetime = parse_datetime(doc.custom_shift_in_out)

        if out_datetime <= in_datetime:
            out_datetime += timedelta(days=1)

    else:
        in_datetime = make_datetime(date_val, doc.custom_in_time)
        out_datetime = make_datetime(date_val, doc.custom_out_time)

        if out_datetime < in_datetime:
            frappe.throw("Out time cannot be less than In time")

    working_hours = (out_datetime - in_datetime).total_seconds() / 3600

    attendance_name = create_or_update_attendance(
        employee=doc.employee,
        date=date_val,
        in_time=in_datetime,
        out_time=out_datetime,
        working_hours=working_hours,
        skip_shift_time_rules=True
    )

    # if attendance_name:
    #     att = frappe.get_doc("Attendance", attendance_name)
    #     att.attendance_request = doc.name
    #     att.flags.ignore_validate_update_after_submit = True
    #     att.save(ignore_permissions=True)

    # return attendance_name
    if attendance_name:
        frappe.db.set_value(
            "Attendance",
            attendance_name,
            "attendance_request",
            doc.name,
            update_modified=False   
        )

    return attendance_name

def apply_attendance_regularisation(doc):
    """
    Called from Attendance Request submit.
    Recalculate attendance using doc.custom_in_time and doc.custom_out_time.
    Remove Absent/Half-Day leaves created by scheduler and set Present.
    """

    # Target date
    att_date = doc.from_date

    # 1️⃣ Fetch existing Attendance
    attendance_name = frappe.db.exists("Attendance", {
        "employee": doc.employee,
        "attendance_date": att_date,
        "docstatus": ["!=", 2]
    })

    if not attendance_name:
        frappe.throw("Auto attendance not found for this date. Scheduler must run first.")

    att = frappe.get_doc("Attendance", attendance_name)

    # 2️⃣ Recalculate working hours
    in_datetime = make_datetime(doc.from_date, doc.custom_in_time)
    out_datetime = make_datetime(doc.from_date, doc.custom_out_time)

    if out_datetime < in_datetime:
        frappe.throw("Out time cannot be earlier than In time.")

    working_hours = (out_datetime - in_datetime).total_seconds() / 3600

    # 3️⃣ Fetch Shift thresholds
    shift_type = att.shift
    shift = frappe.db.get_value(
        "Shift Type",
        shift_type,
        ["working_hours_threshold_for_half_day", "working_hours_threshold_for_absent"],
        as_dict=True
    )

    half_day_threshold = float(shift.working_hours_threshold_for_half_day or 8)
    absent_threshold = float(shift.working_hours_threshold_for_absent or 3)

    # 4️⃣ Decide new status
    if working_hours <= absent_threshold:
        status = "Absent"
    elif working_hours < half_day_threshold:
        status = "Half Day"
    else:
        status = "Present"

    # 5️⃣ Update Attendance
    att.in_time = in_datetime
    att.out_time = out_datetime
    att.working_hours = working_hours
    att.status = status
    att.custom_attendance_request = doc.name
    att.save(ignore_permissions=True)

    if att.docstatus == 0:
        att.submit()

    # 6️⃣ Remove existing leave ledger entry (because user corrected data)
    frappe.db.sql("""
        DELETE FROM `tabLeave Ledger Entry`
        WHERE employee = %s AND from_date = %s
    """, (doc.employee, att_date))

    frappe.db.commit()

    msg = f"Attendance updated to {status} with {round(working_hours,2)} hrs and leave reversed successfully."
    return msg


def make_datetime(date_value, time_value):
    """Safely combine Date and Time into Datetime"""
    if isinstance(date_value, str):
        date_value = datetime.strptime(date_value, "%Y-%m-%d").date()

    if isinstance(time_value, timedelta):
        time_value = (datetime.min + time_value).time()

    elif isinstance(time_value, str):
        try:
            time_value = datetime.strptime(time_value, "%H:%M:%S").time()
        except:
            try:
                time_value = datetime.strptime(time_value, "%H:%M").time()
            except:
                frappe.throw("Invalid time format")

    if not isinstance(date_value, date) or not isinstance(time_value, time):
        frappe.throw("Invalid date or time format")

    return datetime.combine(date_value, time_value)


def get_datetime_object(value):
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return value


def is_within_time(check_time, start, end):
    return start <= check_time <= end
def attach_date(att_date, time_value):

    if isinstance(att_date, str):
        att_date = datetime.fromisoformat(att_date).date()

    if isinstance(time_value, str):
        if len(time_value) <= 8:
            return datetime.combine(att_date, datetime.strptime(time_value, "%H:%M:%S").time())

        return datetime.fromisoformat(time_value)

    return time_value


def get_shift_details(shift_name):
    if not shift_name:
        return None

    return frappe.db.get_value(
        "Shift Type",
        shift_name,
        [
            "start_time",
            "end_time",
            "working_hours_threshold_for_half_day",
            "working_hours_threshold_for_absent"
        ],
        as_dict=True
    )


def get_working_hours(in_time, out_time):
    if not in_time or not out_time:
        return 0

    diff = out_time - in_time
    return round(diff.total_seconds() / 3600, 2)

def get_attendance_status(working_hours, shift_details):

    half_day_threshold = float(shift_details.working_hours_threshold_for_half_day or 7.5)
    absent_threshold   = float(shift_details.working_hours_threshold_for_absent or 3)

    if working_hours == 0:
        return "On Leave"

    if working_hours > 0 and working_hours <= absent_threshold:
        return "Absent"

    if absent_threshold < working_hours < half_day_threshold:
        return "Half Day"

    if working_hours >= half_day_threshold:
        return "Present"

    return "Absent"



@frappe.whitelist()
def get_manual_punch_note_html(employee, from_date, current_punch_type=None, current_name=None):
    """Get HTML note for miss punch limit status, exclude current doc from existing and include current punch once."""
    if not employee or not from_date:
        return {"count": 0, "html": ""}

    manual_punch_limit = frappe.db.get_single_value("HR Settings", "custom_manual_punch_count") or 0
    manual_punch_limit = cint(manual_punch_limit)

    ref_date = getdate(from_date)
    month = ref_date.month
    year = ref_date.year

    def punch_count(pt):
        if not pt:
            return 0
        pt = str(pt).strip().lower()
        return 2 if pt == "both" else (1 if pt in ("in", "out") else 0)

    filters = {"employee": employee, "reason": "Miss Punch", "docstatus": ["<", 2]}
    # exclude current doc if provided
    if current_name:
        filters["name"] = ["!=", current_name]

    existing = frappe.get_all(
        "Attendance Request",
        filters=filters,
        fields=["custom_punch_type", "from_date"]
    ) or []

    total = 0
    for er in existing:
        try:
            d = getdate(er.get("from_date"))
            if d.month == month and d.year == year:
                total += punch_count(er.get("custom_punch_type"))
        except Exception:
            continue

    # include current document's punch_type once (if provided)
    total += punch_count(current_punch_type)

    count = total
    html = ""

    if manual_punch_limit and count > manual_punch_limit:
        note = _("Miss Punch limit exceeded for {0}-{1}. Count: {2}/{3}").format(year, str(month).zfill(2), count, manual_punch_limit)
        html = '<div style="color:#fff;background-color:#d32f2f;padding:12px;border-radius:4px;font-weight:700;">⚠️ {0}</div>'.format(frappe.utils.escape_html(note))

    return {"count": count, "html": html}



@frappe.whitelist()
def get_employee_for_session_user():
    """Return Employee ID of the logged-in user (ignoring permissions)."""
    user = frappe.session.user

    employee = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        "name"
    )

    return {"employee": employee}



@frappe.whitelist()
def get_system_error_window():
    """Return only the required fields, ignore user permissions."""
    settings = frappe.get_single("HR Settings")

    return {
        "from_time": settings.custom_system_error_window_from,
        "to_time": settings.custom_system_error_window_to,
        "allowed_role": settings.custom_allowed_role
    }


@frappe.whitelist()
def create_auto_checkin_and_attendance(docname):
    try:
        if not docname:
            frappe.throw(_("Missing docname"))

        doc = frappe.get_doc("Attendance Request", docname)

        if not doc.employee or not doc.custom_punch_type:
            frappe.throw(_("Missing Employee or Punch Type"))

        messages = []

        if doc.custom_punch_type in ["In", "Both"] and doc.custom_in_time:
            create_checkin(
                doc.name,
                doc.employee,
                doc.custom_in_time,
                "IN",
                doc.name,
                doc.from_date
            )
            messages.append("IN checkin created")

        if doc.custom_punch_type in ["Out", "Both"] and doc.custom_out_time:
            create_checkin(
                doc.name,
                doc.employee,
                doc.custom_out_time,
                "OUT",
                doc.name,
                doc.from_date
            )
            messages.append("OUT checkin created")

        if doc.custom_in_time and doc.custom_out_time:
            attendance_msg = create_or_update_attendance_from_request(doc)
            messages.append(attendance_msg)

        recalculate_attendance_after_manual_log(doc.employee, doc.from_date)

        final_message = ", ".join(messages) if messages else "No actions performed"
        return {"status": "ok", "message": final_message}

    except Exception:
        # log full traceback for debugging, then re-raise original exception
        frappe.log_error(frappe.get_traceback(), "create_auto_checkin_and_attendance")
        raise
    
    
    
@frappe.whitelist()
def get_employee_custom_shift_type(employee, date):
    shift_name = get_employee_shift(employee, date)
 
    if not shift_name:
        return None
 
    custom_shift_type = frappe.db.get_value(
        "Shift Type",
        shift_name,
        "custom_shift_type"
    )
 
    return {
        "custom_shift_type": custom_shift_type,
        "shift_name": shift_name
    }