import frappe


@frappe.whitelist()
def get_my_roles():
    return {
        "user": frappe.session.user,
        "roles": frappe.get_roles(frappe.session.user),
    }


@frappe.whitelist()
def create_deal_with_details(deal, client, items):
    """Create client + products + deal in one go. All-or-nothing."""
    deal = frappe.parse_json(deal)
    client = frappe.parse_json(client)
    items = frappe.parse_json(items)

    frappe.has_permission("Deal", "create", throw=True)

    title = (deal.get("deal_title") or "").strip()
    if not title:
        frappe.throw("Deal title is required")
    if not deal.get("stage"):
        frappe.throw("Stage is required")
    if not items:
        frappe.throw("Add at least one product line")

    client_name = _get_or_create_client(client)

    seen_products = {}
    rows, total = [], 0
    for it in items:
        product_name = _get_or_create_product(it, seen_products)
        qty = int(it.get("quantity") or 0)
        price = float(it.get("price") or 0)
        if qty <= 0 or price < 0:
            frappe.throw("Each line needs a quantity above 0 and a price of 0 or more")
        amount = qty * price
        total += amount
        rows.append({"product": product_name, "quantity": qty, "price": price, "amount": amount})

    doc = frappe.get_doc({
        "doctype": "Deal",
        "deal_title": title,
        "client": client_name,
        "stage": deal.get("stage"),
        "expected_close_date": deal.get("expected_close_date") or None,
        "value": total,
        "items": rows,
    })
    doc.insert()
    return doc.as_dict()


def _get_or_create_client(client):
    existing = client.get("existing")
    if existing:
        if not frappe.db.exists("Client", existing):
            frappe.throw(f"Client {existing} does not exist")
        return existing

    new = client.get("new") or {}
    name = (new.get("client_name") or "").strip()
    if not name:
        frappe.throw("Client name is required")

    found = frappe.db.exists("Client", name)
    if found:
        return found

    doc = frappe.get_doc({
        "doctype": "Client",
        "client_name": name,
        "contact_person": (new.get("contact_person") or "").strip(),
        "contact_email": (new.get("contact_email") or "").strip(),
        "contact_phone": (new.get("contact_phone") or "").strip(),
        "territory": (new.get("territory") or "").strip(),
        "address": (new.get("address") or "").strip(),
    })
    doc.insert()
    return doc.name


def _get_or_create_product(item, seen):
    existing = item.get("product")
    if existing:
        if not frappe.db.exists("Product", existing):
            frappe.throw(f"Product {existing} does not exist")
        return existing

    new = item.get("new_product") or {}
    name = (new.get("product_name") or "").strip()
    if not name:
        frappe.throw("Each line needs a product")
    key = name.lower()
    if key in seen:
        return seen[key]

    found = frappe.db.exists("Product", name)
    if found:
        seen[key] = found
        return found

    ptype = new.get("type")
    if ptype not in ("Software", "Hardware", "Consulting", "Support"):
        frappe.throw(f"Choose a type for new product {name}")

    doc = frappe.get_doc({
        "doctype": "Product",
        "product_name": name,
        "type": ptype,
        "description": (new.get("description") or "").strip(),
    })
    doc.insert()
    seen[key] = doc.name
    return doc.name


@frappe.whitelist()
def can_create(doctype):
    return bool(frappe.has_permission(doctype, "create"))
