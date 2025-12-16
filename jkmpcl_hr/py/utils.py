import traceback
import frappe
from frappe.utils import today, getdate

@frappe.whitelist()
def get_emp_reporting_manager(emp_id, as_on_date=today()):
    rh_dict = frappe.db.get_all("Approver", {"parent":emp_id, "effective_from":["<=", getdate(as_on_date)], "parentfield": "custom_reporting_manager"}, "user", order_by="effective_from desc", limit=1)

    return rh_dict[0]["user"] if rh_dict else None

def send_notification_email(
    recipients,
    doctype,
    docname,
    notification_name,
    send_link=True,
    button_label="View Details",
    button_link="None",
    fallback_subject="Notification",
    fallback_message="You have a new update. Please check your portal.",
    send_attach=False,
    print_format=None,
    letterhead=None,
    send_header_greeting=False,
    enabled=False,
    send_system_notification=False,
    channel="Email",
):
    try:
        # STOP IF NOTIFICATION DISABLED
        if not enabled:
            return
        
        base_url = frappe.utils.get_url()
        attachments = []

        # ? GENERATE DEFAULT BUTTON LINK IF NOT EXPLICITLY PROVIDED
        if send_link and button_link == "None" and doctype and docname:
            button_link = (
                f"{base_url}/app/{doctype.lower().replace(' ', '-')}/{docname}"
            )

        # ? FETCH NOTIFICATION TEMPLATE IF PROVIDED
        notification_doc = None
        message = fallback_message
        subject = fallback_subject
        if notification_name:
            notification_doc = frappe.db.get_value(
                "Notification", notification_name, ["subject", "message"], as_dict=True
            )
            if notification_doc:
                doc = frappe.get_doc(doctype, docname)
                message = frappe.render_template(notification_doc.message, {"doc": doc})
                subject = frappe.render_template(notification_doc.subject, {"doc": doc})

        # ? GENERATE PDF ATTACHMENT IF REQUIRED
        if send_attach and print_format and doctype and docname:
            try:
                # ? GENERATE PDF USING FRAPPE'S BUILT-IN PDF GENERATION
                pdf_content = frappe.get_print(
                    doctype=doctype,
                    name=docname,
                    print_format=print_format,
                    letterhead=letterhead,
                    as_pdf=True,
                )

                # ? CREATE ATTACHMENT DICTIONARY
                attachment_name = f"{doctype}_{docname}_{print_format}.pdf"
                attachments.append({"fname": attachment_name, "fcontent": pdf_content})

            except Exception as pdf_error:
                frappe.log_error(
                    title="PDF Generation Error",
                    message=f"Failed to generate PDF attachment: {str(pdf_error)}\n{traceback.format_exc()}",
                )
                # ? CONTINUE WITHOUT ATTACHMENT RATHER THAN FAILING THE ENTIRE EMAIL

        for email in recipients:
            
            user = frappe.db.get_value(
                    "User", {"email": email}, ["name", "first_name"], as_dict=True
                )
           
            final_message = message
            if send_header_greeting and user:
                
                    
                if user:
                    # ? ADD GREETING BASED ON USER'S FIRST NAME
                    greeting = (
                        f"<p>Dear {user.first_name},</p>"
                        if user.first_name
                        else "<p>Dear User,</p>"
                    )
                    final_message = greeting + final_message

            # ? ADD HASH AND ACTION BUTTON TO MESSAGE IF LINK SHOULD BE INCLUDED
            if send_link:
                
                if button_link:
                    final_message += f"""
                        <hr>
                        <p><b>{button_label}</b></p>
                        <p><a href="{button_link}" target="_blank">{button_label}</a></p>
                    """

            # ? LOG NOTIFICATION IN FRAPPE'S NOTIFICATION LOG
            if send_system_notification or channel == "System Notification":
                if user:
                    system_notification = frappe.get_doc(
                        {
                            "doctype": "Notification Log",
                            "subject": subject,
                            "for_user": user.get("name"),
                            "type": "Alert",
                            "document_type": doctype,
                            "document_name": docname,
                            "email_content": message
                        }
                    )
                    system_notification.insert(ignore_permissions=True)

            # ? SEND EMAIL WITH OPTIONAL ATTACHMENT
            if channel == "Email":
                frappe.sendmail(
                    recipients=[email],
                    subject=subject,
                    message=final_message,
                    attachments=attachments if attachments else None,
                )

    except Exception as e:
        frappe.log_error(
            title="Notification Email Error",
            message=f"Failed sending notification: {str(e)}\n{traceback.format_exc()}",
        )
        frappe.throw(frappe._("An error occurred while sending notification emails."))


# * METHOD TO GET ROLES FROM THE HR SETTINGS
@frappe.whitelist()
def get_roles_from_hr_settings_by_module(role_type_field):
    try:
        if not role_type_field:
            return []

        roles_value = frappe.db.get_single_value("HR Settings", role_type_field)
        if not roles_value:
            return []

        roles_list = [role.strip() for role in roles_value.split(",") if role.strip()]
        return roles_list

    except Exception as error:
        frappe.log_error("Error Fetching Roles from HR Settings", str(error))
        return []



def create_shift_assignment_rec(emp_id, from_date, to_date, shift_type_id):
    
    doc = frappe.get_doc({
                    "doctype": "Shift Assignment",
                    "employee": emp_id,
                    # "employee_name": emp_display
                    "shift_type": shift_type_id,
                    "start_date": from_date,
                    "end_date": to_date,
                })  

    doc.insert(ignore_permissions=True)
    doc.submit()    
    frappe.db.commit()