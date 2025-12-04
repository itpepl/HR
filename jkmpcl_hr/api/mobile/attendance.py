import frappe
from frappe.utils import getdate, nowdate
from datetime import timedelta  
from datetime import datetime
import frappe,uuid, os, mimetypes, calendar, re

@frappe.whitelist()
def get_attendance(employeeId, date=None, from_date=None, to_date=None, status=None):
    try:
        if not employeeId:
            frappe.throw("Employee ID is required")

        # If from_date & to_date given → use them
        if from_date and to_date:
            start_date = from_date
            end_date = to_date

        # If only date is given → pick whole month
        elif date:
            specific_date = datetime.strptime(date, "%Y-%m-%d").date()
            current_month = specific_date.month
            current_year = specific_date.year
            total_days_in_month = calendar.monthrange(current_year, current_month)[1]

            start_date = f"{current_year}-{current_month:02d}-01"
            end_date = f"{current_year}-{current_month:02d}-{total_days_in_month}"

        else:
            frappe.throw("Either 'date' OR 'from_date' and 'to_date' is required.")

        # Base filters
        month_filters = [
            ["employee", "=", employeeId],
            ["attendance_date", "between", [start_date, end_date]],
        ]

        # Status filter (optional, allows single or comma separated)
        if status:
            if "," in status:
                status_list = [s.strip() for s in status.split(",")]
                month_filters.append(["status", "in", status_list])
            else:
                month_filters.append(["status", "=", status])

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
            "Attendance",
            filters=month_filters,
            fields=fields,
            order_by="attendance_date asc"
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
        frappe.local.response["message"] = {
            "success": True,
            "message": "Attendance records retrieved successfully.",
            "data": {
                "from_date": start_date,
                "to_date": end_date,
                "records": month_attendance_records or []
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


@frappe.whitelist(allow_guest=True)
def attendance_status_list():
    """
    Returns a list of predefined attendance statuses with colors
    """

    status_list = [
        {
            "status": "Present",
            "color": "#28a745",     # Green
            "code": "P"
        },
        {
            "status": "Absent",
            "color": "#dc3545",     # Red
            "code": "A"
        },
        {
            "status": "Week Off",
            "color": "#1f2a56",     # Dark Blue
            "code": "WO"
        },
        {
            "status": "Holiday",
            "color": "#6f7dff",     # Purple/Blue
            "code": "H"
        },
        {
            "status": "Leave Not Approved",
            "color": "#ffc0cb",     # Light Pink
            "code": "LNA"
        },
        {
            "status": "Leave Approved",
            "color": "#9e9e9e",     # Grey
            "code": "LA"
        },
        {
            "status": "Half Day",
            "color": "#ffa500",     # Orange
            "code": "HD"
        },
        {
            "status": "Work From Home",
            "color": "#00bcd4",     # Sky Blue
            "code": "WFH"
        }
    ]

    return {
        "success": True,
        "data": status_list
    }
