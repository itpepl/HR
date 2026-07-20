import frappe
from frappe import _
from frappe.utils import getdate, today
# from jkmpcl_hr.py.utils import  get_emp_hr_manager, get_ceo_user, get_emp_review_manager

def before_insert(doc, method):
    # Only applies to the very first save (new doc)
    doc.advance_amount = doc.custom_claim_amount

def validate(doc, method):
    validate_dates_not_in_past(doc)

def validate_dates_not_in_past(doc):
    today_date = getdate(today())

    if doc.get("custom_from_date") and getdate(doc.custom_from_date) < today_date:
        frappe.throw(_("From Date cannot be a date in the past."))

    if doc.get("custom_to_date") and getdate(doc.custom_to_date) < today_date:
        frappe.throw(_("To Date cannot be a date in the past."))

def get_role_users(role):
    return [
        d.user
        for d in frappe.get_all(
            "Has Role",
            filters={
                "role": role,
                "parenttype": "User",
            },
            fields=["parent as user"],
        )
    ]

def share_employee_advance(doc,method):
    old_doc = doc.get_doc_before_save()

    if not old_doc or old_doc.workflow_state == doc.workflow_state:
        return
    
    if doc.workflow_state == "Approved by Reporting Manager":
      users = set()

      print("\n\nEntered condition for Approved by Reporting Manager\n\n")

      # CEO
      if (
        frappe.session.user != "Administrator"
      ):
        users.update(get_role_users("CEO"))

      # PCI
      if frappe.session.user != "Administrator":
          users.update(get_role_users("PCI"))

      # GAO
      if (
        frappe.session.user != "Administrator"
      ):
        users.update(get_role_users("GAO"))

      for user in users:
        frappe.share.add_docshare(
            doc.doctype,
            doc.name,
            user,
            read=1,
            write=1,
            select=1,
            submit=1,
            share=1,
            flags={"ignore_share_permission": True},
        )