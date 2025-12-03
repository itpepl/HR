import requests
import frappe

@frappe.whitelist(allow_guest=True)
def sms_settings(otp1, u_mo, msg):
    # Get Fast2SMS settings from the database
    authorization = frappe.db.get_single_value("Fast2sms Settings", "authorization")
    url = frappe.db.get_single_value("Fast2sms Settings", "url")
    sender_id = frappe.db.get_single_value("Fast2sms Settings", "sender_id")
    route = frappe.db.get_single_value("Fast2sms Settings", "route")
    language = frappe.db.get_single_value("Fast2sms Settings", "language")
    valid_till = frappe.db.get_single_value("Fast2sms Settings", "valid_till")


    try:
        valid_till_seconds = int(''.join(filter(str.isdigit, valid_till)))  # Get numeric part only
    except ValueError:
        frappe.throw("Invalid valid_till value. Please provide a numeric value followed by 's' (e.g., '120s').")

    valid_till_minutes = valid_till_seconds // 60  # Convert to minutes
    valid_till_formatted = f"{valid_till_minutes} min"
    flash = frappe.db.get_single_value("Fast2sms Settings", "flash")
    message = 178701
    variables_values = f"{otp1}|{valid_till_formatted}"
    numbers = f"{u_mo}"

    querystring = {
        "authorization": authorization,
        "sender_id": sender_id,
        "message": message,
        "variables_values": variables_values,
        "route": route,
        "numbers": numbers
    }

    headers = {
        'cache-control': "no-cache"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    return response.status_code



@frappe.whitelist(allow_guest=True)
def get_valid_till():
    valid_till = frappe.db.get_single_value("Fast2sms Settings", "valid_till")

    return valid_till