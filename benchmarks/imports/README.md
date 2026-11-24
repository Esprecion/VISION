# Import accuracy benchmark

This harness measures field-level accuracy for 30 receipt imports and 10 service contract imports.

## Layout

```
benchmarks/imports/
  answers.example.json   committed template with all 40 answer IDs
  answers.json           local copy with real expected values (ignored)
  receipts/              local receipt documents (ignored)
  contracts/             local service contracts (ignored)
  reports/               generated accuracy reports (ignored)
```

Real documents, real answers, and generated reports are intentionally not committed.

## Prepare a run

1. Copy `answers.example.json` to `answers.json`.
2. Put 30 receipts in `receipts/` using the file names from the answer file.
3. Put 10 service contracts in `contracts/` using the file names from the answer file.
4. Fill each `expected` object. Use `null` when a field is genuinely absent from the document.

## Run

From the bench root in WSL:

```bash
bench --site site1.local execute my_custom_app.shared.import_evaluation.run --kwargs '{"answers_path":"benchmarks/imports/answers.json","output_path":"benchmarks/imports/reports/latest.csv"}'
```

The command prints and optionally writes a CSV with one row per field:

```
kind,field,correct,total,accuracy,rag
receipt,vendor,29,30,96.7%,green
contract,milestones,8,10,80.0%,amber
```

## Scoring rules

- Strings are trimmed, whitespace-normalised and compared case-insensitively.
- Dates use `YYYY-MM-DD`.
- Amounts are compared numerically to two decimal places.
- `milestones` is correct only when the list length and each row's name and amount match by position.
- An expected `null` and a missing extraction both count as correct.
- Green is at least 95% accuracy, amber is 80% to under 95%, and red is under 80%.
