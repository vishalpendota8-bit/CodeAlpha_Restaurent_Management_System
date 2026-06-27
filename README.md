# Restaurant Management System Backend

A complete, runnable backend for managing a restaurant: menu, tables,
reservations, inventory, orders, and reporting. Built with Django 5,
Django REST Framework, JWT authentication, and role-based access control.

---

## Features

- **JWT authentication** (register / login / refresh) with `SimpleJWT`.
- **Role-based permissions**: `Admin`, `Manager`, `Waiter`.
- **Menu**: categories and items with availability and pricing.
- **Tables**: capacity and live status (Available / Reserved / Occupied).
- **Reservations**: double-booking prevention and capacity validation.
- **Inventory**: ingredients, recipes, low-stock alerts, and audit logs.
- **Orders**: stock-aware order placement, automatic inventory deduction,
  tax/total calculation, completion, and cancellation with stock restore —
  all wrapped in **atomic transactions**.
- **Reports**: daily sales, monthly sales, top-selling items, low stock.
- **Pagination, search, filtering, and ordering** across list endpoints.
- **Django Admin** configured for every model.
- **Seed command** and a **unit test suite** (29 tests) covering core logic.

---

## Tech Stack

| Layer            | Choice                                  |
|------------------|-----------------------------------------|
| Framework        | Django 5                                |
| API              | Django REST Framework                   |
| Auth             | djangorestframework-simplejwt (JWT)     |
| Database         | PostgreSQL (production) / SQLite (dev)  |
| Filtering        | django-filter                           |

---

## Project Structure

```
restaurant_management/
├── config/                 # settings, root urls, wsgi/asgi
├── apps/
│   ├── accounts/           # custom User, roles, JWT auth, permissions, seed cmd
│   ├── menu/               # Category, MenuItem
│   ├── tables/             # RestaurantTable + /available
│   ├── reservations/       # Reservation + booking rules (services.py)
│   ├── inventory/          # Ingredient, Recipe, InventoryLog (services.py)
│   ├── orders/             # Order, OrderItem + order lifecycle (services.py)
│   └── reports/            # sales & stock reports (services.py)
├── requirements.txt
├── .env.example
├── manage.py
└── README.md
```

Business logic lives in each app's `services.py`; views stay thin.

---

## Setup

### 1. Clone & create a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env        # Windows: copy .env.example .env
```

The defaults run on **SQLite** with `USE_SQLITE=True`. To use PostgreSQL,
set `USE_SQLITE=False` and fill in the `POSTGRES_*` values in `.env`.

### 4. Migrate, seed, and run

```bash
python manage.py migrate
python manage.py seed_data          # demo users, menu, tables, inventory
python manage.py createsuperuser    # optional, for /admin
python manage.py runserver
```

The API is now available at `http://127.0.0.1:8000/` and the admin at
`http://127.0.0.1:8000/admin/`.

### Seeded logins

All seeded users share the password `password123`:

| Username  | Role    |
|-----------|---------|
| `admin`   | Admin   |
| `manager` | Manager |
| `waiter`  | Waiter  |

---

## Running Tests

```bash
python manage.py test
```

---

## Permissions Model

| Action                                   | Admin | Manager | Waiter |
|------------------------------------------|:-----:|:-------:|:------:|
| Read menu / tables / inventory           |  ✅   |   ✅    |   ✅   |
| Create/update menu, tables, ingredients  |  ✅   |   ✅    |   ❌   |
| Manage recipes, view inventory logs      |  ✅   |   ✅    |   ❌   |
| Create / cancel reservations             |  ✅   |   ✅    |   ✅   |
| Place / complete / cancel orders         |  ✅   |   ✅    |   ✅   |
| Sales & low-stock reports                |  ✅   |   ✅    |   ❌   |
| Top-items report                         |  ✅   |   ✅    |   ✅   |
| List all users (`/auth/users`)           |  ✅   |   ❌    |   ❌   |

---

## API Reference

Base URL: `http://127.0.0.1:8000`

All endpoints except `/auth/register` and `/auth/login` require a header:

```
Authorization: Bearer <access_token>
```

### Authentication

| Method | Path             | Description                |
|--------|------------------|----------------------------|
| POST   | `/auth/register` | Register a new user        |
| POST   | `/auth/login`    | Obtain access/refresh JWT  |
| POST   | `/auth/refresh`  | Refresh an access token    |
| GET    | `/auth/me`       | Current user profile       |
| GET    | `/auth/users`    | List users (Admin only)    |

### Resources (full CRUD)

| Resource     | Base path                  |
|--------------|----------------------------|
| Categories   | `/menu/categories/`        |
| Menu items   | `/menu/items/`             |
| Tables       | `/tables/`                 |
| Reservations | `/reservations/`           |
| Ingredients  | `/inventory/ingredients/`  |
| Recipes      | `/inventory/recipes/`      |
| Orders       | `/orders/` (create + read) |

### Extra endpoints

| Method | Path                                   | Description                          |
|--------|----------------------------------------|--------------------------------------|
| GET    | `/tables/available/`                   | Available tables (`?guests=N`)       |
| GET    | `/reservations/available-tables/`      | Free tables (`?time=ISO&guests=N`)   |
| POST   | `/reservations/{id}/cancel/`           | Cancel a reservation                 |
| POST   | `/orders/{id}/complete/`               | Complete & settle an order           |
| POST   | `/orders/{id}/cancel/`                 | Cancel an order, restore stock       |
| GET    | `/inventory/ingredients/low-stock/`    | Low-stock ingredients                |
| POST   | `/inventory/ingredients/{id}/restock/` | Add stock (Admin/Manager)            |
| GET    | `/inventory/logs/`                     | Inventory audit logs                 |
| GET    | `/reports/daily`                       | Daily sales (`?date=YYYY-MM-DD`)     |
| GET    | `/reports/monthly`                     | Monthly sales (`?year=&month=`)      |
| GET    | `/reports/top-items`                   | Top-selling items (`?limit=N`)       |
| GET    | `/reports/low-stock`                   | Low-stock report                     |

### Query parameters

- **Pagination**: `?page=2` (10 items per page).
- **Search**: `?search=burger` (where supported).
- **Filter**: e.g. `/menu/items/?category=1&available=true`.
- **Ordering**: e.g. `/menu/items/?ordering=-price`.

---

## Sample Requests

### Register

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
        "username": "newwaiter",
        "email": "w@example.com",
        "password": "StrongPass123",
        "password2": "StrongPass123",
        "role": "WAITER"
      }'
```

### Login

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "waiter", "password": "password123"}'
```

Response:

```json
{
  "refresh": "<refresh_token>",
  "access": "<access_token>",
  "user": { "id": 3, "username": "waiter", "role": "WAITER", "...": "..." }
}
```

### Create a menu item (Admin/Manager)

```bash
curl -X POST http://127.0.0.1:8000/menu/items/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"category": 2, "name": "BBQ Burger", "price": "13.50", "available": true}'
```

### List available tables for 4 guests

```bash
curl "http://127.0.0.1:8000/tables/available/?guests=4" \
  -H "Authorization: Bearer <access_token>"
```

### Create a reservation

```bash
curl -X POST http://127.0.0.1:8000/reservations/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
        "customer_name": "Jane Doe",
        "phone": "555-0101",
        "table": 3,
        "reservation_time": "2026-07-01T19:00:00Z",
        "guests": 4
      }'
```

### Place an order

```bash
curl -X POST http://127.0.0.1:8000/orders/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
        "table": 3,
        "items": [
          {"menu_item": 3, "quantity": 2},
          {"menu_item": 6, "quantity": 1}
        ]
      }'
```

The server validates availability, checks ingredient stock, captures unit
prices, calculates `subtotal`/`tax`/`total`, deducts inventory, and marks the
table `OCCUPIED` — all in one atomic transaction. If stock is insufficient the
order is rejected with HTTP `409` and a `shortages` list.

### Complete / cancel an order

```bash
curl -X POST http://127.0.0.1:8000/orders/1/complete/ \
  -H "Authorization: Bearer <access_token>"

curl -X POST http://127.0.0.1:8000/orders/1/cancel/ \
  -H "Authorization: Bearer <access_token>"
```

Cancelling restores the deducted inventory and frees the table.

### Reports

```bash
curl "http://127.0.0.1:8000/reports/daily?date=2026-06-26" \
  -H "Authorization: Bearer <access_token>"

curl "http://127.0.0.1:8000/reports/monthly?year=2026&month=6" \
  -H "Authorization: Bearer <access_token>"

curl "http://127.0.0.1:8000/reports/top-items?limit=5" \
  -H "Authorization: Bearer <access_token>"
```

---

## HTTP Status Codes

| Code | Meaning                                              |
|------|------------------------------------------------------|
| 200  | OK                                                   |
| 201  | Created                                              |
| 400  | Validation error (bad input, business rule failure)  |
| 401  | Missing/invalid token                                |
| 403  | Authenticated but role not permitted                 |
| 404  | Not found                                            |
| 409  | Conflict — insufficient ingredient stock for an order|

---

## Notes

- The configured tax rate is read from `TAX_RATE` in `.env` (default `0.10`).
- Reservations treat a booking as holding a table for a 90-minute window
  (`Reservation.SLOT_DURATION_MINUTES`) when checking for conflicts.
- Orders are intentionally immutable after creation; use the
  `complete`/`cancel` actions rather than `PUT`/`PATCH`/`DELETE` so inventory
  and table state stay consistent.
