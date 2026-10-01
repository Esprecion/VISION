from frappe.model.document import Document


class Invoice(Document):
    pass

    def validate(self):
        if self.items:
            for r in self.items:
                r.amount = (r.quantity or 0) * (r.rate or 0)
            self.subtotal = sum((r.amount or 0) for r in self.items)
            self.charges_total = sum((c.amount or 0) for c in (self.charges or []))
            self.amount = self.subtotal + self.charges_total

    def on_update(self):
        import frappe
        if self.contract and self.milestone:
            frappe.db.set_value(
                "Contract Payment Milestone",
                {"parent": self.contract, "milestone_name": self.milestone},
                "is_paid",
                1 if self.status == "Paid" else 0,
            )
