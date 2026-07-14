# CRMbles VPS Deployment

Target host: `crmbles.skulkabout.com`

This app is a standard Django WSGI deployment behind Nginx and Gunicorn. It should run as its own Linux user and service so it does not interfere with the other VPS apps.

## Planned VPS Layout

```text
/var/www/crmbles/current
/var/www/crmbles/shared/media
/var/www/crmbles/shared/db.sqlite3
/var/www/crmbles/venv
/etc/crmbles.env
/etc/systemd/system/crmbles.service
/etc/nginx/sites-available/crmbles
```

## Deploy Steps

If you have root shell access on the VPS, the repeatable install path is:

```bash
curl -fsSL https://raw.githubusercontent.com/Kurisk/crmbles/main/deploy/install_crmbles_vps.sh -o /tmp/install_crmbles_vps.sh
bash /tmp/install_crmbles_vps.sh
```

Manual equivalent:

1. Create the `crmbles` system user and `/var/www/crmbles` directories.
2. Clone `https://github.com/Kurisk/crmbles.git` into `/var/www/crmbles/current`.
3. Create `/etc/crmbles.env` from `deploy/crmbles.env.example` with a real `SECRET_KEY`.
4. Install dependencies into `/var/www/crmbles/venv`.
5. Run:

```bash
/var/www/crmbles/venv/bin/python manage.py migrate
/var/www/crmbles/venv/bin/python manage.py collectstatic --noinput
/var/www/crmbles/venv/bin/python manage.py check
```

6. Install `deploy/crmbles.service` as `/etc/systemd/system/crmbles.service`.
7. Install `deploy/crmbles.nginx` as `/etc/nginx/sites-available/crmbles` and symlink it into `sites-enabled`.
8. Run `nginx -t`, restart Nginx, enable/start `crmbles.service`, then issue TLS with Certbot.

## Smoke Checks

```bash
systemctl status crmbles --no-pager
curl -I http://127.0.0.1:8031/
curl -I https://crmbles.skulkabout.com/
```
