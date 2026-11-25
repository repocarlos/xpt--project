# Research schemas

`options-study.schema.json` defines a versioned options-study envelope with distinct PM threshold quotes, listed-option quotes, normalized matches, and derived estimates. The synthetic fixture lives at `examples/options-study.synthetic.json`.

Run the stdlib structural and rights-gate checks with:

```sh
python -m unittest discover -s schemas -p 'test_options_study_contract.py'
python schemas/validate_options_study.py --requested-use raw_storage --requested-use derived_data
```

`validate_options_study.py` checks core fixture structure and refuses observed records unless access and each requested use are approved. It is deliberately not a complete JSON Schema validator. Use a full Draft 2020-12 validator before production ingestion.
