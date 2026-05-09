# eCommerce Web Application

A Django-based eCommerce application built as part of the HyperionDev AI Engineering programme (Level 2, Task 13). Users can register as either vendors or buyers — vendors create stores and sell products, while buyers browse, add to cart, and checkout.

## Features

- **Authentication and authorisation** — registration with role selection, login, logout, password reset via tokenised email links
- **Vendor side** — full CRUD on stores and products
- **Buyer side** — browse products, shopping cart using Django sessions, checkout with email invoice
- **Reviews** — verified (purchased) and unverified review system
- **Permissions** — Django groups (Vendors, Buyers) restrict access to role-specific views
- **Password recovery** — secure tokenised reset links that expire after 5 minutes

## Tech stack

- Python 3.x
- Django 6.0.5
- SQLite (development database)
- Bootstrap 5 (frontend)

## Setup

### 1. Create and activate a virtual environment

```powershell
python -m venv venv
venv\Scripts\activate
```

On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Run migrations

```powershell
python manage.py migrate
```

### 4. Create the user groups

```powershell
python manage.py setup_groups
```

This creates the `Vendors` and `Buyers` groups with the correct permissions.

### 5. Create a superuser (optional, for admin access)

```powershell
python manage.py createsuperuser
```

### 6. Run the server

```powershell
python manage.py runserver
```

The site will be available at http://127.0.0.1:8000/

## Email backend

The project uses Django's **console email backend** for development. When the app sends an email (password reset, order invoice), the email contents print directly to the terminal where `runserver` is running. To use real email in production, change `EMAIL_BACKEND` in `settings.py` to the SMTP backend.

## Usage

1. **Register a vendor** — visit /register/, choose Vendor, log in, create a store via the Dashboard, add products.
2. **Register a buyer** — visit /register/, choose Buyer, log in, browse products, add to cart, checkout. Watch the terminal for the invoice email.
3. **Leave a review** — as a buyer, visit any product page and click "Leave a Review". Reviews are auto-flagged "Verified" if you've purchased the product.
4. **Forgot password** — click "Forgot your password?" on the login page, enter your email, copy the reset link from the terminal, and set a new password.

## Project structure
```
ecommerce_project/
├── ecommerce_project/      # Project config
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── store/                  # Main app
│   ├── management/
│   │   └── commands/
│   │       └── setup_groups.py
│   ├── migrations/
│   ├── templates/store/    # HTML templates
│   ├── models.py           # 7 models: Profile, Store, Product, Order, OrderItem, Review, ResetToken
│   ├── views.py            # All view functions
│   ├── urls.py             # App URL routing
│   └── admin.py
├── templates/              # (project-level templates folder)
├── Planning/               # Planning documents
├── manage.py
├── requirements.txt
└── README.md
```

## Models overview
```
| Model | Purpose |
|-------|---------|
| Profile | Extends User with a role (vendor or buyer) |
| Store | A vendor's shop |
| Product | An item for sale, belongs to a store |
| Order | A buyer's checkout record |
| OrderItem | Individual product line in an order, with locked-in price |
| Review | Buyer's review with verified/unverified flag |
| ResetToken | Hashed password reset tokens with expiry |
```

## Database
The project uses SQLite for development. The brief mentions MariaDB — to swap, update the `DATABASES` setting in `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'your_db_name',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '',
    }
}
```

Then run `python manage.py migrate` against the new database.