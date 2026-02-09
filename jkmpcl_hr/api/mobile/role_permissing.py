import frappe

@frappe.whitelist(allow_guest=True)
def role_permission(email):

    try:
        user = frappe.get_doc("User", email)

        roles = frappe.get_roles(user.name)

        # Filter only mobile roles
        mobile_roles = []
        for role in roles:
            mobile_flag = frappe.db.get_value("Role", role, "mobile_user")
            if mobile_flag:
                mobile_roles.append(role)

        # 🚨 If no mobile roles found
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

        print(permissions_data)
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
