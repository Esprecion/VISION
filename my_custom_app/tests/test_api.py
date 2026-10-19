import frappe
from frappe.tests.utils import FrappeTestCase

from my_custom_app.api import create_deal_with_details


def ensure_stage(name="Lead"):
	if not frappe.db.exists("Pipeline Stage", name):
		frappe.get_doc({"doctype": "Pipeline Stage", "stage_name": name}).insert(ignore_permissions=True)
	return name


class TestCreateDealWithDetails(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.stage = ensure_stage()

	def tearDown(self):
		frappe.set_user("Administrator")

	def _create(self, title, client, items):
		return create_deal_with_details({"deal_title": title, "stage": self.stage}, client, items)

	def test_creates_new_client_and_products(self):
		deal = self._create(
			"New everything",
			{"new": {"client_name": "Acme New Client", "contact_email": "a@example.com"}},
			[
				{
					"new_product": {"product_name": "Widget New", "type": "Software"},
					"quantity": 2,
					"price": 100,
				},
				{
					"new_product": {"product_name": "Gadget New", "type": "Hardware"},
					"quantity": 1,
					"price": 50,
				},
			],
		)
		self.assertTrue(frappe.db.exists("Deal", deal["name"]))
		self.assertEqual(deal["client"], "Acme New Client")
		self.assertTrue(frappe.db.exists("Client", "Acme New Client"))
		self.assertTrue(frappe.db.exists("Product", "Widget New"))
		self.assertTrue(frappe.db.exists("Product", "Gadget New"))
		self.assertEqual(deal["value"], 250)
		self.assertEqual(len(deal["items"]), 2)

	def test_reuses_existing_client_and_product(self):
		frappe.get_doc({"doctype": "Client", "client_name": "Existing Client"}).insert()
		frappe.get_doc({"doctype": "Product", "product_name": "Existing Product", "type": "Support"}).insert()

		clients_before = frappe.db.count("Client")
		products_before = frappe.db.count("Product")

		deal = self._create(
			"Reuse",
			{"existing": "Existing Client"},
			[{"product": "Existing Product", "quantity": 3, "price": 10}],
		)

		self.assertEqual(deal["client"], "Existing Client")
		self.assertEqual(deal["items"][0]["product"], "Existing Product")
		self.assertEqual(deal["value"], 30)
		self.assertEqual(frappe.db.count("Client"), clients_before)
		self.assertEqual(frappe.db.count("Product"), products_before)

	def test_duplicate_client_name_is_reused(self):
		payload = {"new": {"client_name": "Repeat Client"}}
		first = self._create(
			"First",
			payload,
			[{"new_product": {"product_name": "P1", "type": "Software"}, "quantity": 1, "price": 1}],
		)
		second = self._create(
			"Second",
			payload,
			[{"new_product": {"product_name": "P2", "type": "Software"}, "quantity": 1, "price": 1}],
		)
		self.assertEqual(first["client"], "Repeat Client")
		self.assertEqual(second["client"], "Repeat Client")
		self.assertEqual(frappe.db.count("Client", {"client_name": "Repeat Client"}), 1)

	def test_same_new_product_on_two_lines_created_once(self):
		deal = self._create(
			"Dupe product",
			{"new": {"client_name": "Dupe Product Client"}},
			[
				{
					"new_product": {"product_name": "Shared Thing", "type": "Software"},
					"quantity": 1,
					"price": 10,
				},
				{
					"new_product": {"product_name": "shared thing", "type": "Software"},
					"quantity": 2,
					"price": 5,
				},
			],
		)
		self.assertEqual(frappe.db.count("Product", {"product_name": "Shared Thing"}), 1)
		self.assertEqual(deal["value"], 20)
		self.assertEqual({row["product"] for row in deal["items"]}, {"Shared Thing"})

	def test_user_without_create_permission_is_blocked(self):
		email = "no-deal-perm@example.com"
		if not frappe.db.exists("User", email):
			frappe.get_doc(
				{"doctype": "User", "email": email, "first_name": "No Perm", "send_welcome_email": 0}
			).insert(ignore_permissions=True)
		frappe.set_user(email)
		try:
			with self.assertRaises(frappe.PermissionError):
				self._create(
					"Blocked",
					{"new": {"client_name": "Blocked Client"}},
					[
						{
							"new_product": {"product_name": "Blocked Product", "type": "Software"},
							"quantity": 1,
							"price": 1,
						}
					],
				)
		finally:
			frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists("Client", "Blocked Client"))

	def test_nothing_saved_when_one_line_fails(self):
		with self.assertRaises(frappe.ValidationError):
			self._create(
				"All or nothing",
				{"new": {"client_name": "Should Not Exist Client"}},
				[
					{
						"new_product": {"product_name": "Valid Line Product", "type": "Software"},
						"quantity": 1,
						"price": 10,
					},
					{
						"new_product": {"product_name": "Bad Line Product", "type": "Software"},
						"quantity": 0,
						"price": 10,
					},
				],
			)
		self.assertFalse(frappe.db.exists("Client", "Should Not Exist Client"))
		self.assertFalse(frappe.db.exists("Product", "Valid Line Product"))
		self.assertFalse(frappe.db.exists("Product", "Bad Line Product"))
		self.assertFalse(frappe.db.exists("Deal", {"deal_title": "All or nothing"}))
