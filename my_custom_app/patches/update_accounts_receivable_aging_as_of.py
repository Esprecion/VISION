import frappe

from my_custom_app.finance.seed_reports import AR_QUERY, REPORT_FILTERS

NAME = "Accounts Receivable Aging"
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
				"module": "Finance",
			}
		)

	doc.query = AR_QUERY.strip()
	doc.set("filters", [])
	for filter_row in REPORT_FILTERS.get(NAME, []):
		doc.append("filters", dict(filter_row))
	existing = {row.role for row in doc.roles}
	for role in ROLES:
		if role not in existing:
			doc.append("roles", {"role": role})
	doc.save(ignore_permissions=True)
