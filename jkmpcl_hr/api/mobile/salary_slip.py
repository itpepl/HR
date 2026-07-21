import frappe
from frappe.utils import formatdate, getdate, get_url
from urllib.parse import quote


@frappe.whitelist()
def salary_slip_list():
    user = frappe.session.user

    employee = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        "name"
    )

    if not employee:
        return {
            "data": [],
            "success": False,
            "message": "Employee not found."
        }

    salary_slips = frappe.get_all(
        "Salary Slip",
        filters={
            "employee": employee,
            "docstatus": 1
        },
        fields=[
            "name",
            "start_date",
            "end_date"
        ],
        order_by="start_date desc"
    )

    base_url = get_url()
    print_format = "Salary Slip - JKMPCL"

    data = []

    for slip in salary_slips:
        download_url = (
            f"{base_url}/api/method/frappe.utils.print_format.download_pdf"
            f"?doctype={quote('Salary Slip')}"
            f"&name={quote(slip.name)}"
            f"&format={quote(print_format)}"
            f"&no_letterhead=0"
        )

        data.append({
            "name": slip.name,
            "start_date": formatdate(slip.start_date, "dd-MM-yyyy"),
            "end_date": formatdate(slip.end_date, "dd-MM-yyyy"),
            "display_name": getdate(slip.start_date).strftime("%B-%Y"),
            "download_url": download_url
        })

    return {
        "data": data,
        "success": True,
        "message": "Salary Slip Fetched",
    }