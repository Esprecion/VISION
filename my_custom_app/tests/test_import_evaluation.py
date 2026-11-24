import json
import tempfile
import unittest
from pathlib import Path

from my_custom_app.shared.import_evaluation import (
	accuracy_color,
	build_report,
	normalize_field,
	validate_answers,
)


class TestImportEvaluation(unittest.TestCase):
	def _answers(self):
		receipt_expected = {
			"vendor": "Acme Corp",
			"category": "Tools and Subscriptions",
			"expense_date": "2026-01-15",
			"amount": "100.00",
			"description": "Monthly plan",
		}
		contract_expected = {
			"deal": "DEAL-001",
			"client": "Acme Corp",
			"start_date": "2026-01-01",
			"end_date": "2026-12-31",
			"terms_and_conditions": "Net 30",
			"milestones": [{"milestone_name": "Downpayment", "amount": "1000"}],
		}
		return {
			"receipts": [
				{
					"id": f"receipt-{i:03d}",
					"file": f"receipts/receipt-{i:03d}.pdf",
					"expected": dict(receipt_expected),
				}
				for i in range(1, 31)
			],
			"contracts": [
				{
					"id": f"contract-{i:03d}",
					"file": f"contracts/contract-{i:03d}.pdf",
					"expected": dict(contract_expected),
				}
				for i in range(1, 11)
			],
		}

	def test_validate_counts(self):
		with self.assertRaises(ValueError):
			validate_answers({"receipts": [], "contracts": []})
		validate_answers(self._answers())

	def test_normalize_field(self):
		self.assertEqual(normalize_field("amount", "₱1,200.50"), "1200.50")
		self.assertEqual(
			normalize_field(
				"milestones", [{"milestone_name": " Downpayment ", "amount": "1,000"}]
			),
			[("downpayment", "1000.00")],
		)
		self.assertEqual(normalize_field("vendor", "  Acme   Corp "), "acme corp")
		self.assertIsNone(normalize_field("vendor", None))

	def test_accuracy_color_boundaries(self):
		self.assertEqual(accuracy_color(0.95), "green")
		self.assertEqual(accuracy_color(0.80), "amber")
		self.assertEqual(accuracy_color(0.7999), "red")

	def test_reports_per_field_accuracy(self):
		data = self._answers()
		with tempfile.TemporaryDirectory() as directory:
			root = Path(directory)
			path = root / "answers.json"
			path.write_text(json.dumps(data), encoding="utf-8")

			def extractor(kind, file_path, file_name):
				plural = "receipts" if kind == "receipt" else "contracts"
				entry = next(item for item in data[plural] if item["file"] == file_name)
				values = dict(entry["expected"])
				if file_name == "receipts/receipt-001.pdf":
					values["vendor"] = "Wrong Vendor"
				return values

			rows = build_report(answers_path=path, root=root, extractor=extractor)

		by_field = {(row["kind"], row["field"]): row for row in rows}
		vendor = by_field[("receipt", "vendor")]
		self.assertEqual(vendor["correct"], 29)
		self.assertEqual(vendor["total"], 30)
		self.assertEqual(vendor["rag"], "green")
		self.assertEqual(by_field[("receipt", "amount")]["correct"], 30)
		self.assertEqual(by_field[("contract", "milestones")]["total"], 10)
		self.assertEqual(len(rows), 11)
