# Grocery POS (Django)

A complete Django-based grocery POS web system with:
- Barcode scanning via **USB barcode reader** (keyboard wedge)
- Barcode scanning via **camera** (using `html5-qrcode` in browser)
- Product catalog with price + inventory
- Cart / sale flow with tax and checkout
- Django Admin for management

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open:
- POS: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`

## Barcode scanning support

### 1) USB barcode reader
Most scanners act like a keyboard. In the POS page:
1. Focus barcode input
2. Scan barcode
3. Scanner types barcode + Enter (auto submit)

### 2) Camera scanner
On POS page, open **Scan with camera** section:
1. Allow camera access
2. Point at product barcode
3. Detected code is submitted automatically

## Seed demo products
Use **Seed data** in the top menu to create sample products.

## Core URLs
- `/` POS checkout screen
- `/products/` Product list
- `/products/add/` Quick add product form endpoint
- `/scan/` Barcode scan endpoint
- `/checkout/` Finalize sale
- `/clear/` Clear current cart
- `/seed/` Add sample data

## Notes
- Database is SQLite by default.
- Tax is set to 7% in model logic (`Sale.TAX_RATE`).
- Stock is decremented each time a product is scanned.
