# Developer guide

This guide describes the current code layout and local data flows. It is an
orientation document, not a production deployment or data-security guide.

## Application entry point

Run the Streamlit application from the repository root:

```bash
PYTHONPATH=src python -m streamlit run src/app/gui/main.py
```

`src/app/gui/main.py` initializes shared session state, account management,
logging, and a startup data backup. It builds the navigation from the signed-in
user's role. Streamlit reruns pages within a session, so session-scoped objects
such as the current account and client tracker live in `st.session_state`.

## Code map

| Directory | Responsibility | Examples |
| --- | --- | --- |
| `src/app/auth/` | Account loading, account mutations, and authentication. | `account_manager.py` |
| `src/app/core/` | Client order workflow, donor tracker, and client notifications. | `food_tracker_client.py`, `notification.py` |
| `src/app/exceptions/` | Application exceptions used to report missing records. | `NotFoundException.py` |
| `src/app/food/` | Food and order models plus inventory persistence and stock operations. | `food_item.py`, `food_order.py`, `inventory.py` |
| `src/app/gui/` | Streamlit startup, shared UI, and role-specific pages. | `main.py`, `shared/`, `client/`, `staff/`, `admin/` |
| `src/app/users/` | User-role models and client dietary constraints. | `user.py`, `client.py`, `constraint.py` |
| `src/util/` | Logging, audit helpers, and backup utilities. | `admin_utils.py` |
| `tests/` | Unit and workflow tests, including file-backed tests using temporary paths. | `test_client.py`, `test_stock_management.py` |

The primary navigation is assembled in `src/app/gui/main.py`:

| Role | Page modules |
| --- | --- |
| Signed out | `home.py`, `login.py`, `register.py`, `helps.py` |
| Client | `client/client_dashboard.py`, `client/client_order.py`, `client/display_order.py`, `client/ready_for_collection.py`, `client/client_order_history.py`, shared profile |
| Donor | `donor/donor_dashboard.py`, shared profile |
| Food Bank Staff | `staff/staff_dashboard.py`, `staff/pending_orders.py`, `staff/client_preferences.py`, `staff/order_details.py`, `staff/receive_stock.py`, `staff/food_catalogue.py`, `staff/adjust_stock.py`, `bank/inventory_management.py`, shared profile |
| Admin | `admin/admin_dashboard.py`, `admin/user_management.py`, `admin/stock_monitor.py`, `admin/audit_log.py`, `admin/report_export.py`, shared profile |

## Local data files

The application currently uses JSON files under `assets/`; there is no SQL or
other database layer. Paths are generally resolved relative to the repository
root or the process working directory, so start the application from the
repository root.

| File or directory | Purpose |
| --- | --- |
| `assets/account.json` | Accounts grouped by role. Account records include profile and role-specific fields, such as client order history or donor donation history. Passwords use salted PBKDF2 hashes; the account manager also migrates legacy plaintext passwords when loading accounts. |
| `assets/inventory.json` | Inventory items, the next food ID, and optional minimum-stock thresholds. |
| `assets/orders/YYYY-MM-DD_orders.json` | Shared daily order records grouped by client name. |
| `assets/orders/order_status.json` | Order status lookup keyed by each order's file/client/item key. |
| `assets/orders/client_notifications.json` | In-app notifications for client orders. SMS is not configured. |
| `assets/donor_notifications.json` | Donor dashboard notifications. |
| `assets/admin_audit_log.json` | Persistent administrator action records. |
| `FoodShareTracker.log` | Application log output created by the logger. |
| `assets/backups/` | Destination for startup backups of inventory and the current day's order file. |

These files are mutable runtime data, not a database with transactions or
multi-process coordination. Back up local data before testing workflows that
write to it. Use test accounts and test records; do not put real client
information or production credentials in this course project.

The startup backup helper attempts to copy both the inventory file and the
current day's order file. Check the application log if either backup fails.

## Typical order flow

1. A client selects available food through the client ordering pages. The
   `FoodShareTracker` in `app/core/food_tracker_client.py` coordinates the
   current order and checks hard dietary constraints when the order is
   finalized.
2. The client accepts the order. The shared order is appended to that day's
   `assets/orders/YYYY-MM-DD_orders.json` file, and the client's order history
   is updated through the account manager.
3. Staff read shared daily files in `app/gui/staff/pending_orders.py` and update
   status through `app/gui/staff/order_status.py`.
4. Setting an order to `Ready for Collection` creates an in-app client
   notification. Clients see ready orders and notifications on the collection
   page.

Inventory changes are handled by `app/food/inventory.py` and the staff or
administrator pages that use it. The donor dashboard stores donation records
in the donor account record and writes donor notifications separately.

## Tests and local checks

Install the application dependencies and pytest in the active environment:

```bash
python -m pip install -r requirements.txt
python -m pip install pytest
```

Run the complete test suite from the repository root:

```bash
python -m pytest
```

`pytest.ini` adds `src` to the import path. Prefer temporary files and pytest's
`tmp_path` fixture for new tests so they cannot modify the tracked data in
`assets/`.

For a UI smoke check, start Streamlit using the command at the top of this
guide and verify the sign-in, role navigation, and the page affected by a
change. Use test accounts and restore test data from a backup when needed.

## Change guidelines

- Keep UI rendering in `app/gui/`, reusable workflow behavior in `app/core/`,
  and domain data behavior in `app/food/` or `app/users/`.
- Preserve role checks and existing session-state keys when changing page
  navigation or authentication.
- Keep persisted JSON shapes compatible with existing data and tests. When
  changing a shape, update readers, writers, tests, and this guide together.
- Surface invalid or unavailable data to the caller; do not silently replace a
  malformed file with an empty successful result.
- Add or update tests for changed behavior, run the full suite, and review
  `git status` before staging so local data changes are not included by
  accident.

## Known implementation boundaries

- The local JSON storage does not provide database transactions, cross-user
  coordination, or cloud synchronisation.
- Notifications are in-app only; external SMS delivery is not connected.
- Admin reports export current inventory, order demand, or donation summaries
  to CSV or JSON. Inventory import merges validated inventory JSON, and backup
  actions cover local data; these workflows are limited to the local JSON
  storage model and are not a production reporting or backup service.
- Audit logs and local account storage are development aids, not a substitute
  for a reviewed production security and privacy design.
