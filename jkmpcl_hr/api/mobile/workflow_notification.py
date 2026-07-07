# import frappe
# from frappe.push_notification import PushNotification



# def workflow_notification(doc, method):

#     if not getattr(doc, "employee", None):
#         return

#     employee = frappe.get_doc("Employee", doc.employee)

#     if not employee.user_id:
#         return

#     push = PushNotification("hrms")

#     if not push.is_enabled():
#         return

#     previous = doc.get_doc_before_save()

#     if previous:
#         old_state = getattr(previous, "workflow_state", None)
#         new_state = getattr(doc, "workflow_state", None)

#         if old_state == new_state:
#             return

#     status = getattr(doc, "workflow_state", None) or getattr(doc, "status", "Updated")

#     push.send_notification_to_user(
#         employee.user_id,
#         f"{doc.doctype} {status}",
#         f"Your {doc.doctype} ({doc.name}) has been {status.lower()}.",
#         link=f"/app/{frappe.scrub(doc.doctype)}/{doc.name}",
#     )


import frappe
from jkmpcl_hr.api.mobile.firebase import send_fcm_notification


def workflow_notification(doc, method):

    if not getattr(doc, "employee", None):
        return

    employee = frappe.get_doc("Employee", doc.employee)

    if not employee.custom_fcm_token:
        frappe.log_error(
            f"FCM token not found for Employee {employee.name}",
            "Workflow Notification"
        )
        return

    previous = doc.get_doc_before_save()

    if previous:
        old_state = getattr(previous, "workflow_state", None)
        new_state = getattr(doc, "workflow_state", None)

        if old_state == new_state:
            return

    status = getattr(doc, "workflow_state", None) or getattr(doc, "status", "Updated")

    send_fcm_notification(
        token=employee.custom_fcm_token,
        title=f"{doc.doctype} {status}",
        body=f"Your {doc.doctype} ({doc.name}) has been {status.lower()}.",
        data={
            "doctype": doc.doctype,
            "docname": doc.name,
            "status": status,
        },
    )