import frappe
from frappe import _

MODULE_DOCTYPES = {
	"business_dev": "Deal",
	"finance": "Invoice",
	"operations": "Project",
}

CLOSED_DEAL_STAGES = {"Closed", "Closed Lost", "Closed Won", "Lost", "Won"}

DETAIL_FIELDS = {
	"Client": ["client_name", "territory", "contact_person", "contact_email", "contact_phone", "address"],
	"Client Payment": ["invoice", "client", "amount", "payment_date", "payment_method", "reference"],
	"Deal": ["deal_title", "client", "territory", "stage", "value", "expected_close_date"],
	"Expense": ["category", "amount", "expense_date", "project"],
	"Invoice": [
		"client",
		"contract",
		"amount",
		"paid_amount",
		"outstanding_amount",
		"issue_date",
		"due_date",
		"status",
		"milestone",
	],
	"Product": ["product_name", "type", "description"],
	"Project": [
		"contract",
		"client",
		"project_type",
		"stage",
		"start_date",
		"committed_date",
		"actual_delivery_date",
	],
	"Service Contract": [
		"client",
		"deal",
		"value",
		"start_date",
		"end_date",
		"status",
		"payment_terms_days",
		"terms_and_conditions",
	],
}


def _require_module_read(module):
	doctype = MODULE_DOCTYPES[module]
	if not frappe.has_permission(doctype, "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def _require_doctype_read(doctype):
	if not frappe.has_permission(doctype, "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def _date_filters(fieldname, from_date=None, to_date=None):
	filters = {}
	if from_date:
		filters[fieldname] = [">=", str(from_date)[:10]]
	if to_date:
		if from_date:
			filters[fieldname] = ["between", [str(from_date)[:10], str(to_date)[:10]]]
		else:
			filters[fieldname] = ["<=", str(to_date)[:10]]
	return filters


def _client_filters(client=None):
	return {"client": client} if client else {}


def _rows(doctype, fields, filters=None):
	return frappe.get_all(doctype, filters=filters or {}, fields=fields, limit_page_length=500)


def _record(doctype, row, title_field, subtitle_field=None, meta_field=None):
	return {
		"doctype": doctype,
		"name": row.name,
		"title": row.get(title_field) or row.name,
		"subtitle": row.get(subtitle_field) if subtitle_field else "",
		"meta": row.get(meta_field) if meta_field else "",
	}


def _count(values):
	counts = {}
	for value in values:
		key = value or "Unassigned"
		counts[key] = counts.get(key, 0) + 1
	return counts


def _number(value):
	return float(value or 0)


@frappe.whitelist()
def business_development_records_and_metrics(from_date=None, to_date=None, stage=None, client=None):
	_require_module_read("business_dev")

	deal_filters = _client_filters(client)
	deal_filters.update(_date_filters("expected_close_date", from_date, to_date))
	if stage:
		deal_filters["stage"] = stage
	deals = _rows(
		"Deal",
		["name", "deal_title", "client", "stage", "value", "expected_close_date"],
		deal_filters,
	)

	contract_filters = _client_filters(client)
	contract_filters.update(_date_filters("start_date", from_date, to_date))
	contracts = _rows(
		"Service Contract",
		["name", "client", "deal", "value", "start_date", "status"],
		contract_filters,
	)

	clients = _rows(
		"Client",
		["name", "client_name", "territory"],
		{"name": client} if client else {},
	)
	products = _rows("Product", ["name", "product_name", "type"])

	contract_counts = _count(contract.status for contract in contracts)
	return {
		"metrics": {
			"deals_per_stage": _count(deal.stage for deal in deals),
			"open_deal_value": sum(
				_number(deal.value) for deal in deals if (deal.stage or "") not in CLOSED_DEAL_STAGES
			),
			"draft_contracts": contract_counts.get("Draft", 0),
			"finalized_contracts": contract_counts.get("Finalized", 0),
			"contract_counts": contract_counts,
		},
		"records": {
			"clients": [_record("Client", row, "client_name", "territory") for row in clients],
			"products": [_record("Product", row, "product_name", "type") for row in products],
			"deals": [_record("Deal", row, "deal_title", "client", "stage") for row in deals],
			"contracts": [_record("Service Contract", row, "deal", "client", "status") for row in contracts],
		},
		"filters": {
			"from_date": str(from_date)[:10] if from_date else "",
			"to_date": str(to_date)[:10] if to_date else "",
			"stage": stage or "",
			"client": client or "",
		},
	}


@frappe.whitelist()
def operations_records_and_metrics(status=None, client=None):
	_require_module_read("operations")

	filters = _client_filters(client)
	if status:
		filters["stage"] = status
	projects = _rows(
		"Project",
		[
			"name",
			"contract",
			"client",
			"project_type",
			"stage",
			"start_date",
			"committed_date",
		],
		filters,
	)

	return {
		"metrics": {
			"projects_per_status": _count(project.stage for project in projects),
			"projects_linked_to_contract": sum(1 for project in projects if project.contract),
		},
		"records": {"projects": [_record("Project", row, "contract", "client", "stage") for row in projects]},
		"filters": {"status": status or "", "client": client or ""},
	}


@frappe.whitelist()
def finance_records_and_metrics(from_date=None, to_date=None, client=None):
	_require_module_read("finance")

	invoice_filters = _client_filters(client)
	invoice_filters.update(_date_filters("issue_date", from_date, to_date))
	invoices = _rows(
		"Invoice",
		[
			"name",
			"client",
			"amount",
			"paid_amount",
			"outstanding_amount",
			"issue_date",
			"due_date",
			"status",
		],
		invoice_filters,
	)

	payment_filters = _client_filters(client)
	payment_filters.update(_date_filters("payment_date", from_date, to_date))
	payments = []
	if frappe.has_permission("Client Payment", "read"):
		payments = _rows(
			"Client Payment",
			["name", "invoice", "client", "amount", "payment_date", "payment_method"],
			payment_filters,
		)

	expense_filters = _date_filters("expense_date", from_date, to_date)
	if client:
		project_names = frappe.get_all("Project", filters={"client": client}, pluck="name")
		expense_filters["project"] = ["in", project_names or ["__none__"]]
	expenses = _rows(
		"Expense",
		["name", "category", "amount", "expense_date", "project"],
		expense_filters,
	)

	payment_total = sum(_number(payment.amount) for payment in payments)
	invoice_paid_total = sum(_number(invoice.paid_amount) for invoice in invoices)
	return {
		"metrics": {
			"total_invoiced": sum(_number(invoice.amount) for invoice in invoices),
			"total_received": payment_total if payments else invoice_paid_total,
			"outstanding_balance": sum(_number(invoice.outstanding_amount) for invoice in invoices),
			"total_expenses": sum(_number(expense.amount) for expense in expenses),
		},
		"records": {
			"invoices": [_record("Invoice", row, "client", "issue_date", "status") for row in invoices],
			"payments": [
				_record("Client Payment", row, "invoice", "client", "payment_date") for row in payments
			],
			"expenses": [_record("Expense", row, "category", "project", "expense_date") for row in expenses],
		},
		"filters": {
			"from_date": str(from_date)[:10] if from_date else "",
			"to_date": str(to_date)[:10] if to_date else "",
			"client": client or "",
		},
	}


@frappe.whitelist()
def get_dashboard_record(doctype=None, name=None):
	if doctype not in DETAIL_FIELDS:
		frappe.throw(_("Unsupported record type."))
	_require_doctype_read(doctype)
	if not name or not frappe.db.exists(doctype, name):
		frappe.throw(_("Record not found."))

	doc = frappe.get_doc(doctype, name)
	fields = []
	for fieldname in DETAIL_FIELDS[doctype]:
		value = doc.get(fieldname)
		if value in (None, ""):
			continue
		meta = doc.meta.get_field(fieldname)
		fields.append(
			{
				"label": meta.label if meta else fieldname,
				"value": value,
				"fieldtype": meta.fieldtype if meta else "Data",
			}
		)
	return {"doctype": doctype, "name": name, "fields": fields}


@frappe.whitelist()
def log_dashboard_error(source=None, message=None):
	frappe.log_error(
		message=str(message or "Unknown dashboard error")[:2000],
		title=f"Dashboard error: {source or 'unknown'}",
	)
	return {"ok": True}
