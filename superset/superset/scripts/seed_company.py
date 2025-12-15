"""
This script is intended to be mounted into the Superset container (./superset)
and executed inside the running Superset container so it has access to the
application context and security manager.

Usage (from repo root):
  docker-compose exec superset python /app/pythonpath/scripts/seed_company8.py

What it does:
  - Create department roles listed in `DEPARTMENTS` if they do not exist.
  - Create a few helper roles (Viewer, Analyst).
  - Prints next steps and sample RLS/CLS SQL filters and curl templates.

Note: Creating RLS and Column-level Security programmatically depends on
Superset's internal models/API version; this script intentionally avoids
making DB schema assumptions and instead provides safe, copy-paste curl
examples for creating RLS/CLS via the Superset REST API (replace tokens).
"""

import sys

DEPARTMENTS = [
    'Finance',
    'Sales',
    'HR',
    'Engineering',
]

HELPER_ROLES = ['Viewer', 'Analyst']


def create_roles(app):
    sm = app.appbuilder.sm
    created = []
    for r in HELPER_ROLES + [f'Dept_{d}' for d in DEPARTMENTS]:
        try:
            role = sm.find_role(r)
            if not role:
                sm.add_role(r)
                created.append(r)
        except Exception as e:
            print(f'Warning: cannot create/find role {r}: {e}')
    return created


def main():
    try:
        # Lazy import of Superset app creation
        from superset.app import create_app
        app = create_app()
    except Exception as e:
        print('Error: cannot import/create Superset app. Run this script inside the Superset container where the app and dependencies are available.')
        print('Exception:', e)
        sys.exit(1)

    with app.app_context():
        created = create_roles(app)
        if created:
            print('Created roles:', ', '.join(created))
        else:
            print('No new roles were created (they may already exist).')

        print('\nNext steps:')
        print('1) Create Row Level Security (RLS) rules via Superset UI or API. Example SQL filter for dataset with `department` column:')
        print("\n   department = '{{ current_user.department }}'\n")

        print('2) Example explicit RLS for Dept_Finance (no Jinja):')
        print("\n   department = 'Finance'\n")

        print('3) Column-level Security: set whitelist/blacklist of columns for role. Example to hide `salary` for Dept_Sales:\n')
        print('  - Use Superset UI: Security -> List Column Level Security -> Add')
        print('\n4) If you want to automate RLS/CLS creation via API, you can use the Superset REST API.\n')
        print('   Example curl (replace TOKEN & dataset/role ids):')
        print("\n   curl -X POST 'http://localhost:8088/api/v1/security/rowlevel' \\\n     -H 'Authorization: Bearer <TOKEN>' \\\n     -H 'Content-Type: application/json' \\\n     -d '{"name": "RLS_dept_filter", "dataset": <DATASET_ID>, "clause": "department = \'{{ current_user.department }}\'", "roles": [<ROLE_ID>]}'")

        print('\nRemember: test thoroughly in staging. If you want, I can extend this script to call the Superset REST API directly (needs an API token) to create RLS/CLS programmatically.')


if __name__ == '__main__':
    main()
