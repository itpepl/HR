import frappe
from hrms.hr.doctype.attendance.attendance import Attendance as ERPNextAttendance
from erpnext.controllers.status_updater import *
from hrms.hr.utils import validate_active_employee



class Attendance(ERPNextAttendance):

    def before_insert(self):
        super().before_insert()

        if self.half_day_status == "":
            self.half_day_status = None

    def validate(self):
        allowed_status = [
            "Present",
            "Absent",
            "On Leave",
            "Half Day",
            "Work From Home",
            "Partially",
        ]

        validate_status(self.status, allowed_status)

        validate_active_employee(self.employee)
        self.validate_attendance_date()
        self.validate_duplicate_record()
        self.validate_overlapping_shift_attendance()
        self.validate_employee_status()
        self.check_leave_record()
