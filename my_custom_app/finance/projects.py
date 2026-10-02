import frappe

CONFIRMED = ("Finalized", "Sent to Finance")


def ensure_project(contract, dry_run=0):
    """Create the Project for a confirmed contract if it has none. Returns its name or None."""
    if frappe.db.exists("Project", {"contract": contract.name}):
        return None
    if dry_run:
        return "(would create)"
    doc = frappe.get_doc({
        "doctype": "Project",
        "contract": contract.name,
        "client": contract.client,
        "stage": "Kickoff",
        "start_date": contract.start_date,
        "committed_date": contract.end_date or contract.start_date or frappe.utils.today(),
    })
    doc.insert(ignore_permissions=True)
    return doc.name


def backfill(dry_run=1):
    dry_run = int(dry_run)
    print("DRY RUN: nothing will be saved" if dry_run else "APPLYING CHANGES")
    for c in frappe.get_all("Service Contract", filters={"status": ["in", list(CONFIRMED)]},
                            fields=["name"], order_by="name"):
        contract = frappe.get_doc("Service Contract", c.name)
        try:
            result = ensure_project(contract, dry_run)
        except Exception as e:
            frappe.db.rollback()
            print("  ERROR on %s: %s" % (c.name, e))
            continue
        print("  %s | %s | %s | %s" % (c.name, contract.client, contract.status, result or "already has a project"))
    if not dry_run:
        frappe.db.commit()
