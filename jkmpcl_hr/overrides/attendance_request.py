import frappe
from frappe import _, cint
from frappe.utils import getdate, get_link_to_form, nowdate
from hrms.hr.doctype.attendance_request.attendance_request import AttendanceRequest as HRMSAttendanceRequest, OverlappingAttendanceRequestError
from datetime import datetime, time as time_obj
from datetime import datetime, date
from datetime import datetime, time, timedelta
class AttendanceRequest(HRMSAttendanceRequest):
    def validate(self):
        from hrms.hr.utils import validate_active_employee
        validate_active_employee(self.employee)
        self.validate_dates_custom()
        self.validate_request_overlap_custom()
        self.validate_no_attendance_to_create()
    def on_submit(self):
        """Runs when Attendance Request is submitted"""
        self.create_auto_checkin_and_attendance()

    def create_auto_checkin_and_attendance(self):

        if not self.employee or not self.custom_punch_type:
            return

        try:
            if self.custom_punch_type in ["In", "Both"] and self.custom_in_time:
                create_checkin(
                    self.employee,
                    self.custom_in_time,
                    "IN",
                    self.name,
                    self.from_date
                )

            if self.custom_punch_type in ["Out", "Both"] and self.custom_out_time:
                create_checkin(
                    self.employee,
                    self.custom_out_time,
                    "OUT",
                    self.name,
                    self.from_date
                )

            if self.custom_in_time and self.custom_out_time:
                create_attendance_from_request(self)

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Attendance Request Error")
            frappe.throw(str(e))
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
        overlapping_request = (
            frappe.qb.from_(Request)
            .select(Request.name)
            .where(
                (Request.employee == self.employee)
                & (Request.docstatus < 2)
                & (Request.name != self.name)
                & (self.from_date == Request.from_date)
            )
        ).run(as_dict=True)
        if overlapping_request:
            self.throw_overlap_error(overlapping_request[0].name)

    def throw_overlap_error(self, overlapping_request: str):
        msg = _("Employee {0} already has an Attendance Request {1} that overlaps with this date").format(
            frappe.bold(self.employee),
            get_link_to_form("Attendance Request", overlapping_request),
        )
        frappe.throw(msg, title=_("Overlapping Attendance Request"), exc=OverlappingAttendanceRequestError)
    
def create_checkin(employee, time_value, log_type, attendance_request, att_date=None):

    if not att_date:
        att_date = date.today()
    else:
        if isinstance(att_date, str):
            att_date = datetime.fromisoformat(att_date).date()

    if isinstance(time_value, str) and len(time_value) <= 8:
        time_value = datetime.combine(att_date, datetime.strptime(time_value, "%H:%M:%S").time())

    elif isinstance(time_value, str):
        time_value = datetime.fromisoformat(time_value)

    exists = frappe.db.exists("Employee Checkin", {
        "employee": employee,
        "time": time_value,
        "log_type": log_type
    })

    if exists:
        return

    frappe.get_doc({
        "doctype": "Employee Checkin",
        "employee": employee,
        "time": time_value,
        "log_type": log_type,
        "device_id": "Attendance Request",
        "attendance_request": attendance_request
    }).insert(ignore_permissions=True)

    frappe.db.commit()


from datetime import datetime
import frappe


def create_attendance_from_request(doc):

    shift_type = frappe.db.get_value("Employee", doc.employee, "default_shift")

    if not shift_type:
        frappe.throw(f"No default shift found for employee {doc.employee}")

    shift = frappe.db.get_value(
        "Shift Type",
        shift_type,
        [
            "working_hours_threshold_for_half_day",
            "working_hours_threshold_for_absent"
        ],
        as_dict=True
    )

    in_datetime = make_datetime(doc.from_date, doc.custom_in_time)
    out_datetime = make_datetime(doc.from_date, doc.custom_out_time)

    if out_datetime < in_datetime:
        frappe.throw("Out time cannot be less than In time")

    working_hours = (out_datetime - in_datetime).total_seconds() / 3600
    half_day_threshold = float(shift.working_hours_threshold_for_half_day or 8)
    absent_threshold   = float(shift.working_hours_threshold_for_absent or 3)

    if working_hours == 0:
        status = "On Leave"

    elif 0 < working_hours <= absent_threshold:
        status = "Absent"

    elif absent_threshold < working_hours < half_day_threshold:
        status = "Half Day"

    else:
        status = "Present"
    attendance_name = frappe.db.get_value("Attendance", {
        "employee": doc.employee,
        "attendance_date": doc.from_date,
        "docstatus": ["!=", 2]
    })
    if attendance_name:

        att = frappe.get_doc("Attendance", attendance_name)

        total_hours = float(att.working_hours or 0) + float(working_hours)

        if not att.in_time or in_datetime < att.in_time:
            final_in = in_datetime
        else:
            final_in = att.in_time

        if not att.out_time or out_datetime > att.out_time:
            final_out = out_datetime
        else:
            final_out = att.out_time

        final_status = get_attendance_status(total_hours, shift)

        frappe.db.set_value(
            "Attendance",
            attendance_name,
            {
                "working_hours": total_hours,
                "status": final_status,
                "in_time": final_in,
                "out_time": final_out
            },
            update_modified=True
        )

        frappe.db.commit()
        return


    # Create Attendance
    attendance = frappe.get_doc({
        "doctype": "Attendance",
        "employee": doc.employee,
        "attendance_date": doc.from_date,
        "in_time": in_datetime,
        "out_time": out_datetime,
        "status": status,
        "working_hours": working_hours,
        "shift": shift_type
    })

    attendance.insert(ignore_permissions=True)
    attendance.submit()

    frappe.msgprint(f"Attendance created: {status} ({round(working_hours,2)} hrs)")


from datetime import datetime, date, time

def make_datetime(date_value, time_value):
    """Safely combine Date and Time into Datetime"""

    if isinstance(date_value, str):
        date_value = datetime.strptime(date_value, "%Y-%m-%d").date()

    if isinstance(time_value, str):
        time_value = datetime.strptime(time_value, "%H:%M:%S").time()

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
def get_manual_punch_note_html(employee, from_date):
    """Get HTML note for manual punch limit status, including current document."""
    if not employee or not from_date:
        return {"count": 0, "html": ""}
    
    manual_punch_limit = frappe.db.get_single_value("HR Settings", "custom_manual_punch_count") or 0
    manual_punch_limit = cint(manual_punch_limit)

    ref_date = getdate(from_date)
    month = ref_date.month
    year = ref_date.year

    def punch_count(pt):
        if not pt: return 0
        pt = str(pt).strip().lower()
        return 1 if pt in ("in", "out") else 0

    existing = frappe.get_all(
        "Attendance Request",
        filters={"employee": employee, "reason": "Manual Punch", "docstatus": ["<", 2]},
        fields=["custom_punch_type", "from_date"]
    )

    total = 0
    for er in existing:
        try:
            d = getdate(er.get("from_date"))
            if d.month == month and d.year == year:
                total += punch_count(er.get("custom_punch_type"))
        except Exception:
            continue

    # Add current document punch count
    total += 1

    count = total
    html = ""

    if count > manual_punch_limit:
        note = _("Manual Punch limit exceeded for {0}-{1}. Count: {2}/{3}").format(year,str(month).zfill(2),count,manual_punch_limit)
        # note = _("Manual Punch limit exceeded for {0}-{1}. Count: {2}/2").format(year, str(month).zfill(2), count)
        html = '<div style="color:#fff;background-color:#d32f2f;padding:12px;border-radius:4px;font-weight:700;">⚠️ {0}</div>'.format(frappe.utils.escape_html(note))

    return {"count": count, "html": html}
