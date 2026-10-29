import frappe

MODULES = ("Business Development", "Finance", "Operations")
ROLES = ("CTO", "System Admin")


def execute():
	for report in frappe.get_all("Report", filters={"module": ("in", MODULES)}, pluck="name"):
		doc = frappe.get_doc("Report", report)
		existing = {row.role for row in doc.roles}
		changed = False
		for role in ROLES:
			if role not in existing:
				doc.append("roles", {"role": role})
				changed = True
		if changed:
			doc.save(ignore_permissions=True)
