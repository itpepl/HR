import frappe
from frappe import _
from frappe.utils import get_datetime, flt
from frappe.utils.file_manager import save_file
from geopy.geocoders import Nominatim


geolocator = Nominatim(
    user_agent="employee_activity"
)

def save_image(doctype, docname):
    """
    Reads uploaded image from request.files (multipart/form-data)
    and attaches it to the given document.
    """

    if not frappe.request.files:
        return None

    file_obj = frappe.request.files.get("image")
    if not file_obj:
        return None

    content = file_obj.read()
    filename = file_obj.filename or f"{docname}_photo.jpg"

    file_doc = save_file(
        fname=filename,
        content=content,
        dt=doctype,
        dn=docname,
        is_private=0,
    )

    return file_doc.file_url


@frappe.whitelist()
def create_employee_activity():
    try:
        data = frappe.form_dict

        employee = data.get("employee")
        request_date = data.get("request_date")
        contact_person = data.get("contact_person_name")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        custom_ta_da_mode = data.get("custom_ta_da_mode")
        purpose = data.get("purpose")
        visit_location = data.get("visit_location")
        activity_details = data.get("activity_details")
        remarks = data.get("remarks")

        emp_latitude = flt(latitude)
        emp_longitude = flt(longitude)

        custom_location = ""
        
        try:
    
            location = geolocator.reverse(
                f"{emp_latitude},{emp_longitude}",
                exactly_one=True,
                timeout=5
            )
    
            if location:
                custom_location = location.address
    
        except Exception:
    
            frappe.log_error(
                frappe.get_traceback(),
                "Employee Activity Reverse Geocoding"
            )

        if not employee:
            frappe.throw(_("Employee is mandatory."))

        doc = frappe.get_doc({
            "doctype": "Employee Activity",
            "employee": employee,
            "request_date": get_datetime(request_date) if request_date else None,
            "contact_person": contact_person,
            "latitude": latitude,
            "longitude": longitude,
            "custom_ta_da_mode": custom_ta_da_mode,
            "purpose": purpose,
            "visit_location": visit_location,
            "custom_location": custom_location,
            "activity_details": activity_details,
            "remarks": remarks,
        })

        doc.insert(ignore_permissions=True)

        # Save image attachment
        image_url = save_image(doc.doctype, doc.name)

        frappe.db.commit()

        return {
            "success": True,
            "message": "Employee Activity created successfully.",
            "name": doc.name,
            "image": image_url
        }

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Employee Activity API")

        return {
            "success": False,
            "message": frappe.get_traceback()
        }