from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils.password import check_password

from my_custom_app.admin import deactivate_user, edit_user
from my_custom_app.admin_roles import ensure_roles


class TestAdminEditAndDeactivate(FrappeTestCase):
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

	def _create_user(self, label, roles, password=None):
		account_name = self._account_name(label)
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
				"new_password": password or self.password,
			}
		)
		doc.insert(ignore_permissions=True)
		self.created_users.append(doc.name)
		return doc

	def test_edit_user_updates_role_and_optional_password(self):
		user = self._create_user("edit-role", ["COO"])
		new_password = f"Aa1!{frappe.generate_hash(length=24)}"

		result = edit_user(user.username, "CFO", new_password)
		user.reload()

		self.assertTrue(result["ok"])
		self.assertEqual(result["message"], "User Updated")
		self.assertEqual([row.role for row in user.roles], ["CFO"])
		self.assertEqual(check_password(user.name, new_password), user.name)
		self.assertNotIn(new_password, str(result))

	def test_edit_user_keeps_existing_password_when_blank(self):
		user = self._create_user("edit-no-password", ["COO"])

		result = edit_user(user.username, "CFO", "")

		self.assertTrue(result["ok"])
		self.assertEqual(check_password(user.name, self.password), user.name)

	def test_edit_user_never_assigns_system_manager(self):
		user = self._create_user("edit-system-manager", ["COO"])

		result = edit_user(user.username, "System Manager")
		user.reload()

		self.assertFalse(result["ok"])
		self.assertEqual(result["field"], "role")
		self.assertEqual(result["message"], "Please choose a valid role.")
		self.assertEqual([row.role for row in user.roles], ["COO"])

	def test_edit_user_does_not_return_or_log_passwords(self):
		user = self._create_user("edit-log", ["COO"])
		new_password = f"Aa1!{frappe.generate_hash(length=24)}"

		with patch(
			"my_custom_app.admin.frappe.get_doc",
			side_effect=Exception(f"save failed for {new_password}"),
		):
			with patch("my_custom_app.admin.frappe.log_error") as log_error:
				result = edit_user(user.username, "CFO", new_password)

		self.assertFalse(result["ok"])
		self.assertNotIn(new_password, str(result))
		self.assertNotIn(new_password, str(log_error.call_args))

	def test_non_system_admin_cannot_edit_user(self):
		target = self._create_user("edit-target", ["COO"])
		actor = self._create_user("edit-actor", ["COO"])
		frappe.set_user(actor.name)
		try:
			with self.assertRaises(frappe.PermissionError):
				edit_user(target.username, "CFO")
		finally:
			frappe.set_user("Administrator")

		target.reload()
		self.assertEqual([row.role for row in target.roles], ["COO"])

	def test_deactivate_user_only_disables_the_record(self):
		user = self._create_user("deactivate", ["COO"])

		result = deactivate_user(user.username)
		user.reload()

		self.assertTrue(result["ok"])
		self.assertEqual(result["message"], "User Deactivated")
		self.assertTrue(frappe.db.exists("User", user.name))
		self.assertFalse(user.enabled)
		self.assertEqual([row.role for row in user.roles], ["COO"])
		self.assertNotIn(self.password, str(result))

	def test_deactivate_user_refuses_your_own_account(self):
		user = self._create_user("deactivate-self", ["System Admin"])
		frappe.set_user(user.name)
		try:
			result = deactivate_user(user.username)
		finally:
			frappe.set_user("Administrator")

		user.reload()
		self.assertFalse(result["ok"])
		self.assertEqual(result["message"], "You cannot deactivate your own account.")
		self.assertTrue(user.enabled)

	def test_deactivate_user_refuses_last_active_system_admin(self):
		user = self._create_user("deactivate-last-admin", ["System Admin"])

		with patch("my_custom_app.admin._active_system_admin_count", return_value=1):
			result = deactivate_user(user.username)

		user.reload()
		self.assertFalse(result["ok"])
		self.assertEqual(result["message"], "You cannot deactivate the last active System Admin.")
		self.assertTrue(user.enabled)

	def test_deactivate_user_allows_system_admin_when_another_is_active(self):
		first = self._create_user("deactivate-admin-one", ["System Admin"])
		second = self._create_user("deactivate-admin-two", ["System Admin"])

		result = deactivate_user(first.username)
		first.reload()
		second.reload()

		self.assertTrue(result["ok"])
		self.assertFalse(first.enabled)
		self.assertTrue(second.enabled)

	def test_deactivate_user_refuses_administrator(self):
		before = frappe.db.get_value("User", "Administrator", "enabled")

		result = deactivate_user("Administrator")

		self.assertFalse(result["ok"])
		self.assertEqual(result["message"], "This account cannot be deactivated.")
		self.assertEqual(frappe.db.get_value("User", "Administrator", "enabled"), before)

	def test_non_system_admin_cannot_deactivate_user(self):
		target = self._create_user("deactivate-target", ["COO"])
		actor = self._create_user("deactivate-actor", ["COO"])
		frappe.set_user(actor.name)
		try:
			with self.assertRaises(frappe.PermissionError):
				deactivate_user(target.username)
		finally:
			frappe.set_user("Administrator")

		target.reload()
		self.assertTrue(target.enabled)
