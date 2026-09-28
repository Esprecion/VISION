import frappe

OLD = "VISION"
NEW = "Business Development"


def execute():
    # 1. Create the new Module Def if it doesn't exist
    if not frappe.db.exists("Module Def", NEW):
        frappe.get_doc(
            {
                "doctype": "Module Def",
                "module_name": NEW,
                "app_name": "my_custom_app",
            }
        ).insert(ignore_permissions=True)

    # 2. Move doctypes and reports over to the new module
    frappe.db.sql("UPDATE `tabDocType` SET module = %s WHERE module = %s", (NEW, OLD))
    frappe.db.sql("UPDATE `tabReport` SET module = %s WHERE module = %s", (NEW, OLD))

    # 3. Remove the old Module Def
    frappe.db.sql("DELETE FROM `tabModule Def` WHERE name = %s", (OLD,))
    frappe.clear_cache()
