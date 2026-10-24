# FIT1056 Group 14 — FoodShare Tracker

FoodShare Tracker is a local-first Streamlit application designed to support food banks, charities, and community food-sharing organisations. The project models the day-to-day work of managing food inventory, client orders, donor contributions, staff workflows, and role-based access in a simple, maintainable Python application.

> Project status: This repository is a course-project implementation and a development prototype. It is intended for local experimentation and learning, not for production deployment or handling real sensitive client data.

## Overview

The application brings together four primary user types:

- Clients: browse food, place orders, review dietary requirements, and check order status.
- Donors: register donations, view contribution history, and review donor notifications.
- Food bank staff: manage pending orders, review client preferences, receive stock, and adjust inventory.
- Administrators: monitor stock, audit actions, manage users, and review reports.

The application is built in Python using Streamlit and stores its operational data in local JSON files under `assets/`. This keeps the project easy to run and test in a classroom environment while clearly highlighting the project’s implementation boundaries.

## Features

|Area | Current implementation | Limitations |
| --- | --- | --- |
|Accounts and roles | Registration, authentication, account management, and role-specific pages. | Account records are local JSON, not a production identity service. |
|Client orders | Food selection, dietary-constraint checks, order history, and order status. | Shared local files are not suitable for concurrent or multi-site use. |
|Inventory | Food catalogue, stock updates, thresholds, and expiry information. | Stock is stored locally and is not synchronised across installations. |
|Donations | Donor registration and donation history in the donor interface. | Donation workflows are local and should be checked against project requirements before operational use. |
|Notifications | In-app notification records for client orders ready for collection. | SMS is not configured. |
|Audit and reports | Audit events and administrative views are present. | Some report/export functions are placeholders; see the developer guide. |
|Cloud data governance | Not implemented. | Future work. |

## Project scope and boundaries

FoodShare Tracker focuses on a practical local prototype for a community food support workflow. It supports the main operational flow of ordering, inventory upkeep, and role-based coordination, but it does not implement production-level requirements such as:

- cloud storage or multi-user synchronization
- secure enterprise-grade authentication
- transactional database integrity
- external notification services such as SMS or email
- real production compliance or privacy governance

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for the software design notes and local data boundaries.

## Requirements

- Python 3.11 or newer
- Git

## Quick start

Clone the repository:

```bash
git clone https://github.com/jm0074-yuri/FIT1056-Group14-FoodShareTracker.git
cd FIT1056-Group14-FoodShareTracker
```

Create and activate a virtual environment.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

If you need the test tooling in the environment, install pytest too:

```bash
python -m pip install pytest
```

## Running the app

Run the Streamlit application from the repository root so that the local data paths resolve correctly.

Windows PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m streamlit run src/app/gui/main.py
```

macOS / Linux:

```bash
PYTHONPATH=src python -m streamlit run src/app/gui/main.py
```

Once the app starts, Streamlit will print a local URL in the terminal. Open that URL in a browser to use the interface. Available pages change based on whether the user is signed in and on their role.

## Data storage and local files

This project stores its working data in JSON files under `assets/`. The application does not currently use a database.

Important notes:

- `assets/account.json` stores account records and role-based metadata
- `assets/inventory.json` stores stock and inventory state
- `assets/orders/` stores daily order and status files
- `assets/admin_audit_log.json` stores administrator action records
- `FoodShareTracker.log` is the application log output
- `assets/backups/` contains backup copies created during startup

Because the app writes local files, use test data only and keep a backup before making changes that modify the stored JSON records.

## Repository structure

```text
src/
├── app/
│   ├── auth/           # Account loading and authentication flows
│   ├── core/           # Client, donor, and notification workflows
│   ├── exceptions/     # Application-specific exceptions
│   ├── food/           # Food, order, and inventory models
│   ├── gui/            # Streamlit pages and navigation
│   └── users/          # User roles and client constraints
├── util/               # Shared utilities and logging helpers
assets/                 # Local data files and image assets
docs/                   # Design and developer documentation
tests/                  # Automated tests
pytest.ini              # Test configuration for src on PYTHONPATH
requirements.txt        # Python project dependencies
README.md               # Project overview and usage guide
```

For role-specific pages, runtime responsibilities, and implementation boundaries, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Testing

The repository uses pytest. Run the full suite from the project root:

```bash
python -m pytest
```

`pytest.ini` configures the project so that `src` is available on the Python import path during tests.

## Manual UI smoke checks

After starting the app, verify the following with test data:

1. The home page loads and allows access to login and registration.
2. A user can register and sign in as a client, donor, staff member, or administrator.
3. The navigation updates correctly for the signed-in role.
4. Client order flows include available food and account for dietary restrictions.
5. Staff inventory and order screens respond correctly when inventory or order data changes.
6. Profile, help, and sign-out flows remain accessible.
7. Missing or invalid test data is surfaced rather than silently treated as success.

## Contributing

Contributions should remain aligned with the project’s intended scope and privacy-conscious purpose.

1. Create a branch for your change.
2. Keep modifications focused and avoid unrelated scope expansion.
3. Update relevant tests and documentation when changing behavior.
4. Run `python -m pytest` and perform a quick UI check for affected flows.
5. Submit a pull request with a summary of the change and any known limitations.

## Credits

This project was developed by FIT1056 Group 14.

Contributor list:
- Jia Ming
- Shunya Fuji
- Yan Low
- Chengzhang Su

## License

No software license is currently specified in this repository. Please contact the project maintainers before redistributing or reusing the code outside the course context.

