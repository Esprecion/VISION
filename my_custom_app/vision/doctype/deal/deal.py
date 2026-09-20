import frappe
from frappe.model.document import Document


class Deal(Document):
	def on_update(self):
		previous = self.get_doc_before_save()

		if not previous:
			# first save (new Deal) — log the initial stage with no "from"
			frappe.get_doc({
				"doctype": "Stage Log",
				"deal": self.name,
				"from_stage": None,
				"to_stage": self.stage,
				"changed_on": frappe.utils.now(),
			}).insert(ignore_permissions=True)
			return

		if previous.stage != self.stage:
			frappe.get_doc({
				"doctype": "Stage Log",
				"deal": self.name,
				"from_stage": previous.stage,
				"to_stage": self.stage,
				"changed_on": frappe.utils.now(),
			}).insert(ignore_permissions=True)
