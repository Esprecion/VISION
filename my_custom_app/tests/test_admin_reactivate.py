import frappe
from frappe.tests.utils import FrappeTestCase

from my_custom_app.admin import deactivate_user, reactivate_user
from my_custom_app.admin_roles import ensure_roles


class TestAdminReactivateUser(FrappeTestCase):
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

	def test_reactivate_user_enables_account_and_keeps_roles(self):
		user = self._create_user("reactivate", ["COO"])
		deactivate_user(user.username)

		result = reactivate_user(user.username)
		user.reload()

		self.assertTrue(result["ok"])
		self.assertEqual(result["message"], "User Reactivated")
		self.assertEqual(result["user"]["account_name"], user.username)
		self.assertEqual(result["user"]["role"], "COO")
		self.assertEqual(result["user"]["roles"], ["COO"])
		self.assertFalse(result["user"]["has_extra_roles"])
		self.assertTrue(result["user"]["enabled"])
		self.assertTrue(user.enabled)
		self.assertTrue(frappe.db.exists("User", user.name))
		self.assertNotIn(self.password, str(result))

	def test_reactivate_user_is_idempotent(self):
		user = self._create_user("reactivate-active", ["CFO"])

		result = reactivate_user(user.username)
		user.reload()

		self.assertTrue(result["ok"])
		self.assertTrue(user.enabled)

	def test_reactivate_user_requires_an_account_name(self):
		result = reactivate_user("")

		self.assertFalse(result["ok"])
		self.assertEqual(result["field"], "account_name")
		self.assertEqual(result["fields"], ["account_name"])
		self.assertEqual(result["message"], "Please complete all required user details.")

	def test_reactivate_user_rejects_unknown_user(self):
		result = reactivate_user(self._account_name("missing"))

		self.assertFalse(result["ok"])
		self.assertEqual(result["field"], "account_name")
		self.assertEqual(result["message"], "User not found.")

	def test_reactivate_user_refuses_protected_users(self):
		for account_name in ("Administrator", "Guest"):
			with self.subTest(account_name=account_name):
				result = reactivate_user(account_name)

				self.assertFalse(result["ok"])
				self.assertEqual(result["message"], "This account cannot be reactivated.")

	def test_non_system_admin_cannot_reactivate_user(self):
		target = self._create_user("reactivate-target", ["COO"], enabled=0)
		actor = self._create_user("reactivate-actor", ["COO"])
		frappe.set_user(actor.name)
		try:
			with self.assertRaises(frappe.PermissionError):
				reactivate_user(target.username)
		finally:
			frappe.set_user("Administrator")

		target.reload()
		self.assertFalse(target.enabled)
