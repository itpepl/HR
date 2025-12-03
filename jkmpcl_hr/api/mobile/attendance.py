import frappe
from frappe.utils import getdate, nowdate
from datetime import timedelta  
from datetime import datetime
import frappe,uuid, os, mimetypes, calendar, re


@frappe.whitelist()
def get_attendance(employeeId, date):
    try:
        if not employeeId or not date:
            frappe.throw("Employee ID and Date are required")

        specific_date = datetime.strptime(date, "%Y-%m-%d").date()

        current_month = specific_date.month
        current_year = specific_date.year

        total_days_in_month = calendar.monthrange(current_year, current_month)[1]

        start_date = f"{current_year}-{current_month:02d}-01"
        end_date = f"{current_year}-{current_month:02d}-{total_days_in_month}"

        month_filters = [
            ["employee", "=", employeeId],
            ["attendance_date", "between", [start_date, end_date]],
        ]

        fields = [
            "name",
            "status",
            "check_in",
            "attendance_date",
            "in_time",
            "out_time",
            "working_hours"
        ]

        month_attendance_records = frappe.get_list(
            "Attendance", filters=month_filters, fields=fields
        )

    except Exception as e:
        frappe.log_error("Error While Fetching Attendance", str(e))
        frappe.clear_messages()

        frappe.local.response["message"] = {
            "success": False,
            "message": str(e),
            "data": None,
        }

    else:
        if month_attendance_records:
            frappe.local.response["message"] = {
                "success": True,
                "message": "Attendance records for the current month retrieved successfully.",
                "data": {
                    "current_month_attendance": month_attendance_records
                },
            }
        else:
            frappe.local.response["message"] = {
                "success": True,
                "message": "No attendance records found for the current month.",
                "data": {
                    "current_month_attendance": []
                },
            }
            
            
@frappe.whitelist()
def get_attendance_calendar(employeeId, date):
    try:
        if not employeeId or not date:
            frappe.throw("Employee ID and Date are required")

        from datetime import datetime, date as sys_date
        import calendar

        specific_date = datetime.strptime(date, "%Y-%m-%d").date()
        current_month = specific_date.month
        current_year = specific_date.year
        total_days = calendar.monthrange(current_year, current_month)[1]

        start_date = f"{current_year}-{current_month:02d}-01"
        end_date = f"{current_year}-{current_month:02d}-{total_days}"

        attendance_data = frappe.get_all(
            "Attendance",
            filters={
                "employee": employeeId,
                "attendance_date": ["between", [start_date, end_date]]
            },
            fields=[
                "attendance_date",
                "status",
                "in_time",
                "out_time",
                "working_hours"
            ]
        )

        attendance_map = {str(row.attendance_date): row for row in attendance_data}

        employee = frappe.get_doc("Employee", employeeId)

        holiday_map = {}
        if employee.holiday_list:
            holiday_doc = frappe.get_doc("Holiday List", employee.holiday_list)

            for h in holiday_doc.holidays:
                holiday_map[str(h.holiday_date)] = {
                    "weekly_off": h.weekly_off,
                    "description": h.description,
                    "is_half_day": h.is_half_day
                }

        month_data = []
        for d in range(1, specific_date.day + 1):

            date_obj = sys_date(current_year, current_month, d)
            print(date_obj)
            date_str = str(date_obj)

            day_data = {
                "date": date_str,
                "status": "A",
                "in_time": None,
                "out_time": None,
                "working_hours": 0
            }
            # ✅ From Holiday List
            if date_str in holiday_map:
                holiday_info = holiday_map[date_str]

                if holiday_info["weekly_off"] == 1:
                    day_data["status"] = "WO"   # Weekly Off
                else:
                    day_data["status"] = "H"    # Holiday

            # ✅ Attendance overrides all
            if date_str in attendance_map:
                record = attendance_map[date_str]

                if record.status == "Present":
                    day_data["status"] = "P"
                elif record.status == "On Leave":
                    day_data["status"] = "L"
                else:
                    day_data["status"] = "A"

                day_data["in_time"] = record.in_time
                day_data["out_time"] = record.out_time
                day_data["working_hours"] = record.working_hours

            month_data.append(day_data)

        return {
            "success": True,
            "month": f"{current_year}-{current_month}",
            "attendance": month_data
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Calendar API Error")
        return {
            "success": False,
            "message": str(e)
        }
