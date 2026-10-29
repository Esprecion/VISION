import frappe
from frappe.tests.utils import FrappeTestCase

from my_custom_app.admin import (
	can_manage_users,
	create_user,
	deactivate_user,
	edit_user,
	get_managed_roles,
	get_user,
	list_users,
	reactivate_user,
)
from my_custom_app.admin_roles import ensure_roles


class TestAdminPermissions(FrappeTestCase):
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

	def _create_user(self, label, roles, enabled=1):
		account_name = self._account_name(label)
		doc = frappe.get_doc(
			{
				"doctype": "User",
				"email": f"{account_name}@vision.local",
				"first_name": account_name,
				"username": account_name,
				"send_welcome_email": 0,
				"enabled": enabled,
				"user_type": "System User",
				"roles": [{"role": role} for role in roles],
				"new_password": self.password,
			}
		)
		doc.insert(ignore_permissions=True)
		self.created_users.append(doc.name)
		return doc

	def _assert_non_admin_is_denied(self, actor, label):
		target = self._create_user(f"{label}-target", ["COO"])
		blocked_account = self._account_name(f"{label}-blocked")

		frappe.set_user(actor.name)
		try:
			self.assertFalse(can_manage_users())
			with self.assertRaises(frappe.PermissionError):
				get_managed_roles()
			with self.assertRaises(frappe.PermissionError):
				list_users()
			with self.assertRaises(frappe.PermissionError):
				get_user(target.username)
			with self.assertRaises(frappe.PermissionError):
				create_user(blocked_account, self.password, "CFO")
			with self.assertRaises(frappe.PermissionError):
				edit_user(target.username, "CFO")
			with self.assertRaises(frappe.PermissionError):
				deactivate_user(target.username)
			with self.assertRaises(frappe.PermissionError):
				reactivate_user(target.username)
		finally:
			frappe.set_user("Administrator")

		target.reload()
		self.assertTrue(target.enabled)
		self.assertEqual([row.role for row in target.roles], ["COO"])
		self.assertFalse(frappe.db.exists("User", {"username": blocked_account}))

	def test_managed_role_user_cannot_use_admin_apis(self):
		actor = self._create_user("permission-coo", ["COO"])

		self._assert_non_admin_is_denied(actor, "coo")

	def test_system_manager_role_does_not_grant_admin_access(self):
		actor = self._create_user("permission-manager", ["System Manager"])

		self._assert_non_admin_is_denied(actor, "manager")
