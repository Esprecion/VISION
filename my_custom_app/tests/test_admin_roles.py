import os
from contextlib import redirect_stdout
from io import StringIO

import frappe
from frappe.tests.utils import FrappeTestCase

from my_custom_app.admin_roles import ALLOWED_ROLES, ensure_roles, seed_first_admin


class TestAdminRoles(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.account_name = f"admin-{frappe.generate_hash(length=8)}"
		self.password = frappe.generate_hash(length=32)
		os.environ["VISION_ADMIN_USERNAME"] = self.account_name
		os.environ["VISION_ADMIN_PASSWORD"] = self.password
		self.user_name = None

	def tearDown(self):
		frappe.set_user("Administrator")
		os.environ.pop("VISION_ADMIN_USERNAME", None)
		os.environ.pop("VISION_ADMIN_PASSWORD", None)
		if self.user_name and frappe.db.exists("User", self.user_name):
			frappe.delete_doc("User", self.user_name, force=True, ignore_permissions=True)

	def test_ensure_roles_creates_every_allowed_role(self):
		ensure_roles()
		for role in ALLOWED_ROLES:
			self.assertTrue(frappe.db.exists("Role", role), role)

	def test_ensure_roles_is_idempotent(self):
		ensure_roles()
		before = {role: frappe.db.exists("Role", role) for role in ALLOWED_ROLES}
		ensure_roles()
		self.assertEqual(before, {role: frappe.db.exists("Role", role) for role in ALLOWED_ROLES})

	def test_seed_first_admin_uses_username_and_hidden_email(self):
		self.user_name = seed_first_admin()
		user = frappe.get_doc("User", self.user_name)

		self.assertEqual(user.username, self.account_name)
		self.assertEqual(user.email, f"{self.account_name}@vision.local")
		self.assertEqual([row.role for row in user.roles], ["System Admin"])
		self.assertEqual(user.send_welcome_email, 0)
		self.assertTrue(user.enabled)

	def test_seed_first_admin_is_idempotent(self):
		self.user_name = seed_first_admin()
		second = seed_first_admin()
		self.assertEqual(second, self.user_name)

	def test_seed_first_admin_never_prints_the_password(self):
		output = StringIO()

		with redirect_stdout(output):
			self.user_name = seed_first_admin()

		self.assertNotIn(self.password, output.getvalue())
