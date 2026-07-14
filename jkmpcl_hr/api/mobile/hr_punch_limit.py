import frappe
from frappe.utils import today


@frappe.whitelist()
def get_employee_info(employee_code):
    """
    API to get employee location details based on HQ type
    along with HR Settings punch limit configuration.
    """

    employee = frappe.get_doc("Employee", employee_code)

    # Employee Geofence Enable/Disable
    enable = employee.custom_enabled

    # If disabled, don't validate anything
    if not enable:
        return {
            "status": "success",
            "data": {
                "enable": False
            }
        }

    hq_type = employee.custom_head_quarter_type
    location_info = {}

    # -------------------------
    # Validate HQ Type
    # -------------------------
    if not hq_type:
        return {
            "status": "failed",
            "data": {
                "enable": True
            },
            "message": "Head Quarter Type is not mapped for this employee"
        }

    # -------------------------
    # Resolve location based on HQ Type
    # -------------------------

    if hq_type in ("Plant", "MCC", "BMC"):

        warehouse_name = employee.custom_warehouse

        if not warehouse_name:
            return {
                "status": "failed",
                "data": {
                    "enable": True
                },
                "message": "Warehouse is not mapped for this employee"
            }

        warehouse = frappe.get_doc("Warehouse", warehouse_name)

        location_name = warehouse.custom_location

        if not location_name:
            return {
                "status": "failed",
                "data": {
                    "enable": True
                },
                "message": f"Warehouse '{warehouse_name}' has no Location linked."
            }

        location = frappe.get_doc("Location", location_name)

        location_info = {
            "source_type": "Warehouse",
            "source_name": warehouse_name,
            "location": location_name,
            "latitude": location.latitude,
            "longitude": location.longitude,
        }

    elif hq_type == "MPP":

        supplier_name = employee.custom_supplier

        if not supplier_name:
            return {
                "status": "failed",
                "data": {
                    "enable": True
                },
                "message": "Supplier is not mapped for this employee"
            }

        supplier = frappe.get_doc("Supplier", supplier_name)

        location_name = supplier.custom_location

        if not location_name:
            return {
                "status": "failed",
                "data": {
                    "enable": True
                },
                "message": f"Supplier '{supplier_name}' has no Location linked."
            }

        location = frappe.get_doc("Location", location_name)

        location_info = {
            "source_type": "Supplier",
            "source_name": supplier_name,
            "location": location_name,
            "latitude": location.latitude,
            "longitude": location.longitude,
        }

    else:
        return {
            "status": "failed",
            "data": {
                "enable": True
            },
            "message": (
                f"Unknown Head Quarter Type '{hq_type}'. "
                "Expected one of: Plant, MCC, BMC, MPP."
            )
        }

    # -------------------------
    # HR Settings
    # -------------------------

    hr_settings = frappe.get_single("HR Settings")

    employee_department = employee.department

    punch_limit_settings = []

    for row in hr_settings.custom_punch_limit_setting:
        if row.department == employee_department:
            punch_limit_settings.append({
                "department": row.department,
                "attendance_source": row.attendnace_source,
                "punch_count": row.punch_count,
            })
            break

    geo_fence_radius = hr_settings.custom_geo_fence_radius

    # -------------------------
    # Today's Check-In Counts
    # -------------------------

    checkin_counts = frappe.db.sql("""
        SELECT
            log_type,
            COUNT(*) AS count
        FROM `tabEmployee Checkin`
        WHERE employee = %s
          AND DATE(time) = %s
        GROUP BY log_type
    """, (employee.name, today()), as_dict=True)

    in_count = 0
    out_count = 0

    for row in checkin_counts:
        if row.log_type == "IN":
            in_count = row.count
        elif row.log_type == "OUT":
            out_count = row.count

    return {
        "status": "success",
        "data": {
            "enable": True,
            "employee": {
                "employee_code": employee_code,
                "employee_name": employee.employee_name,
                "head_quarter_type": hq_type,
            },
            "location_info": location_info,
            "geo_fence_radius": geo_fence_radius,
            "punch_limit_settings": punch_limit_settings,
            "checkin_summary": {
                "date": today,
                "in_count": in_count,
                "out_count": out_count,
                "total_punches": in_count + out_count
            }
        }
    }