from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils.password import check_password

from my_custom_app.administration.admin import delete_user, edit_user
from my_custom_app.administration.admin_roles import ensure_roles


class TestAdminEditAndDelete(FrappeTestCase):
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

	def test_edit_user_updates_account_name_and_role(self):
		user = self._create_user("edit-both", ["COO"])
		new_name = self._account_name("edit-both-new")

		with patch("my_custom_app.administration.admin.clear_sessions") as clear_sessions:
			result = edit_user(user.username, "CFO", new_name)

		user.reload()
		self.assertTrue(result["ok"])
		self.assertEqual(result["message"], "User Updated")
		self.assertEqual(result["user"]["account_name"], new_name)
		self.assertEqual(user.username, new_name)
		self.assertEqual(user.first_name, new_name)
		self.assertEqual([row.role for row in user.roles], ["CFO"])
		clear_sessions.assert_called_once_with(user=user.name, force=True)

	def test_edit_user_does_not_change_password(self):
		user = self._create_user("edit-password", ["COO"])
		new_password = f"Aa1!{frappe.generate_hash(length=24)}"

		result = edit_user(user.username, "CFO", user.username, new_password)

		user.reload()
		self.assertTrue(result["ok"])
		self.assertEqual(check_password(user.name, self.password), user.name)
		self.assertNotEqual(check_password(user.name, new_password), user.name)

	def test_edit_user_keeps_sessions_when_nothing_changes(self):
		user = self._create_user("edit-same", ["COO"])

		with patch("my_custom_app.administration.admin.clear_sessions") as clear_sessions:
			result = edit_user(user.username, "COO", user.username)

		self.assertTrue(result["ok"])
		clear_sessions.assert_not_called()

	def test_edit_user_requires_unique_account_name(self):
		user = self._create_user("edit-duplicate", ["COO"])
		other = self._create_user("edit-existing", ["COO"])

		result = edit_user(user.username, "COO", other.username)

		self.assertFalse(result["ok"])
		self.assertEqual(result["field"], "account_name")
		self.assertEqual(result["message"], "Please enter a unique account name.")

	def test_edit_user_rejects_blank_account_name(self):
		user = self._create_user("edit-blank", ["COO"])

		result = edit_user(user.username, "COO", "")

		self.assertFalse(result["ok"])
		self.assertEqual(result["field"], "new_account_name")
		self.assertEqual(result["message"], "Please complete all required user details.")

	def test_edit_user_preserves_unrelated_roles(self):
		user = self._create_user("edit-extra-roles", ["COO", "System Manager"])

		with patch("my_custom_app.administration.admin.clear_sessions"):
			result = edit_user(user.username, "CFO", user.username)

		user.reload()
		self.assertTrue(result["ok"])
		self.assertEqual({row.role for row in user.roles}, {"System Manager", "CFO"})
		self.assertTrue(result["user"]["has_extra_roles"])

	def test_edit_user_refuses_changing_last_active_system_admin_role(self):
		user = self._create_user("edit-last-admin", ["System Admin"])

		with patch("my_custom_app.administration.admin._active_system_admin_count", return_value=1):
			result = edit_user(user.username, "COO", user.username)

		user.reload()
		self.assertFalse(result["ok"])
		self.assertEqual(result["message"], "At least one System Admin is required.")
		self.assertEqual([row.role for row in user.roles], ["System Admin"])

	def test_edit_user_allows_own_role_change_when_another_admin_exists(self):
		user = self._create_user("edit-self", ["System Admin"])
		self._create_user("edit-other-admin", ["System Admin"])
		frappe.set_user(user.name)
		try:
			with patch("my_custom_app.administration.admin._active_system_admin_count", return_value=2):
				with patch("my_custom_app.administration.admin.clear_sessions"):
					result = edit_user(user.username, "COO", user.username)
		finally:
			frappe.set_user("Administrator")

		user.reload()
		self.assertTrue(result["ok"])
		self.assertEqual([row.role for row in user.roles], ["COO"])

	def test_edit_user_refuses_protected_users(self):
		for account_name in ("Administrator", "Guest"):
			with self.subTest(account_name=account_name):
				result = edit_user(account_name, "COO", account_name)
				self.assertFalse(result["ok"])
				self.assertEqual(result["message"], "This account cannot be edited.")

	def test_edit_user_never_assigns_system_manager(self):
		user = self._create_user("edit-manager", ["COO"])

		result = edit_user(user.username, "System Manager", user.username)

		self.assertFalse(result["ok"])
		self.assertEqual(result["field"], "role")

	def test_non_system_admin_cannot_edit_user(self):
		target = self._create_user("edit-target", ["COO"])
		actor = self._create_user("edit-actor", ["COO"])
		frappe.set_user(actor.name)
		try:
			with self.assertRaises(frappe.PermissionError):
				edit_user(target.username, "CFO", target.username)
		finally:
			frappe.set_user("Administrator")

		target.reload()
		self.assertEqual([row.role for row in target.roles], ["COO"])

	def test_delete_user_removes_account(self):
		user = self._create_user("delete-user", ["COO"])

		with patch("my_custom_app.administration.admin.clear_sessions") as clear_sessions:
			result = delete_user(user.username)

		self.assertTrue(result["ok"])
		self.assertEqual(result["message"], "User Deleted")
		self.assertFalse(frappe.db.exists("User", user.name))
		clear_sessions.assert_called_once_with(user=user.name, force=True)

	def test_delete_user_refuses_your_own_account(self):
		user = self._create_user("delete-self", ["System Admin"])
		frappe.set_user(user.name)
		try:
			result = delete_user(user.username)
		finally:
			frappe.set_user("Administrator")

		self.assertFalse(result["ok"])
		self.assertEqual(result["message"], "This user cannot be deleted.")
		self.assertTrue(frappe.db.exists("User", user.name))

	def test_delete_user_refuses_last_active_system_admin(self):
		user = self._create_user("delete-last-admin", ["System Admin"])

		with patch("my_custom_app.administration.admin._active_system_admin_count", return_value=1):
			result = delete_user(user.username)

		self.assertFalse(result["ok"])
		self.assertEqual(result["message"], "This user cannot be deleted.")
		self.assertTrue(frappe.db.exists("User", user.name))

	def test_delete_user_allows_system_admin_when_another_is_active(self):
		first = self._create_user("delete-admin-one", ["System Admin"])
		self._create_user("delete-admin-two", ["System Admin"])

		with patch("my_custom_app.administration.admin._active_system_admin_count", return_value=2):
			result = delete_user(first.username)

		self.assertTrue(result["ok"])
		self.assertFalse(frappe.db.exists("User", first.name))

	def test_delete_user_refuses_protected_users(self):
		for account_name in ("Administrator", "Guest"):
			with self.subTest(account_name=account_name):
				result = delete_user(account_name)
				self.assertFalse(result["ok"])
				self.assertEqual(result["message"], "This account cannot be deleted.")

	def test_non_system_admin_cannot_delete_user(self):
		target = self._create_user("delete-target", ["COO"])
		actor = self._create_user("delete-actor", ["COO"])
		frappe.set_user(actor.name)
		try:
			with self.assertRaises(frappe.PermissionError):
				delete_user(target.username)
		finally:
			frappe.set_user("Administrator")

		self.assertTrue(frappe.db.exists("User", target.name))
