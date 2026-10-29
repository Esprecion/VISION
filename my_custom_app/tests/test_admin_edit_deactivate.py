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

	def test_edit_user_clears_sessions_when_role_changes(self):
		user = self._create_user("edit-session-role", ["COO"])

		with patch("my_custom_app.admin.clear_sessions") as clear_sessions:
			result = edit_user(user.username, "CFO")

		self.assertTrue(result["ok"])
		clear_sessions.assert_called_once_with(user=user.name, force=True)

	def test_edit_user_clears_sessions_when_password_is_reset(self):
		user = self._create_user("edit-session-password", ["COO"])
		new_password = f"Aa1!{frappe.generate_hash(length=24)}"

		with patch("my_custom_app.admin.clear_sessions") as clear_sessions:
			result = edit_user(user.username, "COO", new_password)

		self.assertTrue(result["ok"])
		clear_sessions.assert_called_once_with(user=user.name, force=True)

	def test_edit_user_keeps_sessions_when_role_and_password_are_unchanged(self):
		user = self._create_user("edit-session-same", ["COO"])

		with patch("my_custom_app.admin.clear_sessions") as clear_sessions:
			result = edit_user(user.username, "COO")

		self.assertTrue(result["ok"])
		clear_sessions.assert_not_called()

	def test_edit_user_preserves_unrelated_roles(self):
		user = self._create_user("edit-extra-roles", ["COO", "System Manager"])

		with patch("my_custom_app.admin.clear_sessions"):
			result = edit_user(user.username, "CFO")

		user.reload()
		self.assertTrue(result["ok"])
		self.assertEqual({row.role for row in user.roles}, {"System Manager", "CFO"})
		self.assertEqual(result["user"]["roles"], ["CFO"])
		self.assertTrue(result["user"]["has_extra_roles"])

	def test_edit_user_replaces_other_managed_roles_with_one_role(self):
		user = self._create_user("edit-managed-roles", ["COO", "CFO"])

		with patch("my_custom_app.admin.clear_sessions"):
			result = edit_user(user.username, "System Admin")

		user.reload()
		self.assertTrue(result["ok"])
		self.assertEqual([row.role for row in user.roles], ["System Admin"])
		self.assertEqual(result["user"]["roles"], ["System Admin"])

	def test_edit_user_refuses_changing_your_own_role(self):
		user = self._create_user("edit-self-role", ["System Admin"])
		frappe.set_user(user.name)
		try:
			result = edit_user(user.username, "COO")
		finally:
			frappe.set_user("Administrator")

		user.reload()
		self.assertFalse(result["ok"])
		self.assertEqual(result["message"], "You cannot change your own role.")
		self.assertEqual([row.role for row in user.roles], ["System Admin"])

	def test_edit_user_allows_resetting_your_own_password(self):
		user = self._create_user("edit-self-password", ["System Admin"])
		new_password = f"Aa1!{frappe.generate_hash(length=24)}"
		frappe.set_user(user.name)
		try:
			with patch("my_custom_app.admin.clear_sessions") as clear_sessions:
				result = edit_user(user.username, "System Admin", new_password)
		finally:
			frappe.set_user("Administrator")

		self.assertTrue(result["ok"])
		self.assertEqual(check_password(user.name, new_password), user.name)
		clear_sessions.assert_called_once_with(user=user.name, force=True)

	def test_edit_user_refuses_changing_the_last_active_system_admin_role(self):
		user = self._create_user("edit-last-admin", ["System Admin"])

		with patch("my_custom_app.admin._active_system_admin_count", return_value=1):
			result = edit_user(user.username, "COO")

		user.reload()
		self.assertFalse(result["ok"])
		self.assertEqual(
			result["message"],
			"You cannot change the role of the last active System Admin.",
		)
		self.assertEqual([row.role for row in user.roles], ["System Admin"])

	def test_edit_user_allows_role_change_when_another_active_system_admin_exists(self):
		user = self._create_user("edit-other-admin", ["System Admin"])

		with patch("my_custom_app.admin._active_system_admin_count", return_value=2):
			with patch("my_custom_app.admin.clear_sessions"):
				result = edit_user(user.username, "COO")

		user.reload()
		self.assertTrue(result["ok"])
		self.assertEqual([row.role for row in user.roles], ["COO"])

	def test_edit_user_refuses_protected_users(self):
		for account_name in ("Administrator", "Guest"):
			with self.subTest(account_name=account_name):
				result = edit_user(account_name, "COO")

				self.assertFalse(result["ok"])
				self.assertEqual(result["message"], "This account cannot be edited.")

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

	def test_deactivate_user_clears_active_sessions(self):
		user = self._create_user("deactivate-session", ["COO"])

		with patch("my_custom_app.admin.clear_sessions") as clear_sessions:
			result = deactivate_user(user.username)

		self.assertTrue(result["ok"])
		clear_sessions.assert_called_once_with(user=user.name, force=True)

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

	def test_deactivate_user_refuses_protected_users(self):
		for account_name in ("Administrator", "Guest"):
			with self.subTest(account_name=account_name):
				before = frappe.db.get_value("User", account_name, "enabled")

				result = deactivate_user(account_name)

				self.assertFalse(result["ok"])
				self.assertEqual(result["message"], "This account cannot be deactivated.")
				self.assertEqual(frappe.db.get_value("User", account_name, "enabled"), before)

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
