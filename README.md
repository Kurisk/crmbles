# CRMbles

CRMbles is a modular Django CRM workspace for projects, documents, vendors, account access, and finance workflows.

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy your environment values into a local `.env` file.
4. Run migrations and checks:

```powershell
python manage.py migrate
python manage.py check
```

The future public domain target is `crmbles.com`.

## Production Host

The staging/live VPS target for this private deployment is:

```text
https://crmbles.skulkabout.com
```

Use the files in `deploy/` as the starting point for the VPS service, Nginx site, and environment values.
