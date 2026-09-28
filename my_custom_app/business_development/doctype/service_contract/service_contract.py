import frappe
from frappe.model.document import Document


class ServiceContract(Document):
	def validate(self):
		self.value = sum((m.amount or 0) for m in self.payment_milestones)
