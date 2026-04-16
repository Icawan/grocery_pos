# Grocery POS (Django)

A complete Django-based grocery POS web system with:
- Barcode scanning via **USB barcode reader** (keyboard wedge)
- Barcode scanning via **camera** (using `zxing-js` in browser)
- Barcode scanning via **uploaded image file**
- Product catalog with price + inventory
- Cart / sale flow with tax and checkout
- Django Admin for management

## Quick start

### 1) Create virtual environment
```bash
python -m venv .venv
```

### 2) Activate virtual environment

**Windows (Command Prompt / `cmd.exe`):**
```bat
.venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux (bash/zsh):**
```bash
source .venv/bin/activate
```

### 3) Install and run
```bash
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
On POS page, open **Scan with camera or uploaded image**:
1. Click **Start camera scan**
2. Allow camera access
3. Point at product barcode
4. On successful read, the product is added to cart automatically

### 3) Upload barcode image
In the same scanner section:
1. Choose an image file that clearly shows the barcode
2. Wait for decode status
3. On successful read, the barcode is auto-submitted to cart

## Expected output when scanning works
- A green success message like `Added Milk 1L`
- Cart table updates with quantity and line total
- Subtotal/tax/total values increase
- Product stock decreases by 1 per successful scan

## If you see “No MultiFormat Readers were able to detect the code”
Try the following:
- Ensure the full barcode is visible and not cropped.
- Avoid blurry/out-of-focus images.
- Increase lighting and avoid glare on product packaging.
- Keep quiet zone (blank margin) visible around barcode edges.
- Test with another barcode type/product if available.
- If camera scan fails, try USB scanner input and vice versa.

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
