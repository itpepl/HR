
import frappe
from frappe.utils import get_first_day, get_last_day, today, add_days
from frappe import _
from frappe.utils import now



@frappe.whitelist()
def check_in(employeeId, latitude=None, longitude=None):

    try:
        if not employeeId:
            frappe.throw(_("Employee ID is required"))

        if not latitude or not longitude:
            frappe.throw(_("Latitude and Longitude are required"))

        attendance = frappe.get_doc(
            {
                "doctype": "Employee Checkin",
                "employee": employeeId,
                "check_in": now(),
                "latitude": float(latitude),
                "longitude": float(longitude),
                "log_type": "IN",
            }
        )

        attendance.insert()
        frappe.db.commit()

        frappe.logger().info(f"Check-in record created successfully: {attendance.name}")

    except Exception as e:
        frappe.logger().error(f"Error creating check-in record: {str(e)}")
        frappe.clear_messages()

        frappe.local.response["message"] = {
            "success": False,
            "message": str(e),
            "data": None,
        }

    else:
        frappe.local.response["message"] = {
            "success": True,
            "message": _("Check-In successful"),
            "data": {
                "name": attendance.name,
                "employee": employeeId,
                "check_in_time": attendance.check_in,
                "latitude": latitude,
                "longitude": longitude,
                "log_type": "IN"
            },
        }

@frappe.whitelist()
def check_out(employeeId, latitude=None, longitude=None):

    try:
        if not employeeId:
            frappe.throw(_("Employee ID is required"))

        if not latitude or not longitude:
            frappe.throw(_("Latitude and Longitude are required"))

        # Get Last IN record
        check_in_records = frappe.get_all(
            "Employee Checkin",
            filters={
                "employee": employeeId,
                "log_type": "IN"
            },
            order_by="creation desc",
            limit=1,
        )

        if not check_in_records:
            frappe.throw(_("No Check-In record found for this employee"))

        last_checkin = check_in_records[0].name

        check_out_record = frappe.get_doc(
            {
                "doctype": "Employee Checkin",
                "employee": employeeId,
                "check_out": now(),
                "latitude": float(latitude) or None,
                "longitude": float(longitude),
                "log_type": "OUT",
                "related_check_in": last_checkin,
            }
        )

        check_out_record.insert()
        frappe.db.commit()

        frappe.logger().info(f"Check-out record created successfully: {check_out_record.name}")

    except Exception as e:
        frappe.logger().error(f"Error creating check-out record: {str(e)}")
        frappe.clear_messages()

        frappe.local.response["message"] = {
            "success": False,
            "message": str(e),
            "data": None
        }

    else:
        frappe.local.response["message"] = {
            "success": True,
            "message": _("Check-out successful"),
            "data": {
                "name": check_out_record.name,
                "employee": employeeId,
                "check_out_time": check_out_record.check_out,
                # "latitude": latitude,
                # "longitude": longitude,
                "log_type": "OUT",
                "related_check_in": last_checkin
            }
        }



@frappe.whitelist()
def checkInLog(employeeId=None):

    try:
        if not employeeId:
            frappe.throw(_("Employee ID is required"))

        final_data = []

        checkInData = frappe.get_list(
            "Employee Checkin",
            filters={
                "employee": employeeId,
                "creation": ["between", [today() + " 00:00:00", today() + " 23:59:59"]],
            },
            order_by="creation desc",
            fields=["employee", "employee_name", "log_type", "time", "name"],
        )

        for data in checkInData:
            final_data.append(
                {
                    "employee": data.get("employee"),
                    "employee_name": data.get("employee_name"),
                    "log_type": data.get("log_type"),
                    "time": data.get("time").strftime("%H:%M:%S") if data.get("time") else None,
                }
            )

    except Exception as e:
        frappe.log_error("Error While Fetching Check-In Log", str(e))
        frappe.clear_messages()

        frappe.local.response["message"] = {
            "success": False,
            "message": str(e),
            "data": None
        }

    else:
        frappe.local.response["message"] = {
            "success": True,
            "message": _("Check-in log fetched successfully"),
            "data": final_data
        }