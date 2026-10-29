from unittest import TestCase
from unittest.mock import patch

from my_custom_app.patches.enable_username_login import execute


class TestUsernameLoginPatch(TestCase):
	def test_execute_enables_username_login_and_clears_cache(self):
		with patch("my_custom_app.patches.enable_username_login.frappe") as frappe:
			execute()

		frappe.db.set_single_value.assert_called_once_with(
			"System Settings",
			"allow_login_using_user_name",
			1,
		)
		frappe.clear_cache.assert_called_once_with()
