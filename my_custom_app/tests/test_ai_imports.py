from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from my_custom_app.administration.admin_roles import ensure_roles
from my_custom_app.shared.ai_imports import (
	ProviderUnavailable,
	extract_expense_fields,
	extract_record_fields,
)


class TestAIImports(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_roles()
		self.suffix = frappe.generate_hash(length=8)
		self.created_users = []

	def tearDown(self):
		frappe.set_user("Administrator")
		for name in self.created_users:
			if frappe.db.exists("User", name):
				frappe.delete_doc("User", name, force=True, ignore_permissions=True)

	def _login(self, role):
		account_name = f"ai-{role.lower()}-{self.suffix}"
		doc = frappe.get_doc(
			{
				"doctype": "User",
				"email": f"{account_name}@vision.local",
				"first_name": account_name,
				"username": account_name,
				"send_welcome_email": 0,
				"user_type": "System User",
				"roles": [{"role": role}],
			}
		)
		doc.insert(ignore_permissions=True)
		self.created_users.append(doc.name)
		frappe.set_user(doc.name)

	@patch("my_custom_app.shared.ai_imports._extract")
	def test_extract_client_fields(self, extract):
		self._login("CBO")
		extract.return_value = {
			"client_name": "Acme Corp",
			"contact_email": "ops@acme.test",
			"unknown": "ignored",
		}
		result = extract_record_fields("client", source_text="Acme Corp ops@acme.test")
		self.assertEqual(
			result,
			{"client_name": "Acme Corp", "contact_email": "ops@acme.test"},
		)

	@patch("my_custom_app.shared.ai_imports._extract")
	def test_extract_deal_items(self, extract):
		self._login("CBO")
		extract.return_value = {
			"deal_title": "Phase 1",
			"items": [{"product": "Product-1", "quantity": "2", "price": "500", "extra": "x"}],
		}
		result = extract_record_fields("deal", source_text="Phase 1")
		self.assertEqual(result["deal_title"], "Phase 1")
		self.assertEqual(
			result["items"],
			[{"product": "Product-1", "quantity": "2", "price": "500"}],
		)

	@patch("my_custom_app.shared.ai_imports._extract")
	def test_extract_expense_fields(self, extract):
		self._login("CFO")
		extract.return_value = {
			"vendor": "Figma",
			"date": "2026-11-19",
			"amount": "250",
			"category": "Tools and Subscriptions",
		}
		result = extract_expense_fields(file_name="receipt.png", file_content="aGVsbG8=")
		self.assertEqual(
			result,
			{
				"vendor": "Figma",
				"category": "Tools and Subscriptions",
				"expense_date": "2026-11-19",
				"amount": "250",
			},
		)

	def test_missing_record_source(self):
		self._login("CBO")
		with self.assertRaises(frappe.ValidationError) as error:
			extract_record_fields("client")
		self.assertIn("Please provide text or a supported file.", str(error.exception))

	def test_missing_receipt(self):
		self._login("CFO")
		with self.assertRaises(frappe.ValidationError) as error:
			extract_expense_fields()
		self.assertIn("Please upload a receipt as an image or PDF.", str(error.exception))

	@patch("my_custom_app.shared.ai_imports._extract")
	def test_provider_unavailable(self, extract):
		self._login("CBO")
		extract.side_effect = ProviderUnavailable("AI provider unavailable")
		with self.assertRaises(frappe.ValidationError):
			extract_record_fields("client", source_text="Acme Corp")

	def test_cbo_cannot_import_expenses(self):
		self._login("CBO")
		with self.assertRaises(frappe.PermissionError):
			extract_expense_fields(file_name="receipt.png", file_content="aGVsbG8=")
