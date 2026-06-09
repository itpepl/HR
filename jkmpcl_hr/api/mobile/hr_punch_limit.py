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