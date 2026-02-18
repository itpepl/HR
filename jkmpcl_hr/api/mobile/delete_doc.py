import frappe

@frappe.whitelist()
def delete_record(doctype, docname):
    try:
        user = frappe.session.user

        if not frappe.has_permission(doctype, "delete", user=user):
            return {
                "success": 0,
                "message": "You do not have permission to delete this record"
            }

        frappe.delete_doc(doctype, docname)

        return {
            "success": 1,
            "message": f"{doctype} {docname} deleted successfully"
        }

    except frappe.DoesNotExistError:
        return {
            "success": 0,
            "message": "Record not found"
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Delete API Error")

        return {
            "success": 0,
            "message": str(e)
        }