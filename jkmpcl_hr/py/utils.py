import frappe
from frappe.utils import today, getdate

@frappe.whitelist()
def get_emp_reporting_manager(emp_id, as_on_date=today()):
    rh_dict = frappe.db.get_all("Approver", {"parent":emp_id, "effective_from":["<=", getdate(as_on_date)], "parentfield": "custom_reporting_manager"}, "user", order_by="effective_from desc", limit=1)

    return rh_dict[0]["user"] if rh_dict else None
    