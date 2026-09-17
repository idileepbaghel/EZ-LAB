# Meridian HMS

A hospital management system built with **Flask + SQLite** on the backend and
server-rendered **HTML/CSS/JS** templates on the frontend. Covers the full
registration → lab → billing flow for a small clinic or lab front desk.

This is an original build (design, code, and data model) - it is not a copy of
any third-party product's templates or source.

## Features

- **Auth** — staff login (Flask-Login), session-protected routes
- **Registration** — patient intake, search, profile view/edit, MRN generation
- **Appointments** — scheduling by department/doctor, daily list, inline status updates (AJAX)
- **Laboratory** — test catalog, multi-test orders, sample collection → result entry workflow, auto status rollup
- **Billing** — itemized invoices with a dynamic line-item builder, partial/full payments, balance tracking
- **Dashboard** — live counts and recent activity across all modules

## Getting started

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 app.py
```

The app runs at `http://127.0.0.1:5000`. SQLite is used by default and a database
is created automatically at `instance/hms.db`, seeded with:

- **Login:** username `ultrademo`, password `Demo@2026`
- 3 sample patients
- An 8-test lab catalog (CBC, LFT, KFT, TSH, glucose, lipid profile, urine
  routine, COVID RT-PCR)

Delete `instance/hms.db` at any time to reset to a fresh seeded state.

### XAMPP MySQL

Start MySQL in the XAMPP Panel, create a database named `hms`, install the
requirements, and set these variables before starting the app:

```powershell
$env:DB_CONNECTION="mysql"
$env:DB_USER="root"
$env:DB_PASSWORD=""
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="3306"
$env:DB_NAME="hms"
python app.py
```

Alternatively, set `DATABASE_URL` to a complete SQLAlchemy connection URL.

## Project structure

```
hms_app/
├── app.py                     # application entry point
├── config.py                  # database and application configuration
├── requirements.txt
├── app/
│   ├── __init__.py             # application factory
│   ├── extensions.py           # shared Flask extensions
│   ├── main/
│   │   ├── __init__.py
│   │   └── routes.py           # models, auth, and main blueprint routes
│   ├── static/
│   │   ├── css/style.css      # design system (tokens, layout, components)
│   │   └── js/main.js          # invoice line items, lab checklist totals, AJAX status update
│   └── templates/
│       ├── base.html           # sidebar + topbar shell used by all authenticated pages
│       ├── login.html
│       ├── dashboard.html
│       ├── patients/  (list, form, view)
│       ├── appointments/  (list, form)
│       ├── lab/  (orders, order_form, report)
│       └── billing/  (invoices, invoice_form, invoice_view)
```

## Extending it

- Configure MySQL/Postgres through `DATABASE_URL` or the `DB_*` variables in `config.py`.
- Add role-based permissions by branching on `current_user.role` in routes.
- Add a printable invoice/report view by creating a `print.html` variant of
  `invoice_view.html` / `lab/report.html` with `@media print` CSS.
- Change the palette/type in `app/static/css/style.css` - all colors are CSS
  custom properties in `:root`.
