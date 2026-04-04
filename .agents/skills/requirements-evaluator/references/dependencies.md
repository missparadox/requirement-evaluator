# Runtime Dependencies

This skill is mostly self-contained. The packet builder script only needs extra Python packages for specific input formats.

## Python packages

- `openpyxl`
  Required only when the input file is `.xlsx` or `.xlsm`.

## Install command

```bash
python3 -m pip install openpyxl
```

## Detection rule

- For `.csv` and `.json`, no extra Python package is required.
- For `.xlsx` and `.xlsm`, detect whether `openpyxl` is installed before reading the file.
- If the package is missing, stop and show the install command instead of failing with a vague import error.
