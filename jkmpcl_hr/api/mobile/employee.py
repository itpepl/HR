import frappe
from frappe.utils import getdate, nowdate
from datetime import timedelta  
import frappe
from frappe.utils import today

@frappe.whitelist(allow_guest=True)
def get_employee_details(email):

    try:
        employee = frappe.get_all(
            "Employee",
            filters={"user_id": email},
            fields=[
                "name",
                "employee_name",
                "department",
                "gender",
                "date_of_birth",
                "date_of_joining",
                "blood_group",
                "company",
                "grade",
                "branch",
                "reports_to",
                "employment_type",
                "personal_email",
                "cell_number",
                "company_email",
                "designation",
            ],
        )

        if not employee:
            frappe.throw("No employee record found for the provided email")

        employee = employee[0]
        employee_name = employee.get("name")

        # Get today's checkin records
        checkinRecords = frappe.get_list(
            "Employee Checkin",
            filters={
                "employee": employee_name,
                # "creation": ["Timespan", "today"],
            },
            fields=["name", "log_type", "time"],
            order_by="creation desc",
        )
        isCheckedIn = checkinRecords[0]["log_type"] == "IN" if checkinRecords else False
        isAcknowledged = bool(checkinRecords)
        showPunchIn = False if len(checkinRecords) >= 4 else True

        checkInData = {}
        if checkinRecords:
            latest_checkin = checkinRecords[0]

            attachment = frappe.db.get_value(
                "File",
                {
                    "attached_to_doctype": "Employee Checkin",
                    "attached_to_name": latest_checkin["name"],
                },
                "file_url",
            )

            checkInData = {
                "log_type": latest_checkin["log_type"],
                "time": latest_checkin["time"].strftime("%H:%M:%S") if latest_checkin.get("time") else None,
                "attachments": frappe.utils.get_url(attachment) if attachment else None,
            }

        # Get photo
        photo = frappe.db.get_value("File", {"attached_to_name": employee_name}, "file_url")

        # Check if person is reporting manager
        report_to_status = (
            True
            if frappe.get_all("Employee", filters={"reports_to": employee_name}, pluck="name")
            else False
        )

        data = {
            "company_info": {
                "company": employee.get("company", "N/A"),
                "department": employee.get("department", "N/A"),
                "branch": employee.get("branch", "N/A"),
               
            },
            "employee_info": {
                "name": employee_name,
                "grade": employee.get("grade", "N/A"),
                "reports_to": employee.get("reports_to", "N/A"),
                "employment_type": employee.get("employment_type", "N/A"),
                "designation": employee.get("designation", "N/A"),
                "employee_name": employee.get("employee_name", "N/A"),
                "gender": employee.get("gender", "N/A"),
                "date_of_birth": employee.get("date_of_birth", "N/A"),
                "date_of_joining": employee.get("date_of_joining", "N/A"),
            },
            "contact_info": {
                "personal_email": employee.get("personal_email", "N/A"),
                "cell_number": employee.get("cell_number", "N/A"),
                "company_email": employee.get("company_email", "N/A"),
                "parent_email": employee.get("custom_parent_email", "N/A"),
            },
            "photo_url": (
                frappe.utils.get_url(photo)
                if photo
                else frappe.utils.get_url("/assets/frappe/images/ui/no_image.jpg")
            ),
            "report_to_status": report_to_status,
            "is_checked_in": isCheckedIn,
            "check_in_data": checkInData,
            "isAcknowledged": isAcknowledged,
            "showPunchIn": showPunchIn,
        }

    except Exception as e:
        frappe.log_error("Error in get_employee_details", str(e))
        frappe.clear_messages()

        frappe.local.response["message"] = {
            "success": False,
            "message": str(e),
            "data": None,
        }

    else:
        frappe.local.response["message"] = {
            "success": True,
            "message": "Employee details loaded successfully",
            "data": data,
        }


@frappe.whitelist()
def get_upcoming_holidays(employeeId=None):
    try:
        if not employeeId:
            frappe.throw("Employee ID is required")

        final_result = []
        today = getdate(nowdate())
        start_of_month = today.replace(day=1)

        if today.month == 12:
            end_of_month = today.replace(
                year=today.year + 1, month=1, day=1
            ) - timedelta(days=1)
        else:
            end_of_month = today.replace(
                month=today.month + 1, day=1
            ) - timedelta(days=1)

        employeeRecord = frappe.get_doc("Employee", employeeId)
        employeeHolidayList = employeeRecord.get("holiday_list")

        if not employeeHolidayList:
            frappe.throw("Holiday list not found for this employee")

        holidays = frappe.get_doc("Holiday List", employeeHolidayList)

        for row in holidays.get("holidays"):
            if (
                row.holiday_date >= start_of_month
                and row.holiday_date <= end_of_month
                and row.weekly_off == 0
            ):

                # Date formatting
                holiday_date = getdate(row.holiday_date)
                day = holiday_date.day
                month = holiday_date.strftime("%b").upper()    # OCT
                full_date = holiday_date.strftime("%A, %d %B %Y")  # Thursday, 02 October 2025

                final_result.append({
                    "date": row.holiday_date,
                    "day": day,
                    "month": month,
                    "display_date": f"{day} {month}",     # 2 OCT
                    "full_date": full_date,              # Thursday, 02 October 2025
                    "occasion": row.description
                })

    except Exception as e:
        frappe.log_error("Error While Getting Upcoming Holidays", str(e))
        frappe.clear_messages()

        frappe.local.response["message"] = {
            "success": False,
            "message": str(e),
            "data": None
        }

    else:
        frappe.local.response["message"] = {
            "success": True,
            "message": "Upcoming holidays loaded successfully",
            "data": final_result
        }
