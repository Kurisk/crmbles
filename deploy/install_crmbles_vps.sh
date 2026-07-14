#!/usr/bin/env bash
set -euo pipefail

APP_NAME="crmbles"
APP_USER="crmbles"
APP_ROOT="/var/www/${APP_NAME}"
APP_DIR="${APP_ROOT}/current"
SHARED_DIR="${APP_ROOT}/shared"
VENV_DIR="${APP_ROOT}/venv"
ENV_FILE="/etc/${APP_NAME}.env"
REPO_URL="https://github.com/Kurisk/crmbles.git"
DOMAIN="crmbles.skulkabout.com"
PORT="8031"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script as root." >&2
  exit 1
fi

apt-get update
apt-get install -y git python3-venv python3-pip nginx certbot python3-certbot-nginx

if ! id "${APP_USER}" >/dev/null 2>&1; then
  useradd --system --home "${APP_ROOT}" --shell /usr/sbin/nologin "${APP_USER}"
fi

mkdir -p "${SHARED_DIR}/media"
chown -R "${APP_USER}:www-data" "${APP_ROOT}"

if [[ ! -d "${APP_DIR}/.git" ]]; then
  rm -rf "${APP_DIR}"
  sudo -u "${APP_USER}" git clone "${REPO_URL}" "${APP_DIR}"
else
  sudo -u "${APP_USER}" git -C "${APP_DIR}" fetch origin main
  sudo -u "${APP_USER}" git -C "${APP_DIR}" checkout main
  sudo -u "${APP_USER}" git -C "${APP_DIR}" reset --hard origin/main
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  python3 -m venv "${VENV_DIR}"
fi

"${VENV_DIR}/bin/pip" install --upgrade pip
"${VENV_DIR}/bin/pip" install -r "${APP_DIR}/requirements.txt"

if [[ ! -f "${ENV_FILE}" ]]; then
  SECRET_KEY="$("${VENV_DIR}/bin/python" - <<'PY'
import secrets
print(secrets.token_urlsafe(50))
PY
)"
  cat > "${ENV_FILE}" <<EOF
SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=${DOMAIN}
CSRF_TRUSTED_ORIGINS=https://${DOMAIN}
DATABASE_URL=sqlite:////var/www/crmbles/shared/db.sqlite3
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
EOF
  chmod 640 "${ENV_FILE}"
  chown root:www-data "${ENV_FILE}"
fi

while IFS='=' read -r key value; do
  [[ -z "${key}" || "${key}" =~ ^[[:space:]]*# ]] && continue
  if [[ "${key}" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    export "${key}=${value}"
  fi
done < "${ENV_FILE}"

sudo -u "${APP_USER}" "${VENV_DIR}/bin/python" "${APP_DIR}/manage.py" migrate --noinput
sudo -u "${APP_USER}" "${VENV_DIR}/bin/python" "${APP_DIR}/manage.py" collectstatic --noinput
sudo -u "${APP_USER}" "${VENV_DIR}/bin/python" "${APP_DIR}/manage.py" check

install -m 0644 "${APP_DIR}/deploy/${APP_NAME}.service" "/etc/systemd/system/${APP_NAME}.service"
install -m 0644 "${APP_DIR}/deploy/${APP_NAME}.nginx" "/etc/nginx/sites-available/${APP_NAME}"
ln -sfn "/etc/nginx/sites-available/${APP_NAME}" "/etc/nginx/sites-enabled/${APP_NAME}"

systemctl daemon-reload
systemctl enable --now "${APP_NAME}"
nginx -t
systemctl reload nginx

if ! certbot certificates 2>/dev/null | grep -q "Domains: .*${DOMAIN}"; then
  certbot --nginx -d "${DOMAIN}"
fi

systemctl restart "${APP_NAME}"
curl -I "https://${DOMAIN}/"
