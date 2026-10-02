import frappe
from frappe.model.document import Document

from my_custom_app.finance.projects import CONFIRMED, ensure_project


class ServiceContract(Document):
    def validate(self):
        self.value = sum((m.amount or 0) for m in self.payment_milestones)

    def on_update(self):
        # A confirmed contract always has a Project
        if self.status in CONFIRMED:
            ensure_project(self)
