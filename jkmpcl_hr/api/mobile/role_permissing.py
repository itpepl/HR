import frappe

@frappe.whitelist(allow_guest=True)
def role_permission(email):

    try:
        user = frappe.get_doc("User", email)

        roles = frappe.get_roles(user.name)

        mobile_roles = []
        for role in roles:
            mobile_flag = frappe.db.get_value("Role", role, "mobile_user")
            if mobile_flag:
                mobile_roles.append(role)

        if not mobile_roles:
            frappe.response["message"] = {
                "success_key": 1,
                "roles": [],
                "doc_list": [],
                "permissions": [],
                "info": "No mobile enabled roles found for this user"
            }
            return

        permissions_data = frappe.db.sql("""
            SELECT
                parent,
                role,
                `read`,
                `write`,
                `create`,
                `delete`,
                `submit`
            FROM `tabDocPerm`
            WHERE role IN %(roles)s

            UNION ALL

            SELECT
                parent,
                role,
                `read`,
                `write`,
                `create`,
                `delete`,
                `submit`
            FROM `tabCustom DocPerm`
            WHERE role IN %(roles)s
        """, {"roles": tuple(mobile_roles)}, as_dict=True)

        doc_list = []
        permission_keys = []

        for perm in permissions_data:

            doc_name = perm.parent
            formatted = doc_name.replace(" ", "_").lower()

            doc_list.append(doc_name)

            if perm.read:
                permission_keys.append(f"{formatted}_read")
            if perm.write:
                permission_keys.append(f"{formatted}_write")
            if perm.create:
                permission_keys.append(f"{formatted}_create")
            if perm.delete:
                permission_keys.append(f"{formatted}_delete")
            if perm.submit:
                permission_keys.append(f"{formatted}_submit")

        frappe.response["message"] = {
            "success_key": 1,
            "roles": mobile_roles,
            "doc_list": list(set(doc_list)),
            "permissions": list(set(permission_keys)),
        }

    except Exception as e:

        frappe.log_error(frappe.get_traceback(), "Mobile Role Permission API")

        frappe.response["message"] = {
            "success_key": 0,
            "error": str(e),
        }


@frappe.whitelist(allow_guest=True)
def employee_list(search=None, limit_page_length=20, limit_start=0):
    try:
        filters = []
        or_filters = None  # ✅ always define first

        # Search filter
        if search:
            or_filters = [
                ["employee_name", "like", f"%{search}%"],
                ["name", "like", f"%{search}%"]
            ]

        employees = frappe.get_list(
            "Employee",
            fields=["name", "employee_name","department", "designation","branch","reports_to"],
            filters=filters,
            or_filters=or_filters,
            limit_page_length=int(limit_page_length),
            limit_start=int(limit_start),
            order_by="employee_name asc"
        )

        # Permission-safe count
        total_count = len(
            frappe.get_list(
                "Employee",
                filters=filters,
                or_filters=or_filters,
                fields=["name"]
            )
        )

        return {
            "success": True,
            "total_count": total_count,
            "limit": int(limit_page_length),
            "offset": int(limit_start),
            "data": employees
        }

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Employee List API Error"
        )
        return {
            "success": False,
            "message": "Unable to fetch employee list"
        }

    
@frappe.whitelist(allow_guest=True)
def employee_department(search=None, limit_page_length=20, limit_start=0):
    try:
        filters = []

        if search:
            filters = [
                ["Employee", "department", "like", f"%{search}%"]
            ]

        employees = frappe.get_list(
            "Employee",
            fields=[ "department"],
            filters=filters,
            limit_page_length=int(limit_page_length),
            limit_start=int(limit_start),
            order_by="department asc"
        )

        total_count = frappe.get_list("Employee")

        return {
            "success": True,
            "total_count": len(total_count),
            "limit": limit_page_length,
            "offset": limit_start,
            "data": employees
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Employee Department API Error")
        return {
            "success": False,
            "message": str(e)
        }
@frappe.whitelist(allow_guest=True)
def employee_department(search=None, limit_page_length=20, limit_start=0):
    try:
        filters = []
        or_filters = None

        if search:
            or_filters = [
                ["name", "like", f"%{search}%"]
            ]

        departments = frappe.get_list(
            "Department",
            fields=["name"],
            filters=filters,
            or_filters=or_filters,
            limit_page_length=int(limit_page_length),
            limit_start=int(limit_start),
            order_by="name asc"
        )

        total_count = len(
            frappe.get_list(
                "Department",
                filters=filters,
                or_filters=or_filters,
                fields=["name"]
            )
        )

        return {
            "success": True,
            "total_count": total_count,
            "limit": int(limit_page_length),
            "offset": int(limit_start),
            "data": departments
        }

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Employee Department API Error"
        )
        return {
            "success": False,
            "message": "Unable to fetch department list"
        }
