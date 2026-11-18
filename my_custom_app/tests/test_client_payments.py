import frappe
from frappe.exceptions import ValidationError
from frappe.tests.utils import FrappeTestCase

from my_custom_app.administration.admin_roles import ensure_roles


class TestClientPayments(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_roles()
		self.suffix = frappe.generate_hash(length=6)
		self.client = frappe.get_doc(
			{
				"doctype": "Client",
				"client_name": f"Payment Test Client {self.suffix}",
			}
		).insert(ignore_permissions=True)
		self.invoice = frappe.get_doc(
			{
				"doctype": "Invoice",
				"client": self.client.name,
				"amount": 75000,
				"issue_date": "2026-01-20",
				"due_date": "2026-02-19",
				"status": "Sent",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		for doctype, name in (
			("Client Payment", None),
			("Invoice", self.invoice.name),
			("Client", self.client.name),
		):
			if doctype == "Client Payment":
				for row in frappe.get_all("Client Payment", filters={"invoice": self.invoice.name}):
					frappe.delete_doc(doctype, row.name, force=True, ignore_permissions=True)
			elif frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)

	def _payment(self, amount, method="Bank Transfer", reference=None):
		return frappe.get_doc(
			{
				"doctype": "Client Payment",
				"invoice": self.invoice.name,
				"amount": amount,
				"payment_date": "2026-01-25",
				"payment_method": method,
				"reference": reference,
			}
		)

	def _invoice_values(self):
		return frappe.db.get_value(
			"Invoice", self.invoice.name, ["paid_amount", "outstanding_amount", "status"], as_dict=True
		)

	def test_insert_updates_invoice_totals(self):
		self._payment(25000, reference="TC-22-07").insert(ignore_permissions=True)
		values = self._invoice_values()
		self.assertEqual(values.paid_amount, 25000)
		self.assertEqual(values.outstanding_amount, 50000)
		self.assertEqual(values.status, "Sent")

	def test_edit_updates_invoice_totals(self):
		payment = self._payment(25000, reference="TC-22-08")
		payment.insert(ignore_permissions=True)
		payment.amount = 30000
		payment.save(ignore_permissions=True)
		values = self._invoice_values()
		self.assertEqual(values.paid_amount, 30000)
		self.assertEqual(values.outstanding_amount, 45000)

	def test_delete_restores_invoice_totals(self):
		payment = self._payment(25000, reference="TC-22-09")
		payment.insert(ignore_permissions=True)
		frappe.delete_doc("Client Payment", payment.name, force=True, ignore_permissions=True)
		values = self._invoice_values()
		self.assertEqual(values.paid_amount, 0)
		self.assertEqual(values.outstanding_amount, 75000)

	def test_payment_cannot_exceed_outstanding(self):
		with self.assertRaises(ValidationError) as error:
			self._payment(50001).insert(ignore_permissions=True)
		self.assertIn("outstanding balance", str(error.exception))

	def test_full_payment_marks_invoice_paid_and_rollback(self):
		payment = self._payment(50000, reference="TC-22-11")
		payment.insert(ignore_permissions=True)
		final = self._payment(25000, reference="TC-22-11B")
		final.insert(ignore_permissions=True)
		self.assertEqual(self._invoice_values().status, "Paid")
		frappe.delete_doc("Client Payment", final.name, force=True, ignore_permissions=True)
		values = self._invoice_values()
		self.assertEqual(values.status, "Sent")
		self.assertEqual(values.outstanding_amount, 25000)

	def test_invoice_delete_blocked_with_payments(self):
		payment = self._payment(25000)
		payment.insert(ignore_permissions=True)
		with self.assertRaises(ValidationError) as error:
			frappe.delete_doc("Invoice", self.invoice.name, force=True, ignore_permissions=True)
		self.assertIn("linked client payments", str(error.exception))

	def test_non_cfo_cannot_manage_payments(self):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": f"cbo-pay-{self.suffix}@vision.local",
				"first_name": f"cbo-pay-{self.suffix}",
				"username": f"cbo-pay-{self.suffix}",
				"send_welcome_email": 0,
				"user_type": "System User",
				"roles": [{"role": "CBO"}],
			}
		).insert(ignore_permissions=True)
		try:
			frappe.set_user(user.name)
			with self.assertRaises(ValidationError):
				self._payment(1000).insert(ignore_permissions=True)
		finally:
			frappe.set_user("Administrator")
			frappe.delete_doc("User", user.name, force=True, ignore_permissions=True)
