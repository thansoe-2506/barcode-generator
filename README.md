# Barcode Generator

This repository contains a small Python script that reads product data from a CSV file and generates barcode images. The images are combined into a table‑style PDF for printing.

## Requirements

- Python 3.8+
- `pandas`
- `pillow`
- `python-barcode`
- `fpdf`

All required fonts are included in the `fonts/` directory.

Install dependencies with:

```bash
pip install pandas pillow python-barcode fpdf
```

## Usage

1. Place your CSV data in `source/items2.csv`. Each row should contain:
   `item_code, barcode_number, item_name`.
2. Run the script:

```bash
python3 main.py
```

Barcode images will be created in `barcodes/` and a combined `barcodes_table_format.pdf` will be produced in the repository root.

