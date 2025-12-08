import frappe
from frappe.utils import getdate

def get_required_shift_hours(dt, branch):
    dt = getdate(dt)
    if branch == "Srinagar":
        if 4 <= dt.month <= 9:
            return "8hours"
        return "7hours"
    elif branch == "Jammu":
        if (4 <= dt.month <= 11) or (2 <= dt.month <= 3):
            return "8hours"
        return "7hours"



def validate(doc, event):
    validate_shift_hours(doc)


@frappe.whitelist()
def validate_shift_hours(doc):
    
        if isinstance(doc, str):
            doc = frappe.parse_json(doc)
        if not (doc.shift_type and doc.from_date and doc.custom_branch):
            return

        
        from_hours = get_required_shift_hours(doc.from_date, doc.custom_branch)
        to_hours = from_hours
        if doc.to_date:
            to_hours = get_required_shift_hours(doc.to_date, doc.custom_branch)

        if from_hours != to_hours:
            frappe.throw(
                f"From Date and To Date fall under different shift-hour periods "
                f"({from_hours} hours vs {to_hours} hours). "
                "Please create separate Shift Requests for each period."
            )
        
        from_date = getdate(doc.from_date)
        to_date = getdate(doc.to_date)
        if from_hours == to_hours:
            if doc.custom_branch == "Jammu" and (from_date <= getdate(f"{from_date.year}-12-01") and getdate(f"{from_date.year+1}-01-31") <= to_date):
                frappe.throw(
                    f" 7 Hours shift fall between the from date and to date "
                    "Please create separate Shift Requests for each period."
                )
            
        shift_hours = frappe.db.get_value("Shift Type", doc.shift_type, "custom_hours")

        if not shift_hours:
            return

        required_hours = from_hours

        if shift_hours != required_hours:
            frappe.throw(
                f"Selected Shift Type '{doc.shift_type}' is a {shift_hours}-hour shift, "
                f"but for the selected dates only {required_hours}-hour shifts are allowed."
            )
        
        