import base64
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

import frappe

from my_custom_app.shared import ai_imports

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ANSWERS_PATH = "benchmarks/imports/answers.json"
EXPECTED_COUNTS = {"receipts": 30, "contracts": 10}
FIELDS = {
	"receipts": ["vendor", "category", "expense_date", "amount", "description"],
	"contracts": [
		"deal",
		"client",
		"start_date",
		"end_date",
		"terms_and_conditions",
		"milestones",
	],
}
GREEN_ACCURACY = 0.95
AMBER_ACCURACY = 0.80


def build_report(answers_path=None, root=None, extractor=None):
	base = Path(root) if root else DEFAULT_ROOT
	path = Path(answers_path or DEFAULT_ANSWERS_PATH)
	if not path.is_absolute():
		path = base / path
	data = json.loads(path.read_text(encoding="utf-8"))
	validate_answers(data)
	using_default_extractor = extractor is None
	extract = extractor or _extract_document
	rows = []
	for plural, fields in FIELDS.items():
		stats = {field: [0, 0] for field in fields}
		kind = plural[:-1]
		for entry in data[plural]:
			file_name = str(entry["file"])
			file_path = base / file_name
			if using_default_extractor and not file_path.exists():
				raise FileNotFoundError(f"Missing {kind} document: {file_name}")
			values = extract(kind, file_path, file_name)
			for field in fields:
				expected = normalize_field(field, entry["expected"][field])
				actual = normalize_field(field, values.get(field))
				stats[field][1] += 1
				if expected == actual:
					stats[field][0] += 1
		for field in fields:
			correct, total = stats[field]
			accuracy = correct / total if total else 0
			rows.append(
				{
					"kind": kind,
					"field": field,
					"correct": correct,
					"total": total,
					"accuracy": accuracy,
					"rag": accuracy_color(accuracy),
				}
			)
	return rows


def validate_answers(data):
	if not isinstance(data, dict):
		raise ValueError("Answer file must be an object.")
	for plural, expected_count in EXPECTED_COUNTS.items():
		entries = data.get(plural)
		if not isinstance(entries, list):
			raise ValueError(f"Answer file must include a {plural} list.")
		if len(entries) != expected_count:
			raise ValueError(f"Expected {expected_count} {plural} answers, found {len(entries)}.")
		seen = set()
		for entry in entries:
			if not isinstance(entry, dict):
				raise ValueError(f"Each {plural[:-1]} answer must be an object.")
			identifier = str(entry.get("id") or "").strip()
			file_name = str(entry.get("file") or "").strip()
			expected = entry.get("expected")
			if not identifier or not file_name:
				raise ValueError(f"Each {plural[:-1]} answer needs an id and file.")
			if identifier in seen:
				raise ValueError(f"Duplicate {plural[:-1]} answer id: {identifier}")
			if not isinstance(expected, dict):
				raise ValueError(f"Each {plural[:-1]} answer needs an expected object.")
			missing = [field for field in FIELDS[plural] if field not in expected]
			if missing:
				raise ValueError(f"{identifier} is missing expected fields: {', '.join(missing)}")
			seen.add(identifier)


def normalize_field(field, value):
	if value is None or str(value).strip() == "":
		return None
	if field == "milestones":
		if not isinstance(value, list):
			return normalize_text(value)
		rows = []
		for row in value:
			if not isinstance(row, dict):
				rows.append(normalize_text(row))
				continue
			rows.append((normalize_text(row.get("milestone_name")), normalize_amount(row.get("amount"))))
		return rows
	if field == "amount":
		return normalize_amount(value)
	return normalize_text(value)


def normalize_text(value):
	if value is None:
		return None
	return re.sub(r"\s+", " ", str(value).strip()).casefold()


def normalize_amount(value):
	text = re.sub(r"[₱,\s]", "", str(value).strip())
	try:
		return str(Decimal(text).quantize(Decimal("0.01")))
	except (InvalidOperation, ValueError):
		return normalize_text(value)


def accuracy_color(accuracy):
	if accuracy >= GREEN_ACCURACY:
		return "green"
	if accuracy >= AMBER_ACCURACY:
		return "amber"
	return "red"


def format_report(rows):
	lines = ["kind,field,correct,total,accuracy,rag"]
	for row in rows:
		lines.append(
			f'{row["kind"]},{row["field"]},{row["correct"]},{row["total"]},'
			f'{row["accuracy"]:.1%},{row["rag"]}'
		)
	return "\n".join(lines)


@frappe.whitelist()
def run(answers_path=None, output_path=None, root=None):
	rows = build_report(answers_path=answers_path, root=root)
	report = format_report(rows)
	print(report)
	if output_path:
		path = Path(output_path)
		if not path.is_absolute():
			path = DEFAULT_ROOT / path
		path.parent.mkdir(parents=True, exist_ok=True)
		path.write_text(report + "\n", encoding="utf-8")
	return rows


def _extract_document(kind, file_path, file_name):
	if kind == "receipt":
		fields = ai_imports.EXPENSE_FIELDS
		allowed = ai_imports.RECEIPT_EXTENSIONS
		extract_kind = "expense"
	else:
		fields = ai_imports.RECORD_FIELDS["contract"]
		allowed = ai_imports.DATA_EXTENSIONS
		extract_kind = "contract"
	content = base64.b64encode(file_path.read_bytes()).decode("utf-8")
	source = ai_imports._prepare_source(None, file_name, content, allowed, "Unsupported file.")
	values = ai_imports._extract(extract_kind, fields, source, file_name)
	return ai_imports._normalize(values, fields, extract_kind)
