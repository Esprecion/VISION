from frappe.model.document import Document


class Expense(Document):
    def validate(self):
        if self.items:
            self.amount = sum((r.amount or 0) for r in self.items)
