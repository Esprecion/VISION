import frappe
from frappe import _
from frappe.model.document import Document


class Client(Document):
	def autoname(self):
		self._normalize_names(require=False)
		self.name = self.client_name

	def validate(self):
		if self.is_new():
			self._normalize_names(require=True)
		elif self.first_name or self.last_name:
			self._normalize_names(require=False)

	def _normalize_names(self, require=False):
		first = (self.first_name or "").strip()
		last = (self.last_name or "").strip()

		if not first and not last:
			parts = (self.client_name or "").split()
			if parts:
				first = parts[0]
				last = " ".join(parts[1:])

		if require:
			if not first:
				frappe.throw(_("First name is required for new clients."))
			if not last:
				frappe.throw(_("Last name is required for new clients."))

		if first:
			self.first_name = first
		if last:
			self.last_name = last
		if first or last:
			self.client_name = " ".join(part for part in (first, last) if part)
