import frappe

from my_custom_app.patches.add_project_profitability import NAME, QUERY

ROLES = ("System Manager", "CBO", "COO", "CFO", "CTO")


def execute():
	if frappe.db.exists("Report", NAME):
		doc = frappe.get_doc("Report", NAME)
	else:
		doc = frappe.get_doc(
			{
				"doctype": "Report",
				"report_name": NAME,
				"ref_doctype": "Invoice",
				"report_type": "Query Report",
				"is_standard": "No",
				"module": frappe.db.get_value("DocType", "Invoice", "module"),
			}
		)

	doc.query = QUERY
	existing = {row.role for row in doc.roles}
	for role in ROLES:
		if role not in existing:
			doc.append("roles", {"role": role})
	doc.save(ignore_permissions=True)
