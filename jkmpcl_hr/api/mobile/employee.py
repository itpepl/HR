import frappe
from frappe.utils import getdate, nowdate
from datetime import timedelta  
import frappe
from frappe.utils import today
from frappe.utils import strip_html
from jkmpcl_hr.py.utils import get_emp_reporting_manager
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
                "shift_request_approver",
                "designation",
                "custom_attendance_source"
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

            if getdate(latest_checkin["time"]) == getdate(nowdate()):

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
            else:
                isCheckedIn = False
                checkInData = {
                    "log_type": "OUT",
                    "time": "00:00:00",
                    "attachments": None,
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
                # "shift_request_approver": employee.get("shift_request_approver", "N/A"),
                "shift_request_approver" : get_emp_reporting_manager(employee_name),
                "custom_attendance_source":employee.get("custom_attendance_source","N/A")

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


# @frappe.whitelist()
# def get_upcoming_holidays(employeeId=None):
#     try:
#         if not employeeId:
#             frappe.throw("Employee ID is required")

#         final_result = []
#         today = getdate(nowdate())
#         start_of_month = today.replace(day=1)
#         if today.month == 12:
#             end_of_month = today.replace(
#                 year=today.year + 1, month=1, day=1
#             ) - timedelta(days=1)
#         else:
#             end_of_month = today.replace(
#                 month=today.month + 1, day=1
#             ) - timedelta(days=1)

#         employeeRecord = frappe.get_doc("Employee", employeeId)
#         employeeHolidayList = employeeRecord.get("holiday_list")

#         if not employeeHolidayList:
#             frappe.throw("Holiday list not found for this employee")
#         holidays = frappe.get_doc("Holiday List", employeeHolidayList)
#         print(holidays,start_of_month,end_of_month)
#         for row in holidays.get("holidays"):
#             print(row.holiday_date)
            
#             if (
#                 row.holiday_date >= start_of_month
#                 and row.holiday_date <= end_of_month
#                 and row.weekly_off == 0
#             ):

#                 # Date formatting
#                 holiday_date = getdate(row.holiday_date)
#                 day = holiday_date.day
#                 month = holiday_date.strftime("%b").upper()    # OCT
#                 full_date = holiday_date.strftime("%A, %d %B %Y")  # Thursday, 02 October 2025

#                 final_result.append({
#                     "date": row.holiday_date,
#                     "day": day,
#                     "month": month,
#                     "display_date": f"{day} {month}",     # 2 OCT
#                     "full_date": full_date,              # Thursday, 02 October 2025
#                     "occasion": strip_html(row.description) if row.description else ""
#                 })

#     except Exception as e:
#         frappe.log_error("Error While Getting Upcoming Holidays", str(e))
#         frappe.clear_messages()

#         frappe.local.response["message"] = {
#             "success": False,
#             "message": str(e),
#             "data": None
#         }

#     else:
#         frappe.local.response["message"] = {
#             "success": True,
#             "message": "Upcoming holidays loaded successfully",
#             "data": final_result
#         }
@frappe.whitelist()
def get_upcoming_holidays(employeeId=None):
    try:
        if not employeeId:
            frappe.throw("Employee ID is required")

        final_result = []

        today = getdate(nowdate())
        start_of_year = today.replace(month=1, day=1)
        end_of_year = today.replace(month=12, day=31)

        employee = frappe.get_doc("Employee", employeeId)
        holiday_list_name = employee.holiday_list

        if not holiday_list_name:
            frappe.throw("Holiday list not found for this employee")

        holiday_list = frappe.get_doc("Holiday List", holiday_list_name)

        # for row in holiday_list.holidays:
        #     if (
        #         row.holiday_date
        #         and start_of_year <= row.holiday_date <= end_of_year
        #         and not row.weekly_off
        #     ):
        #         holiday_date = getdate(row.holiday_date)

        #         final_result.append({
        #             "date": row.holiday_date,
        #             "day": holiday_date.day,
        #             "month": holiday_date.strftime("%b").upper(),
        #             "display_date": holiday_date.strftime("%d %b"),
        #             "full_date": holiday_date.strftime("%A, %d %B %Y"),
        #             "occasion": strip_html(row.description or ""),
        #             "restricted_holiday": row.custom_is_restricted_holiday
        #         })

        valid_holidays = []
        restricted_rows = {}

        # -----------------------------
        # First Pass: Filter Holidays
        # -----------------------------
        for row in holiday_list.holidays:
            if (
                row.holiday_date
                and start_of_year <= row.holiday_date <= end_of_year
                and not row.weekly_off
            ):
                valid_holidays.append(row)

                # Collect restricted holidays with their pair date
                if (
                    row.custom_is_restricted_holiday
                    and row.custom_restricted_holiday_date
                ):
                    restricted_rows[getdate(row.holiday_date)] = getdate(
                        row.custom_restricted_holiday_date
                    )

        # -----------------------------------
        # Second Pass: Create RH Pair Mapping
        # -----------------------------------
        rh_pair_map = {}
        visited = set()
        pair_counter = 1

        for holiday_date, pair_date in restricted_rows.items():

            # Skip if already assigned
            if holiday_date in visited:
                continue

            pair_label = f"RH{pair_counter}"

            # Assign same label to both dates
            rh_pair_map[holiday_date] = pair_label
            rh_pair_map[pair_date] = pair_label

            visited.add(holiday_date)
            visited.add(pair_date)

            pair_counter += 1

        # -----------------------------------
        # Third Pass: Build Final Response
        # -----------------------------------
        for row in valid_holidays:
            holiday_date = getdate(row.holiday_date)

            final_result.append({
                "date": row.holiday_date,
                "day": holiday_date.day,
                "month": holiday_date.strftime("%b").upper(),
                "display_date": holiday_date.strftime("%d %b"),
                "full_date": holiday_date.strftime("%A, %d %B %Y"),
                "occasion": strip_html(row.description or ""),
                "restricted_holiday": row.custom_is_restricted_holiday,
                "rh_pair": rh_pair_map.get(holiday_date)
            })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error While Getting Year Holidays")
        frappe.local.response["message"] = {
            "success": False,
            "message": str(e),
            "data": None
        }

    else:
        frappe.local.response["message"] = {
            "success": True,
            "message": "Year-wise holidays loaded successfully",
            "data": final_result
        }
