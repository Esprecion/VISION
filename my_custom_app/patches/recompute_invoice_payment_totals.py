import frappe


def execute():
	for name in frappe.get_all("Invoice", pluck="name"):
		paid = frappe.db.sql(
			"SELECT COALESCE(SUM(amount), 0) FROM `tabClient Payment` WHERE invoice = %s", name
		)[0][0]
		invoice = frappe.get_doc("Invoice", name)
		outstanding = max((invoice.amount or 0) - paid, 0)
		status = invoice.status
		if (invoice.amount or 0) > 0 and outstanding <= 0:
			status = "Paid"
		elif status == "Paid" and outstanding > 0:
			status = "Sent"
		frappe.db.set_value(
			"Invoice",
			name,
			{"paid_amount": paid, "outstanding_amount": outstanding, "status": status},
			update_modified=False,
		)
		if invoice.contract and invoice.milestone:
			frappe.db.set_value(
				"Contract Payment Milestone",
				{"parent": invoice.contract, "milestone_name": invoice.milestone},
				"is_paid",
				1 if status == "Paid" else 0,
				update_modified=False,
			)
