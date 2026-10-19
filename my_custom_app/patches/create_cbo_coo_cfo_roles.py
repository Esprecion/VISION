import frappe

ROLES = ("CBO", "COO", "CFO")


def create_roles():
	"""Create the CBO, COO and CFO roles if they do not already exist."""
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc(
				{
					"doctype": "Role",
					"role_name": role,
					"desk_access": 1,
				}
			).insert(ignore_permissions=True)


def execute():
	create_roles()