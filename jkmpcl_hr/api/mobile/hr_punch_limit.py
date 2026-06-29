import frappe


@frappe.whitelist()
def get_punch_limit_settings():

    hr_setting = frappe.get_single("HR Settings")

    data = []

    for row in hr_setting.custom_punch_limit_setting:
        data.append({
            "department": row.department,
            "attendnace_source":row.attendnace_source,
            "punch_count": row.punch_count
        })

    return {
        "status": "success",
        "data": data
    }




@frappe.whitelist()
def get_employee_info(employee_code):
    """
    API to get employee location details based on HQ type
    along with HR Settings punch limit configuration.

    Args:
        employee_code (str): Employee ID / Code

    Returns:
        dict: Employee location info + punch limit settings
    """

    # -------------------------
    # 1. Fetch Employee doc
    # -------------------------
    employee = frappe.get_doc("Employee", employee_code)

    hq_type = employee.custom_head_quarter_type
    location_info = {}
    if not hq_type:
        return {
            "status": "failed",
            "data": {},
            "message": "Head Quarter Type is not set for this employee."
        }
    # -------------------------
    # 2. Resolve location based on HQ Type
    # -------------------------
    if hq_type in ("Plant", "MCC", "BMC"):
        # Fetch linked Warehouse
        warehouse_name = employee.custom_warehouse
        if not warehouse_name:
            frappe.throw(
                f"Employee {employee_code} has HQ Type '{hq_type}' "
                f"but no Warehouse linked (custom_warehouse is empty)."
            )

        warehouse = frappe.get_doc("Warehouse", warehouse_name)
        location_name = warehouse.custom_location

        if not location_name:
            frappe.throw(
                f"Warehouse '{warehouse_name}' has no Location linked "
                f"(custom_location is empty)."
            )

        location = frappe.get_doc("Location", location_name)

        location_info = {
            "source_type": "Warehouse",
            "source_name": warehouse_name,
            "location": location_name,
            "latitude": location.latitude,
            "longitude": location.longitude,
        }

    elif hq_type == "MPP":
        # Fetch linked Supplier
        supplier_name = employee.custom_supplier
        if not supplier_name:
            frappe.throw(
                f"Employee {employee_code} has HQ Type 'MPP' "
                f"but no Supplier linked (custom_supplier is empty)."
            )

        supplier = frappe.get_doc("Supplier", supplier_name)
        location_name = supplier.custom_location

        if not location_name:
            frappe.throw(
                f"Supplier '{supplier_name}' has no Location linked "
                f"(custom_location is empty)."
            )

        location = frappe.get_doc("Location", location_name)

        location_info = {
            "source_type": "Supplier",
            "source_name": supplier_name,
            "location": location_name,
            "latitude": location.latitude,
            "longitude": location.longitude,
        }

    else:
        frappe.throw(
            f"Unknown custom_head_quarter_type '{hq_type}' "
            f"for employee {employee_code}. "
            f"Expected one of: Plant, MCC, BMC, MPP."
        )

    # -------------------------
    # 3. Fetch HR Settings punch limit settings + geo fence radius
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
            break  # No need to loop further once matched

    geo_fence_radius = hr_settings.custom_geo_fence_radius
        # -------------------------
    # 4. Get Today's Check-In / Check-Out Counts
    # -------------------------
    today = frappe.utils.today()

    checkin_counts = frappe.db.sql("""
        SELECT
            log_type,
            COUNT(*) AS count
        FROM `tabEmployee Checkin`
        WHERE employee = %s
          AND DATE(time) = %s
        GROUP BY log_type
    """, (employee.name, today), as_dict=True)

    in_count = 0
    out_count = 0

    for row in checkin_counts:
        if row.log_type == "IN":
            in_count = row.count
        elif row.log_type == "OUT":
            out_count = row.count

    # -------------------------
    # 5. Build final response
    # -------------------------
    return {
        "status": "success",
        "data": {
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