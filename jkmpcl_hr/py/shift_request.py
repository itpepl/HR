import frappe
from frappe.utils import getdate, today

def get_required_shift_hours(dt, branch, is_female):
    dt = getdate(dt)
    if branch == "Jammu and Kashmir Milk Producers Co-operative Ltd Cheshmashahi Srinagar":
        if 4 <= dt.month <= 9:
            return "8hours"
        return "7hours"
    elif branch == "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu":
        if is_female:
            if (4 <= dt.month <= 11) or (2 <= dt.month <= 3):
                return "8hours"
            return "7hours"
        else:
            return "8hours"



def validate(doc, event):

    # if doc.from_date and getdate(doc.from_date) < getdate(today()):
    #     frappe.throw("From Date cannot be a previous date.")

    if doc.to_date and getdate(doc.to_date) < getdate(doc.from_date):
        frappe.throw("To Date cannot be before From Date.")
    # elif doc.to_date and not doc.from_date and getdate(doc.to_date) < getdate(today()):
    #     frappe.throw("To Date cannot be a previous date.")
    
    validate_shift_hours(doc)


def on_submit(doc, event):
    
    try:
        notification_doc = frappe.db.get_value(
                    "Notification", "Shift Request Submitted", ["subject", "message"], as_dict=True
        )
        
        emp_user = frappe.db.get_value("Employee", doc.employee, "user_id")
        
        if notification_doc and emp_user:
                    # doc = frappe.get_doc(doctype, docname)
            message = frappe.render_template(notification_doc.message, {"doc": doc})
            subject = frappe.render_template(notification_doc.subject, {"doc": doc})
            
            
            system_notification = frappe.get_doc(
                                {
                                    "doctype": "Notification Log",
                                    "subject": subject,
                                    "for_user": emp_user,
                                    # "type": "Energy Point",
                                    "document_type": doc.doctype,
                                    "document_name": doc.name,
                                }
                            )
            system_notification.insert(ignore_permissions=True)
                
            
            
            frappe.sendmail(
                recipients=[emp_user],
                subject=subject,
                message=message                
            )
    except Exception as e:
        frappe.throw(e)
        frappe.log_error("error_send_shift_request_notification", frappe.get_traceback())


@frappe.whitelist()
def validate_shift_hours(doc):
    
        if isinstance(doc, str):
            doc = frappe.parse_json(doc)
        if not (doc.shift_type and doc.from_date and doc.custom_branch):
            return

        
        is_female = True if frappe.db.get_value("Employee", doc.employee, "gender") == "Female" else False
        
        from_hours = get_required_shift_hours(doc.from_date, doc.custom_branch, is_female)
        to_hours = from_hours
        if doc.to_date:
            to_hours = get_required_shift_hours(doc.to_date, doc.custom_branch, is_female)

        if from_hours != to_hours:
            frappe.throw(
                f"From Date and To Date fall under different shift-hour periods "
                f"({from_hours} hours vs {to_hours} hours). "
                "Please create separate Shift Requests for each period."
            )
        
        from_date = getdate(doc.from_date)
        to_date = getdate(doc.to_date)
        if from_hours == to_hours:
            if doc.custom_branch == "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu" and (from_date <= getdate(f"{from_date.year}-12-01") and getdate(f"{from_date.year+1}-01-31") <= to_date):
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
        

# * METHOD TO GET CEO USER
@frappe.whitelist()
def get_ceo(shift_type, branch):
    
    if not frappe.db.get_value("Shift Type", shift_type, "custom_shift_type") == "24 hours":
        return {"is_ceo": 0}
        
    ceo_users = frappe.get_all(
        "Has Role",
        filters={"role": "CEO"},
        fields=["parent as user"]
    )

    if not ceo_users:
        return {"is_ceo": 0}

    ceo_user_ids = [d.user for d in ceo_users]

    # Step 2: Get Employee linked to these users with matching branch
    employees = frappe.get_all(
        "Employee",
        filters={
            "user_id": ["in", ceo_user_ids],
            "branch": branch
        },
        fields=["name", "user_id", "employee_name", "branch"]
    )

    if not employees:
        return {"is_ceo": 0}

    return {"is_ceo": 1, "user": employees[0].user_id}