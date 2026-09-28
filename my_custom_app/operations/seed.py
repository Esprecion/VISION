import frappe

# Dev-only helper for the Operations prototype. Safe to re-run (skips if Projects exist).


def run():
    if frappe.db.count("Project"):
        print("Already seeded, skipping")
        return

    won = frappe.get_all("Deal", filters={"stage": "Won"}, pluck="name")
    used = set(frappe.get_all("Service Contract", pluck="deal"))
    free = [d for d in won if d not in used]
    print("Won deals without a contract:", len(free))

    contract_specs = [
        ("2026-01-15", "2026-12-31"),
        ("2026-03-01", "2027-02-28"),
        ("2026-05-10", "2027-05-09"),
    ]
    contracts = []
    for deal, (s, e) in zip(free, contract_specs):
        doc = frappe.get_doc({
            "doctype": "Service Contract",
            "deal": deal,
            "client": frappe.db.get_value("Deal", deal, "client"),
            "start_date": s,
            "end_date": e,
            "status": "Finalized",
        })
        doc.insert(ignore_permissions=True, ignore_mandatory=True)
        contracts.append(doc.name)
    contracts += frappe.get_all("Service Contract", filters={"start_date": "2026-10-01"}, pluck="name")
    print("Contracts used:", contracts)

    project_specs = [
        ("Web Portal", "Deployed", "2026-04-30", "2026-04-24"),   # on time
        ("ERP Integration", "Deployed", "2026-06-30", "2026-07-14"),  # late
        ("Mobile App", "Development", "2026-11-30", None),        # active
        ("Data Dashboard", "Kickoff", "2027-03-31", None),        # active
    ]
    projects = []
    for c, (ptype, stage, committed, actual) in zip(contracts, project_specs):
        p = frappe.get_doc({
            "doctype": "Project",
            "contract": c,
            "project_type": ptype,
            "stage": stage,
            "committed_date": committed,
            "actual_delivery_date": actual,
        })
        p.insert(ignore_permissions=True)
        projects.append(p.name)
    print("Projects:", projects)

    clients = frappe.get_all("Client", pluck="name")
    logs = [
        (0, "2026-08-04", "Call", "Kickoff check-in"),
        (1, "2026-08-19", "Email", "Sent revised timeline"),
        (2, "2026-09-02", "Meeting", "Requirements review"),
        (3, "2026-09-10", "Chat", "Quick question on invoice"),
        (4, "2026-09-18", "Call", "Follow-up on proposal"),
        (0, "2026-09-25", "Email", "Sent progress update"),
    ]
    for i, d, ch, n in logs:
        frappe.get_doc({
            "doctype": "Client Engagement Log",
            "client": clients[i % len(clients)],
            "contact_date": d, "channel": ch, "notes": n,
        }).insert(ignore_permissions=True)

    months = ["2026-06-01", "2026-07-01", "2026-08-01", "2026-09-01"]
    subs = [
        ("Frappe Cloud Hosting", "Monthly", 3000, "2026-12-01", [3000, 3000, 3000, 3000], projects[:2]),
        ("Claude API", "Monthly", 3100, "2026-10-15", [1200, 1800, 2400, 3100], projects[1:3]),
        ("Domain and SSL", "Annual", 8500, "2027-03-01", [8500], projects[:1]),
    ]
    for name, cycle, cost, renew, hist, used_in in subs:
        frappe.get_doc({
            "doctype": "Tool Subscription",
            "tool_name": name, "billing_cycle": cycle, "current_cost": cost,
            "renewal_date": renew,
            "projects_using": [{"project": x} for x in used_in],
            "cost_history": [{"month": m, "amount": a} for m, a in zip(months[-len(hist):], hist)],
        }).insert(ignore_permissions=True)

    frappe.db.commit()
    print("Seed done")
