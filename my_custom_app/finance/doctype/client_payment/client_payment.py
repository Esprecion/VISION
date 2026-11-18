import frappe
from frappe.model.document import Document


class ClientPayment(Document):
	def validate(self):
		self._require_cfo()
		if not (self.invoice and self.amount and self.payment_date and self.payment_method):
			frappe.throw(frappe._("Please complete all required payment details."))
		self._validate_amount()

	def on_update(self):
		previous = self.get_doc_before_save()
		if previous and previous.invoice != self.invoice:
			self._recompute(previous.invoice, exclude=self.name)
		self._recompute(self.invoice)

	def on_trash(self):
		self._require_cfo()
		self._recompute(self.invoice, exclude=self.name)

	def _require_cfo(self):
		roles = frappe.get_roles()
		if "System Manager" in roles or "CFO" in roles:
			return
		frappe.throw(frappe._("Only the CFO can manage client payments."))

	def _validate_amount(self):
		if not frappe.db.exists("Invoice", self.invoice):
			frappe.throw(frappe._("Please complete all required payment details."))
		invoice = frappe.get_doc("Invoice", self.invoice)
		if self._paid_total() > (invoice.amount or 0):
			frappe.throw(frappe._("The payment cannot exceed the outstanding balance."))

	def _paid_total(self):
		rows = frappe.get_all("Client Payment", filters={"invoice": self.invoice}, fields=["name", "amount"])
		exclude = self.name if not self.is_new() else None
		return sum((r.amount or 0) for r in rows if r.name != exclude) + (self.amount or 0)

	def _recompute(self, invoice_name, exclude=None):
		if not invoice_name or not frappe.db.exists("Invoice", invoice_name):
			return
		rows = frappe.get_all("Client Payment", filters={"invoice": invoice_name}, fields=["name", "amount"])
		paid = sum((r.amount or 0) for r in rows if r.name != exclude)
		invoice = frappe.get_doc("Invoice", invoice_name)
		outstanding = max((invoice.amount or 0) - paid, 0)
		status = invoice.status
		if (invoice.amount or 0) > 0 and outstanding <= 0:
			status = "Paid"
		elif status == "Paid" and outstanding > 0:
			status = "Sent"
		frappe.db.set_value(
			"Invoice",
			invoice_name,
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
