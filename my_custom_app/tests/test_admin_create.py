from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils.password import check_password

from my_custom_app.admin import create_user
from my_custom_app.admin_roles import ensure_roles


class TestAdminCreateUser(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_roles()
		self.suffix = frappe.generate_hash(length=8)
		self.password = f"Aa1!{frappe.generate_hash(length=24)}"
		self.created_users = []

	def tearDown(self):
		frappe.set_user("Administrator")
		for name in self.created_users:
			if frappe.db.exists("User", name):
				frappe.delete_doc("User", name, force=True, ignore_permissions=True)

	def _account_name(self, label):
		return f"{label}-{self.suffix}"

	def _create_user(self, label="coo", role="COO", password=None):
		result = create_user(self._account_name(label), password or self.password, role)
		if result.get("ok"):
			name = frappe.db.get_value("User", {"username": result["user"]["account_name"]}, "name")
			self.created_users.append(name)
		return result

	def _find_user(self, account_name):
		name = frappe.db.get_value("User", {"username": account_name}, "name")
		return frappe.get_doc("User", name) if name else None

	def test_create_user_succeeds_with_one_managed_role(self):
		account_name = self._account_name("coo")
		result = create_user(account_name, self.password, "COO")
		user = self._find_user(account_name)
		self.assertIsNotNone(user)
		self.created_users.append(user.name)

		self.assertTrue(result["ok"])
		self.assertEqual(result["message"], "User Created")
		self.assertEqual(
			result["user"],
			{
				"account_name": account_name,
				"role": "COO",
				"roles": ["COO"],
				"has_extra_roles": False,
				"enabled": True,
			},
		)
		self.assertEqual(user.username, account_name)
		self.assertEqual(user.email, f"{account_name}@vision.local")
		self.assertEqual(user.first_name, account_name)
		self.assertEqual(user.send_welcome_email, 0)
		self.assertTrue(user.enabled)
		self.assertEqual([row.role for row in user.roles], ["COO"])
		self.assertEqual(check_password(user.name, self.password), user.name)
		self.assertNotIn(self.password, str(result))

	def test_create_user_requires_all_fields(self):
		result = create_user("", "", "")

		self.assertFalse(result["ok"])
		self.assertEqual(result["field"], "account_name")
		self.assertEqual(result["fields"], ["account_name", "password", "role"])
		self.assertEqual(result["message"], "Please complete all required user details.")

	def test_create_user_requires_password(self):
		account_name = self._account_name("missing-password")
		result = create_user(account_name, "", "COO")

		self.assertFalse(result["ok"])
		self.assertEqual(result["field"], "password")
		self.assertEqual(result["fields"], ["password"])
		self.assertEqual(result["message"], "Please complete all required user details.")
		self.assertIsNone(self._find_user(account_name))

	def test_create_user_rejects_duplicate_account_name(self):
		account_name = self._account_name("duplicate")
		self._create_user("duplicate")

		result = create_user(account_name, self.password, "CFO")

		self.assertFalse(result["ok"])
		self.assertEqual(result["field"], "account_name")
		self.assertEqual(result["fields"], ["account_name"])
		self.assertEqual(result["message"], "This account name is already taken.")
		self.assertEqual(frappe.db.count("User", {"username": account_name}), 1)

	def test_create_user_rejects_protected_account_names(self):
		for account_name in ("Administrator", "Guest", "administrator"):
			with self.subTest(account_name=account_name):
				result = create_user(account_name, self.password, "COO")

				self.assertFalse(result["ok"])
				self.assertEqual(result["field"], "account_name")
				self.assertEqual(result["message"], "This account name is already taken.")

	def test_create_user_rejects_roles_outside_allowed_list(self):
		for role in ("System Manager", "Administrator", "HR Manager"):
			with self.subTest(role=role):
				account_name = self._account_name(f"invalid-{role.lower().replace(' ', '-')}")
				result = create_user(account_name, self.password, role)

				self.assertFalse(result["ok"])
				self.assertEqual(result["field"], "role")
				self.assertEqual(result["fields"], ["role"])
				self.assertEqual(result["message"], "Please choose a valid role.")
				self.assertIsNone(self._find_user(account_name))

	def test_create_user_returns_field_error_for_weak_password(self):
		account_name = self._account_name("weak-password")
		feedback = {
			"feedback": {
				"password_policy_validation_passed": False,
				"warning": "This password is too short.",
				"suggestions": ["Add another word or two."],
			}
		}

		with patch("frappe.core.doctype.user.user.test_password_strength", return_value=feedback):
			result = create_user(account_name, "123", "COO")

		self.assertFalse(result["ok"])
		self.assertEqual(result["field"], "password")
		self.assertEqual(result["fields"], ["password"])
		self.assertIn("Password requirements not met.", result["message"])
		self.assertIn("This password is too short.", result["message"])
		self.assertNotIn("123", result["message"])
		self.assertIsNone(self._find_user(account_name))

	def test_non_system_admin_cannot_create_user(self):
		creator = self._create_user("coo-creator")
		account_name = self._account_name("blocked")
		frappe.set_user(frappe.db.get_value("User", {"username": creator["user"]["account_name"]}, "name"))
		try:
			with self.assertRaises(frappe.PermissionError):
				create_user(account_name, self.password, "CFO")
		finally:
			frappe.set_user("Administrator")

		self.assertIsNone(self._find_user(account_name))
