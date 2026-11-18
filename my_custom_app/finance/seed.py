import frappe

# Dev helper for the Finance prototype. Safe to re-run (skips if Invoices exist).


def run():
	if frappe.db.count("Invoice"):
		print("Already seeded, skipping")
		return

	contracts = frappe.get_all("Service Contract", fields=["name", "client", "start_date"])
	print("Contracts:", contracts)

	invoice_specs = [
		# (contract idx, amount, issue_date, due_date, status)
		(0, 65000, "2026-05-01", "2026-05-31", "Paid"),
		(0, 65000, "2026-08-01", "2026-08-31", "Paid"),
		(1, 90000, "2026-07-01", "2026-07-31", "Paid"),
		(1, 90000, "2026-09-01", "2026-09-30", "Overdue"),
		(2, 48000, "2026-08-15", "2026-09-14", "Sent"),
	]
	payment_specs = [
		# (invoice idx, amount, payment date, method, reference)
		(0, 65000, "2026-05-05", "Bank Transfer", "PAY-SEED-001"),
		(1, 65000, "2026-08-05", "Bank Transfer", "PAY-SEED-002"),
		(2, 90000, "2026-07-05", "Bank Transfer", "PAY-SEED-003"),
		(4, 24000, "2026-08-20", "Online", "PAY-SEED-004"),
	]
	invoice_docs = []
	for idx, amount, isd, dd, status in invoice_specs:
		if idx >= len(contracts):
			continue
		c = contracts[idx]
		doc = frappe.get_doc(
			{
				"doctype": "Invoice",
				"client": c["client"],
				"contract": c["name"],
				"amount": amount,
				"issue_date": isd,
				"due_date": dd,
				"status": status,
			}
		).insert(ignore_permissions=True)
		invoice_docs.append(doc)

	if not frappe.db.count("Client Payment"):
		for idx, amount, date, method, reference in payment_specs:
			if idx >= len(invoice_docs):
				continue
			frappe.get_doc(
				{
					"doctype": "Client Payment",
					"invoice": invoice_docs[idx].name,
					"amount": amount,
					"payment_date": date,
					"payment_method": method,
					"reference": reference,
				}
			).insert(ignore_permissions=True)

	projects = frappe.get_all("Project", pluck="name")
	print("Projects:", projects)

	expense_specs = [
		# (category, amount, date, project idx or None)
		("Salaries", 40000, "2026-07-15", None),
		("Salaries", 40000, "2026-08-15", None),
		("Tools and Subscriptions", 4200, "2026-06-30", 0),
		("Tools and Subscriptions", 6100, "2026-09-30", 1),
		("Infrastructure", 3000, "2026-07-01", 0),
		("Infrastructure", 3000, "2026-08-01", 1),
		("Other", 5000, "2026-08-20", None),
	]
	for cat, amount, d, pidx in expense_specs:
		frappe.get_doc(
			{
				"doctype": "Expense",
				"category": cat,
				"amount": amount,
				"expense_date": d,
				"project": projects[pidx] if pidx is not None and pidx < len(projects) else None,
			}
		).insert(ignore_permissions=True)

	frappe.db.commit()
	print("Seed done")
