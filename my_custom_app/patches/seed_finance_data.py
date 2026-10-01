import frappe

MARK = "Phase 1 - discovery and data audit"

INVOICES = [
    # (contract, issue, due, status, items[(name, qty, rate)], charges[(desc, amt)])
    ("g5ho345e7i", "2026-01-20", "2026-02-19", "Paid", [(MARK, 1, 48000)], []),
    ("g5ho345e7i", "2026-08-15", "2026-09-14", "Sent", [("Phase 2 - meter data dashboard", 1, 48000)], []),
    ("g5ivt73jvu", "2026-03-05", "2026-04-04", "Paid", [("Downpayment - logistics platform", 1, 90000)], []),
    ("g5ivt73jvu", "2026-07-10", "2026-08-09", "Paid", [("Milestone - dispatch module", 1, 90000)], [("Rush delivery fee", 5000)]),
    ("g5ivt73jvu", "2026-09-01", "2026-09-30", "Overdue", [("Milestone - route optimization", 1, 90000)], []),
    ("g5iv7ntk0a", "2026-05-10", "2026-06-09", "Paid", [("Downpayment - inventory rollout", 1, 65000)], []),
    ("g5iv7ntk0a", "2026-06-20", "2026-07-20", "Overdue", [("Barcode scanner configuration", 1, 40000)], []),
    ("g5iv7ntk0a", "2026-07-25", "2026-08-24", "Overdue", [("Milestone - warehouse deployment", 1, 65000)], []),
    ("g5iv7ntk0a", "2026-09-20", "2026-10-20", "Sent", [("Staff training and handover", 1, 30000)], []),
    ("jjk2r9ilrr", "2026-10-01", "2026-10-31", "Paid", [("Downpayment - executive dashboard", 1, 80000)], []),
]

EXPENSES = [
    # (project, category, date, items[(vendor, description, amount)])
    ("PRJ-00004", "Tools and Subscriptions", "2026-10-01", [("Figma", "Design seats", 2500), ("Claude", "AI assistant subscription", 1800)]),
    ("PRJ-00004", "Tools and Subscriptions", "2026-10-01", [("Microsoft Azure", "Dashboard hosting", 3200)]),
    ("PRJ-00003", "Contractors and Freelancers", "2026-08-15", [("Freelance developer", "Scanner integration", 35000)]),
    ("PRJ-00003", "Tools and Subscriptions", "2026-09-01", [("GitHub", "Copilot seats", 1100), ("Jira", "Project tracking", 1500)]),
    ("PRJ-00003", "Hardware", "2026-06-10", [("Zebra Philippines", "Barcode scanners", 18000)]),
    ("PRJ-00002", "Tools and Subscriptions", "2026-07-01", [("AWS", "Logistics platform hosting", 4800)]),
    ("PRJ-00002", "Tools and Subscriptions", "2026-08-01", [("AWS", "Logistics platform hosting", 4800)]),
    ("PRJ-00002", "Contractors and Freelancers", "2026-07-20", [("Freelance QA tester", "Dispatch module testing", 12000)]),
    ("PRJ-00001", "Tools and Subscriptions", "2026-02-01", [("Figma", "Design seats", 2500), ("Notion", "Documentation", 900)]),
    ("PRJ-00001", "Tools and Subscriptions", "2026-03-01", [("Microsoft Azure", "Data pipeline hosting", 3000)]),
]


def _owner(doctype, name):
    if frappe.db.exists("User", "cfo@test.com"):
        frappe.db.set_value(doctype, name, "owner", "cfo@test.com", update_modified=False)


def execute():
    if frappe.db.exists("Invoice Item", {"item_name": MARK}):
        return

    # remove old dummy rows (those without line items)
    for dt, child in (("Invoice", "Invoice Item"), ("Expense", "Expense Item")):
        for name in frappe.get_all(dt, pluck="name"):
            if not frappe.db.exists(child, {"parent": name}):
                frappe.delete_doc(dt, name, force=True, ignore_permissions=True)

    for contract, issue, due, status, items, charges in INVOICES:
        client = frappe.db.get_value("Service Contract", contract, "client")
        if not client:
            continue
        total = sum(q * r for _, q, r in items) + sum(a for _, a in charges)
        doc = frappe.get_doc({
            "doctype": "Invoice", "client": client, "contract": contract,
            "issue_date": issue, "due_date": due, "status": status, "amount": total,
            "items": [{"item_name": n, "quantity": q, "rate": r} for n, q, r in items],
            "charges": [{"description": d, "amount": a} for d, a in charges],
        }).insert(ignore_permissions=True)
        _owner("Invoice", doc.name)

    for project, category, date, items in EXPENSES:
        if not frappe.db.exists("Project", project):
            continue
        doc = frappe.get_doc({
            "doctype": "Expense", "project": project, "category": category,
            "expense_date": date, "amount": sum(a for _, _, a in items),
            "items": [{"vendor": v, "description": d, "amount": a} for v, d, a in items],
        }).insert(ignore_permissions=True)
        _owner("Expense", doc.name)
