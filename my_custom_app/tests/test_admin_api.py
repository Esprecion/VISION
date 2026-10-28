from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from my_custom_app.admin import get_user, list_users
from my_custom_app.admin_roles import ensure_roles


class TestAdminReadApis(FrappeTestCase):
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

	def _create_user(self, label, roles):
		account_name = f"{label}-{self.suffix}"
		doc = frappe.get_doc(
			{
				"doctype": "User",
				"email": f"{account_name}@vision.local",
				"first_name": account_name,
				"username": account_name,
				"send_welcome_email": 0,
				"enabled": 1,
				"user_type": "System User",
				"roles": [{"role": role} for role in roles],
				"new_password": frappe.generate_hash(length=32),
			}
		)
		doc.insert(ignore_permissions=True)
		self.created_users.append(doc.name)
		return doc

	def test_list_users_uses_username_and_managed_role(self):
		user = self._create_user("coo", ["COO"])

		rows = list_users()
		row = next(item for item in rows if item["account_name"] == user.username)

		self.assertEqual(row["role"], "COO")
		self.assertFalse(row["has_extra_roles"])

	def test_list_users_shows_first_managed_role_and_flags_extra_roles(self):
		user = self._create_user("multi", ["COO", "System Admin"])

		rows = list_users()
		row = next(item for item in rows if item["account_name"] == user.username)

		self.assertEqual(row["role"], "COO")
		self.assertTrue(row["has_extra_roles"])

	def test_list_users_flags_non_managed_extra_role(self):
		user = self._create_user("mixed", ["CFO", "System Manager"])

		rows = list_users()
		row = next(item for item in rows if item["account_name"] == user.username)

		self.assertEqual(row["role"], "CFO")
		self.assertTrue(row["has_extra_roles"])

	def test_list_users_hides_protected_users(self):
		names = [row["account_name"] for row in list_users()]
		self.assertNotIn("Administrator", names)
		self.assertNotIn("Guest", names)

	def test_list_users_excludes_users_without_a_managed_role(self):
		user = self._create_user("unmanaged", ["System Manager"])

		names = [row["account_name"] for row in list_users()]
		self.assertNotIn(user.username, names)

	def test_get_user_returns_account_name_and_role(self):
		user = self._create_user("cfo", ["CFO"])

		detail = get_user(user.username)

		self.assertEqual(detail["account_name"], user.username)
		self.assertEqual(detail["role"], "CFO")
		self.assertFalse(detail["has_extra_roles"])

	def test_get_user_returns_first_managed_role(self):
		user = self._create_user("cfo-multi", ["CFO", "System Admin"])

		detail = get_user(user.username)

		self.assertEqual(detail["role"], "CFO")
		self.assertTrue(detail["has_extra_roles"])

	def test_get_user_rejects_protected_user(self):
		with self.assertRaises(frappe.DoesNotExistError):
			get_user("Administrator")

	def test_get_user_rejects_user_without_a_managed_role(self):
		user = self._create_user("unmanaged-detail", ["System Manager"])

		with self.assertRaises(frappe.DoesNotExistError):
			get_user(user.username)

	def test_non_system_admin_cannot_read_users(self):
		user = self._create_user("coo-reader", ["COO"])
		frappe.set_user(user.name)
		try:
			with self.assertRaises(frappe.PermissionError):
				list_users()
			with self.assertRaises(frappe.PermissionError):
				get_user(user.username)
		finally:
			frappe.set_user("Administrator")

	def test_list_users_logs_and_reports_read_failure(self):
		with patch("my_custom_app.admin._load_users", side_effect=Exception("db down")):
			with self.assertRaises(frappe.ValidationError) as error:
				list_users()

		self.assertIn("Unable to load users. Please try again.", str(error.exception))

	def test_get_user_logs_and_reports_read_failure(self):
		with patch("my_custom_app.admin._load_user", side_effect=Exception("db down")):
			with self.assertRaises(frappe.ValidationError) as error:
				get_user("someone")

		self.assertIn("Unable to load user. Please try again.", str(error.exception))
