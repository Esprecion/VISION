import unittest

from my_custom_app.finance.seed_reports import REPORTS
from my_custom_app.patches.add_total_revenue_by_period_report import NAME, QUERY


class TestTotalRevenueByPeriodReport(unittest.TestCase):
	def test_patch_query_uses_paid_invoices_and_range_filters(self):
		self.assertEqual(NAME, "Total Revenue by Period")
		self.assertIn("status = 'Paid'", QUERY)
		self.assertIn("SUM(paid_amount)", QUERY)
		self.assertIn("%(from_date)s", QUERY)
		self.assertIn("%(to_date)s", QUERY)

	def test_seed_reports_include_the_new_report(self):
		names = [report[0] for report in REPORTS]
		self.assertIn(NAME, names)
