import frappe
from frappe.tests.utils import FrappeTestCase

from my_custom_app.admin import can_manage_users
from my_custom_app.admin_roles import ensure_roles
from my_custom_app.api import get_module_perms


class TestRoleAccess(FrappeTestCase):
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

	def _user_with_role(self, role):
		account_name = f"role-{role.lower().replace(' ', '-')}-{self.suffix}"
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
		return doc

	def _perms_for(self, role):
		user = self._user_with_role(role)
		frappe.set_user(user.name)
		try:
			return get_module_perms(), can_manage_users()
		finally:
			frappe.set_user("Administrator")

	def assert_perms(self, perms, business_dev, finance, operations):
		self.assertEqual(
			{key: perms["business_dev"][key] for key in ("read", "write")},
			{"read": business_dev[0], "write": business_dev[1]},
		)
		self.assertEqual(
			{key: perms["finance"][key] for key in ("read", "write")},
			{"read": finance[0], "write": finance[1]},
		)
		self.assertEqual(
			{key: perms["operations"][key] for key in ("read", "write")},
			{"read": operations[0], "write": operations[1]},
		)

	def test_cbo_access(self):
		perms, can_admin = self._perms_for("CBO")
		self.assert_perms(perms, (True, True), (True, False), (True, False))
		self.assertFalse(can_admin)

	def test_cfo_access(self):
		perms, can_admin = self._perms_for("CFO")
		self.assert_perms(perms, (True, False), (True, True), (True, False))
		self.assertFalse(can_admin)

	def test_coo_access(self):
		perms, can_admin = self._perms_for("COO")
		self.assert_perms(perms, (True, True), (True, True), (True, True))
		self.assertFalse(can_admin)

	def test_cto_access(self):
		perms, can_admin = self._perms_for("CTO")
		self.assert_perms(perms, (True, False), (True, False), (True, True))
		self.assertFalse(can_admin)

	def test_system_admin_has_module_and_admin_access(self):
		perms, can_admin = self._perms_for("System Admin")
		self.assert_perms(perms, (True, True), (True, True), (True, True))
		self.assertTrue(can_admin)
