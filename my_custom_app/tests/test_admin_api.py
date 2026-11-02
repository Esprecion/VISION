from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from my_custom_app.admin import can_manage_users, get_managed_roles, get_user, list_users
from my_custom_app.admin_roles import ALLOWED_ROLES, ensure_roles


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

	def test_can_manage_users_uses_server_permission(self):
		self.assertTrue(can_manage_users())

		coo = self._create_user("access-coo", ["COO"])
		frappe.set_user(coo.name)
		try:
			self.assertFalse(can_manage_users())
		finally:
			frappe.set_user("Administrator")

		system_admin = self._create_user("access-admin", ["System Admin"])
		frappe.set_user(system_admin.name)
		try:
			self.assertTrue(can_manage_users())
		finally:
			frappe.set_user("Administrator")

	def test_managed_roles_never_include_system_manager(self):
		self.assertEqual(get_managed_roles(), list(ALLOWED_ROLES))
		self.assertNotIn("System Manager", get_managed_roles())

	def test_list_users_uses_username_and_managed_role(self):
		user = self._create_user("coo", ["COO"])

		rows = list_users()
		row = next(item for item in rows if item["account_name"] == user.username)

		self.assertEqual(row["role"], "COO")
		self.assertFalse(row["has_extra_roles"])
		self.assertTrue(row["enabled"])

	def test_list_users_includes_inactive_status(self):
		active = self._create_user("active", ["COO"])
		inactive = self._create_user("inactive", ["CFO"])
		frappe.db.set_value("User", inactive.name, "enabled", 0)

		rows = list_users()
		active_row = next(item for item in rows if item["account_name"] == active.username)
		inactive_row = next(item for item in rows if item["account_name"] == inactive.username)

		self.assertTrue(active_row["enabled"])
		self.assertFalse(inactive_row["enabled"])

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
		self.assertTrue(detail["enabled"])

	def test_get_user_returns_inactive_status(self):
		user = self._create_user("cfo-inactive", ["CFO"])
		frappe.db.set_value("User", user.name, "enabled", 0)

		detail = get_user(user.username)

		self.assertFalse(detail["enabled"])

	def test_get_user_returns_first_managed_role(self):
		user = self._create_user("cfo-multi", ["CFO", "System Admin"])

		detail = get_user(user.username)

		self.assertEqual(detail["role"], "CFO")
		self.assertTrue(detail["has_extra_roles"])

	def test_list_users_marks_the_current_account(self):
		current = self._create_user("list-self", ["System Admin"])
		other = self._create_user("list-other", ["COO"])

		frappe.set_user(current.name)
		try:
			rows = list_users()
		finally:
			frappe.set_user("Administrator")

		current_row = next(item for item in rows if item["account_name"] == current.username)
		other_row = next(item for item in rows if item["account_name"] == other.username)

		self.assertTrue(current_row["is_self"])
		self.assertFalse(other_row["is_self"])

	def test_list_users_flags_the_last_active_system_admin(self):
		admin = self._create_user("list-last-admin", ["System Admin"])
		coo = self._create_user("list-not-admin", ["COO"])

		with patch("my_custom_app.admin._active_system_admin_count", return_value=1):
			rows = list_users()

		admin_row = next(item for item in rows if item["account_name"] == admin.username)
		coo_row = next(item for item in rows if item["account_name"] == coo.username)

		self.assertTrue(admin_row["is_last_active_system_admin"])
		self.assertFalse(coo_row["is_last_active_system_admin"])

	def test_list_users_does_not_flag_a_disabled_system_admin(self):
		admin = self._create_user("list-disabled-admin", ["System Admin"])
		frappe.db.set_value("User", admin.name, "enabled", 0)

		with patch("my_custom_app.admin._active_system_admin_count", return_value=1):
			rows = list_users()

		row = next(item for item in rows if item["account_name"] == admin.username)

		self.assertFalse(row["is_last_active_system_admin"])

	def test_get_user_marks_the_current_account(self):
		current = self._create_user("detail-self", ["System Admin"])
		other = self._create_user("detail-other", ["COO"])

		frappe.set_user(current.name)
		try:
			current_detail = get_user(current.username)
			other_detail = get_user(other.username)
		finally:
			frappe.set_user("Administrator")

		self.assertTrue(current_detail["is_self"])
		self.assertFalse(other_detail["is_self"])

	def test_get_user_flags_the_last_active_system_admin(self):
		admin = self._create_user("detail-last-admin", ["System Admin"])
		coo = self._create_user("detail-not-admin", ["COO"])

		with patch("my_custom_app.admin._active_system_admin_count", return_value=1):
			admin_detail = get_user(admin.username)
			coo_detail = get_user(coo.username)

		self.assertTrue(admin_detail["is_last_active_system_admin"])
		self.assertFalse(coo_detail["is_last_active_system_admin"])

	def test_get_user_rejects_protected_users(self):
		for account_name in ("Administrator", "Guest"):
			with self.subTest(account_name=account_name):
				with self.assertRaises(frappe.DoesNotExistError):
					get_user(account_name)

	def test_get_user_rejects_user_without_a_managed_role(self):
		user = self._create_user("unmanaged-detail", ["System Manager"])

		with self.assertRaises(frappe.DoesNotExistError):
			get_user(user.username)

	def test_non_system_admin_cannot_read_users(self):
		user = self._create_user("coo-reader", ["COO"])
		frappe.set_user(user.name)
		try:
			with self.assertRaises(frappe.PermissionError):
				get_managed_roles()
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
