import base64
import binascii
import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import frappe

DATA_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".pdf", ".docx", ".doc"}
RECEIPT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".pdf"}
TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json"}
MAX_SOURCE_CHARS = 60000

RECORD_FIELDS = {
	"client": [
		"client_name",
		"first_name",
		"last_name",
		"address",
		"street_barangay",
		"city_municipality",
		"province",
		"postal_code",
		"country",
		"contact_person",
		"contact_email",
		"contact_phone",
		"territory",
	],
	"product": ["product_name", "type", "description"],
	"deal": [
		"deal_title",
		"expected_close_date",
		"client",
		"client_name",
		"items",
	],
	"contract": [
		"deal",
		"deal_title",
		"client",
		"client_name",
		"start_date",
		"end_date",
		"terms_and_conditions",
		"milestones",
	],
}
EXPENSE_FIELDS = ["vendor", "category", "expense_date", "date", "amount", "description"]
PRODUCT_TYPES = {"Software", "Hardware", "Consulting", "Support"}
EXPENSE_CATEGORIES = {"Tools and Subscriptions", "Hardware", "Contractors and Freelancers", "Other"}
ITEM_FIELDS = {"product", "newName", "newType", "quantity", "price"}
MILESTONE_FIELDS = {"milestone_name", "amount"}


class ProviderUnavailable(frappe.ValidationError):
	pass


@frappe.whitelist()
def extract_record_fields(kind=None, source_text=None, file_name=None, file_content=None):
	kind = str(kind or "").strip().lower()
	if kind == "contract":
		_require_any_role("CBO", "COO")
	else:
		_require_role("CBO")
	if kind not in RECORD_FIELDS:
		frappe.throw("Unsupported form type.", frappe.ValidationError)

	fields = RECORD_FIELDS[kind]
	source = _prepare_source(
		source_text,
		file_name,
		file_content,
		DATA_EXTENSIONS,
		"Please provide text or a supported file.",
	)
	values = _extract(kind, fields, source, file_name)
	values = _normalize(values, fields, kind)
	if not values:
		frappe.throw("No details could be found in the data.", frappe.ValidationError)
	return values


@frappe.whitelist()
def extract_expense_fields(source_text=None, file_name=None, file_content=None):
	_require_role("CFO")
	source = _prepare_source(
		None,
		file_name,
		file_content,
		RECEIPT_EXTENSIONS,
		"Please upload a receipt as an image or PDF.",
	)
	values = _extract("expense", EXPENSE_FIELDS, source, file_name)
	values = _normalize(values, EXPENSE_FIELDS, "expense")
	if not values:
		frappe.throw("No details could be read from the receipt.", frappe.ValidationError)
	return values


def _require_role(role):
	if role not in frappe.get_roles():
		frappe.throw("Not permitted.", frappe.PermissionError)


def _require_any_role(*roles):
	if not any(role in frappe.get_roles() for role in roles):
		frappe.throw("Not permitted.", frappe.PermissionError)


def _prepare_source(source_text, file_name, file_content, allowed_extensions, error_message):
	text = str(source_text or "").strip()
	name = str(file_name or "").strip()
	content = str(file_content or "").strip()

	if not text and not (name and content):
		frappe.throw(error_message, frappe.ValidationError)
	if not name:
		return text[:MAX_SOURCE_CHARS]

	extension = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
	if extension not in allowed_extensions:
		frappe.throw(error_message, frappe.ValidationError)
	if extension in TEXT_EXTENSIONS:
		try:
			return base64.b64decode(content, validate=True).decode("utf-8", errors="replace")[
				:MAX_SOURCE_CHARS
			]
		except (binascii.Error, ValueError):
			raise ProviderUnavailable("AI provider unavailable")
	return "File: " + name + "\nBase64 content:\n" + content[:MAX_SOURCE_CHARS]


def _extract(kind, fields, source, file_name):
	prompt = _build_prompt(kind, fields, source, file_name)
	body = {
		"model": frappe.conf.get("vision_ai_model") or "gpt-4o-mini",
		"messages": [
			{"role": "system", "content": "Extract form values. Return only a JSON object."},
			{"role": "user", "content": prompt},
		],
		"temperature": 0,
	}
	endpoint = frappe.conf.get("vision_ai_endpoint")
	api_key = frappe.conf.get("vision_ai_api_key")
	if not endpoint or not api_key:
		raise ProviderUnavailable("AI provider unavailable")

	request = Request(
		str(endpoint),
		data=json.dumps(body).encode("utf-8"),
		headers={
			"Authorization": "Bearer " + str(api_key),
			"Content-Type": "application/json",
		},
		method="POST",
	)
	try:
		with urlopen(request, timeout=20) as response:
			payload = json.loads(response.read().decode("utf-8"))
		content = _response_content(payload)
		return _parse_json(content)
	except (HTTPError, URLError, TimeoutError, ValueError, KeyError, IndexError, TypeError):
		raise ProviderUnavailable("AI provider unavailable")


def _build_prompt(kind, fields, source, file_name):
	field_list = ", ".join(fields)
	if kind == "expense":
		instruction = (
			"Extract expense details from the receipt. Use the keys: "
			+ field_list
			+ ". Category must be one of: "
			+ ", ".join(sorted(EXPENSE_CATEGORIES))
			+ ". Return only JSON."
		)
	elif kind == "deal":
		instruction = (
			"Extract deal details. Use the keys: "
			+ field_list
			+ ". For items, return objects with product, newName, newType, quantity, and price. "
			+ "Return only JSON."
		)
	elif kind == "contract":
		instruction = (
			"Extract service contract details. Use the keys: "
			+ field_list
			+ ". For milestones, return objects with milestone_name and amount. "
			+ "Dates must be YYYY-MM-DD. Return only JSON."
		)
	else:
		instruction = "Extract form values. Use the keys: " + field_list + ". Return only JSON."
	name_line = "File name: " + str(file_name or "") + "\n" if file_name else ""
	return instruction + "\n\n" + name_line + "Source data:\n" + source


def _response_content(payload):
	if isinstance(payload, dict):
		choices = payload.get("choices")
		if isinstance(choices, list) and choices:
			message = choices[0].get("message") or {}
			if isinstance(message, dict) and message.get("content"):
				return str(message["content"])
		for key in ("fields", "values", "data", "result", "output", "text"):
			if key in payload:
				value = payload[key]
				if isinstance(value, str):
					return value
				if isinstance(value, dict):
					return json.dumps(value)
	return ""


def _parse_json(content):
	text = str(content or "").strip()
	if text.startswith("```"):
		text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
		text = re.sub(r"```$", "", text).strip()
	start = text.find("{")
	end = text.rfind("}")
	if start == -1 or end <= start:
		raise ValueError("No JSON object returned")
	parsed = json.loads(text[start : end + 1])
	if not isinstance(parsed, dict):
		raise ValueError("Provider response must be an object")
	return parsed


def _normalize(values, fields, kind):
	if not isinstance(values, dict):
		return {}
	source = values.get("fields") or values.get("values") or values.get("data") or values
	if not isinstance(source, dict):
		return {}

	cleaned = {}
	for field in fields:
		if field in {"items", "milestones"}:
			continue
		value = source.get(field)
		if value is None:
			continue
		text = str(value).strip()
		if not text:
			continue
		if field == "type" and kind == "product" and text not in PRODUCT_TYPES:
			continue
		if field == "category" and kind == "expense" and text not in EXPENSE_CATEGORIES:
			continue
		cleaned[field] = text

	if "items" in fields and isinstance(source.get("items"), list):
		items = []
		for item in source["items"]:
			if not isinstance(item, dict):
				continue
			row = {}
			for key in ITEM_FIELDS:
				value = item.get(key)
				if value is not None and str(value).strip():
					row[key] = str(value).strip()
			if row:
				items.append(row)
		if items:
			cleaned["items"] = items

	if "milestones" in fields and isinstance(source.get("milestones"), list):
		milestones = []
		for milestone in source["milestones"]:
			if not isinstance(milestone, dict):
				continue
			row = {}
			for key in MILESTONE_FIELDS:
				value = milestone.get(key)
				if value is not None and str(value).strip():
					row[key] = str(value).strip()
			if row:
				milestones.append(row)
		if milestones:
			cleaned["milestones"] = milestones

	if kind == "expense":
		if not cleaned.get("expense_date") and cleaned.get("date"):
			cleaned["expense_date"] = cleaned.pop("date")
		elif "date" in cleaned:
			cleaned.pop("date")
	return cleaned
