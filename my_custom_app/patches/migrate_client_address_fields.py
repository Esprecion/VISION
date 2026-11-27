import frappe


def execute():
	if not frappe.db.has_column("Client", "street_barangay"):
		return

	clients = frappe.get_all(
		"Client",
		filters={"address": ("is", "set")},
		fields=["name", "address"],
	)
	for client in clients:
		street_barangay = frappe.db.get_value("Client", client.name, "street_barangay")
		if street_barangay or not client.address:
			continue
		frappe.db.set_value(
			"Client",
			client.name,
			"street_barangay",
			client.address,
			update_modified=False,
		)
