import frappe
from frappe.tests.utils import FrappeTestCase

from my_custom_app.administration.admin_roles import ensure_roles
from my_custom_app.shared.dashboard import (
	business_development_records_and_metrics,
	finance_records_and_metrics,
	get_dashboard_record,
	operations_records_and_metrics,
)


class TestDashboardRecordsAndMetrics(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_roles()
		self.suffix = frappe.generate_hash(length=8)
		self.created = []

	def tearDown(self):
		frappe.set_user("Administrator")
		for doctype, name in reversed(self.created):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)

	def _name(self, label):
		return f"{label}-{self.suffix}"

	def _insert(self, doc):
		doc.insert(ignore_permissions=True)
		self.created.append((doc.doctype, doc.name))
		return doc

	def _client(self, label="client"):
		return self._insert(
			frappe.get_doc(
				{
					"doctype": "Client",
					"client_name": self._name(label),
					"territory": "Metro",
				}
			)
		)

	def _deal(self, client, stage, value, label):
		return self._insert(
			frappe.get_doc(
				{
					"doctype": "Deal",
					"deal_title": self._name(label),
					"client": client.name,
					"stage": stage,
					"value": value,
					"expected_close_date": "2026-03-01",
				}
			)
		)

	def _contract(self, client, deal, status, label):
		return self._insert(
			frappe.get_doc(
				{
					"doctype": "Service Contract",
					"client": client.name,
					"deal": deal.name,
					"value": deal.value,
					"start_date": "2026-03-01",
					"status": status,
				}
			)
		)

	def _project(self, client, contract, stage, label):
		return self._insert(
			frappe.get_doc(
				{
					"doctype": "Project",
					"contract": contract.name,
					"client": client.name,
					"project_type": self._name(label),
					"stage": stage,
					"committed_date": "2026-04-01",
				}
			)
		)

	def _invoice(self, client):
		return self._insert(
			frappe.get_doc(
				{
					"doctype": "Invoice",
					"client": client.name,
					"amount": 100000,
					"issue_date": "2026-03-01",
					"due_date": "2026-03-31",
					"status": "Sent",
				}
			)
		)

	def _payment(self, invoice):
		return self._insert(
			frappe.get_doc(
				{
					"doctype": "Client Payment",
					"invoice": invoice.name,
					"amount": 30000,
					"payment_date": "2026-03-05",
					"payment_method": "Bank Transfer",
					"reference": self._name("payment"),
				}
			)
		)

	def _expense(self, project):
		return self._insert(
			frappe.get_doc(
				{
					"doctype": "Expense",
					"category": "Tools and Subscriptions",
					"amount": 5000,
					"expense_date": "2026-03-04",
					"project": project.name,
				}
			)
		)

	def test_business_development_records_and_metrics(self):
		client = self._client()
		lead_one = self._deal(client, "Lead", 1000, "lead-one")
		lead_two = self._deal(client, "Lead", 2000, "lead-two")
		self._deal(client, "Negotiation", 3000, "negotiation")
		self._deal(client, "Won", 4000, "won")
		self._contract(client, lead_one, "Draft", "draft")
		self._contract(client, lead_two, "Finalized", "finalized")

		result = business_development_records_and_metrics(client=client.name)

		self.assertTrue(result["metrics"]["deals_per_stage"]["Lead"] >= 2)
		self.assertTrue(result["metrics"]["deals_per_stage"]["Negotiation"] >= 1)
		self.assertTrue(result["metrics"]["open_deal_value"] >= 6000)
		self.assertTrue(result["metrics"]["draft_contracts"] >= 1)
		self.assertTrue(result["metrics"]["finalized_contracts"] >= 1)
		self.assertTrue(any(row["name"] == lead_one.name for row in result["records"]["deals"]))
		self.assertTrue(any(row["doctype"] == "Service Contract" for row in result["records"]["contracts"]))

	def test_business_development_stage_filter(self):
		client = self._client("filtered-client")
		self._deal(client, "Lead", 1000, "filtered-lead")
		self._deal(client, "Negotiation", 2000, "filtered-negotiation")

		result = business_development_records_and_metrics(client=client.name, stage="Lead")

		self.assertEqual(result["metrics"]["deals_per_stage"], {"Lead": 1})
		self.assertEqual(len(result["records"]["deals"]), 1)

	def test_operations_records_and_metrics(self):
		client = self._client("ops-client")
		deal = self._deal(client, "Lead", 1000, "ops-deal")
		contract = self._contract(client, deal, "Finalized", "ops-contract")
		self._project(client, contract, "Kickoff", "kickoff")
		self._project(client, contract, "Development", "development")
		self._project(client, contract, "Deployed", "deployed")

		result = operations_records_and_metrics(client=client.name)

		self.assertEqual(
			result["metrics"]["projects_per_status"],
			{"Kickoff": 1, "Development": 1, "Deployed": 1},
		)
		self.assertEqual(result["metrics"]["projects_linked_to_contract"], 3)
		self.assertEqual(len(result["records"]["projects"]), 3)

	def test_operations_status_filter(self):
		client = self._client("ops-filtered")
		deal = self._deal(client, "Lead", 1000, "ops-filtered-deal")
		contract = self._contract(client, deal, "Finalized", "ops-filtered-contract")
		self._project(client, contract, "Testing", "testing")

		result = operations_records_and_metrics(client=client.name, status="Deployed")

		self.assertEqual(result["metrics"]["projects_per_status"], {})
		self.assertEqual(result["records"]["projects"], [])

	def test_finance_records_and_metrics(self):
		client = self._client("finance-client")
		deal = self._deal(client, "Lead", 1000, "finance-deal")
		contract = self._contract(client, deal, "Finalized", "finance-contract")
		project = self._project(client, contract, "Development", "finance-project")
		invoice = self._invoice(client)
		self._payment(invoice)
		self._expense(project)

		result = finance_records_and_metrics(client=client.name)

		self.assertEqual(result["metrics"]["total_invoiced"], 100000)
		self.assertEqual(result["metrics"]["total_received"], 30000)
		self.assertEqual(result["metrics"]["outstanding_balance"], 70000)
		self.assertEqual(result["metrics"]["total_expenses"], 5000)
		self.assertEqual(len(result["records"]["invoices"]), 1)
		self.assertEqual(len(result["records"]["payments"]), 1)
		self.assertEqual(len(result["records"]["expenses"]), 1)

	def test_finance_date_filter(self):
		client = self._client("finance-filtered")
		deal = self._deal(client, "Lead", 1000, "finance-filtered-deal")
		contract = self._contract(client, deal, "Finalized", "finance-filtered-contract")
		project = self._project(client, contract, "Development", "finance-filtered-project")
		invoice = self._invoice(client)
		self._payment(invoice)
		self._expense(project)

		result = finance_records_and_metrics(client=client.name, from_date="2026-03-06", to_date="2026-03-10")

		self.assertEqual(result["metrics"]["total_invoiced"], 0)
		self.assertEqual(result["metrics"]["total_received"], 0)
		self.assertEqual(result["metrics"]["total_expenses"], 0)

	def test_get_dashboard_record_returns_read_only_fields(self):
		client = self._client("detail-client")
		deal = self._deal(client, "Lead", 1500, "detail-deal")

		result = get_dashboard_record("Deal", deal.name)

		self.assertEqual(result["doctype"], "Deal")
		self.assertEqual(result["name"], deal.name)
		self.assertTrue(any(field["label"] == "Stage" for field in result["fields"]))
		self.assertTrue(any(field["value"] == "Lead" for field in result["fields"]))

	def test_dashboard_endpoints_require_module_read(self):
		actor = self._insert(
			frappe.get_doc(
				{
					"doctype": "User",
					"email": self._name("dashboard-actor") + "@vision.local",
					"first_name": "Dashboard Actor",
					"enabled": 1,
					"user_type": "System User",
					"send_welcome_email": 0,
				}
			)
		)
		frappe.set_user(actor.name)
		try:
			with self.assertRaises(frappe.PermissionError):
				business_development_records_and_metrics()
			with self.assertRaises(frappe.PermissionError):
				operations_records_and_metrics()
			with self.assertRaises(frappe.PermissionError):
				finance_records_and_metrics()
			with self.assertRaises(frappe.PermissionError):
				get_dashboard_record("Deal", "missing")
		finally:
			frappe.set_user("Administrator")
