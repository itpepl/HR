import frappe
from frappe import _, cint
from frappe.utils import getdate, get_link_to_form, nowdate
from hrms.hr.doctype.attendance_request.attendance_request import AttendanceRequest as HRMSAttendanceRequest, OverlappingAttendanceRequestError


class AttendanceRequest(HRMSAttendanceRequest):
    def validate(self):
        from hrms.hr.utils import validate_active_employee
        validate_active_employee(self.employee)
        self.validate_dates_custom()
        self.validate_request_overlap_custom()
        self.validate_no_attendance_to_create()

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
        return 2 if pt == "both" else (1 if pt in ("in", "out") else 0)

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
