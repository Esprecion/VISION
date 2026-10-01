import frappe

REMAINDER = "Remaining balance (not yet invoiced)"


def run(dry_run=1):
    dry_run = int(dry_run)
    print("DRY RUN: nothing will be saved" if dry_run else "APPLYING CHANGES")
    for c in frappe.get_all("Service Contract", fields=["name", "deal", "client"], order_by="name"):
        try:
            fix_contract(c, dry_run)
            if not dry_run:
                frappe.db.commit()
        except Exception as e:
            frappe.db.rollback()
            print("  ERROR on %s: %s" % (c.name, e))


def fix_contract(c, dry_run):
    deal = frappe.get_doc("Deal", c.deal)
    deal_value = float(deal.value or 0) or sum(float(i.amount or 0) for i in deal.items)
    sc = frappe.get_doc("Service Contract", c.name)
    invoices = frappe.get_all(
        "Invoice", filters={"contract": c.name},
        fields=["name", "amount", "status", "milestone", "issue_date"],
        order_by="issue_date asc, name asc",
    )
    print("\n%s | %s | deal value %s" % (c.name, c.client, format(deal_value, ",.0f")))

    used = {i.milestone for i in invoices if i.milestone}
    names = {m.milestone_name for m in sc.payment_milestones}
    inv_of = {i.milestone: i for i in invoices if i.milestone}
    links = []
    changed = False

    for inv in invoices:
        if inv.milestone:
            continue
        unused = [m for m in sc.payment_milestones if m.milestone_name not in used]
        match = next((m for m in unused if abs(float(m.amount or 0) - float(inv.amount or 0)) < 0.01), None)
        if match:
            name = match.milestone_name
            print("  link   %s -> existing milestone '%s'" % (inv.name, name))
        elif unused:
            print("  REVIEW %s (%s): no unused milestone has this amount; left unlinked"
                  % (inv.name, format(float(inv.amount), ",.0f")))
            continue
        else:
            base = frappe.db.get_value("Invoice Item", {"parent": inv.name, "parenttype": "Invoice"}, "item_name") or "Billing"
            name = base if base not in names else "%s (%s)" % (base, inv.name)
            sc.append("payment_milestones", {
                "milestone_name": name, "amount": inv.amount,
                "is_paid": 1 if inv.status == "Paid" else 0,
            })
            names.add(name)
            changed = True
            print("  create milestone '%s' %s for %s" % (name, format(float(inv.amount), ",.0f"), inv.name))
        used.add(name)
        inv_of[name] = inv
        links.append((inv.name, name))

    for m in sc.payment_milestones:
        inv = inv_of.get(m.milestone_name)
        if inv:
            want = 1 if inv.status == "Paid" else 0
            if int(m.is_paid or 0) != want:
                m.is_paid = want
                changed = True
                print("  paid flag '%s' -> %s" % (m.milestone_name, want))

    total = sum(float(m.amount or 0) for m in sc.payment_milestones)
    diff = deal_value - total
    if diff > 0.01 and not any(m.milestone_name == REMAINDER for m in sc.payment_milestones):
        sc.append("payment_milestones", {"milestone_name": REMAINDER, "amount": diff, "is_paid": 0})
        total += diff
        changed = True
        print("  add remaining balance milestone %s" % format(diff, ",.0f"))
    billed = sum(float(i.amount or 0) for i in invoices)
    if billed - deal_value > 0.01:
        print("  OVER-BILLED: invoices %s vs deal %s (over by %s). Amounts NOT changed, needs a decision."
              % (format(billed, ",.0f"), format(deal_value, ",.0f"), format(billed - deal_value, ",.0f")))

    if abs(float(sc.value or 0) - total) > 0.01:
        changed = True
    if not changed and not links:
        print("  nothing to change")
        return
    print("  milestone total -> %s" % format(total, ",.0f"))
    if dry_run:
        return
    sc.save(ignore_permissions=True)
    frappe.db.set_value("Service Contract", c.name, "value", total, update_modified=False)
    for inv_name, ms in links:
        frappe.db.set_value("Invoice", inv_name, "milestone", ms, update_modified=False)
    print("  saved")
