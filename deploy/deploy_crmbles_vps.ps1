param(
    [string]$HostAlias = "crmbles-vps",
    [string]$Branch = "main",
    [string]$ExpectedVersion = ""
)

$ErrorActionPreference = "Stop"

$remoteScript = @"
set -euo pipefail

BRANCH="`${BRANCH:?}"
EXPECTED_VERSION="`${EXPECTED_VERSION:-}"
APP_DIR=/var/www/crmbles/current
VENV_DIR=/var/www/crmbles/venv
PY=`$VENV_DIR/bin/python
PIP=`$VENV_DIR/bin/pip
SERVICE=crmbles
DOMAIN=crmbles.skulkabout.com

echo "==> Fetching latest `$BRANCH"
sudo -u crmbles git -C "`$APP_DIR" fetch origin "`$BRANCH"
sudo -u crmbles git -C "`$APP_DIR" checkout "`$BRANCH"
sudo -u crmbles git -C "`$APP_DIR" pull --ff-only origin "`$BRANCH"

echo "==> Installing dependencies"
"`$PIP" install -r "`$APP_DIR/requirements.txt"

run_manage() {
  systemd-run --quiet --wait --collect --pipe \
    --uid=crmbles \
    --gid=www-data \
    --property=WorkingDirectory="`$APP_DIR" \
    --property=EnvironmentFile=/etc/crmbles.env \
    "`$PY" manage.py "`$@"
}

echo "==> Running migrations"
run_manage migrate --noinput

echo "==> Collecting static files"
run_manage collectstatic --noinput

echo "==> Running Django checks"
run_manage check

echo "==> Restarting CRMbles"
systemctl restart "`$SERVICE"
systemctl reload nginx

echo "==> Verifying service"
systemctl is-active --quiet "`$SERVICE"
for attempt in {1..30}; do
  if curl -fsSI "https://`$DOMAIN/faq/" >/tmp/crmbles-deploy-headers.txt 2>/dev/null; then
    head -n 12 /tmp/crmbles-deploy-headers.txt
    break
  fi
  if [[ "`$attempt" -eq 30 ]]; then
    echo "FAQ health check did not recover after restart." >&2
    exit 1
  fi
  sleep 1
done

if [[ -n "`$EXPECTED_VERSION" ]]; then
  echo "==> Verifying versioned stylesheet v`$EXPECTED_VERSION"
  for attempt in {1..30}; do
    if curl -fsSL "https://`$DOMAIN/faq/" 2>/dev/null | grep -q "style.css?v=`$EXPECTED_VERSION"; then
      break
    fi
    if [[ "`$attempt" -eq 30 ]]; then
      echo "Versioned stylesheet v`$EXPECTED_VERSION was not found after restart." >&2
      exit 1
    fi
    sleep 1
  done
fi

echo "==> Deployed commit"
commit=`$(sudo -u crmbles git -C "`$APP_DIR" rev-parse --short HEAD)
subject=`$(sudo -u crmbles git -C "`$APP_DIR" show -s --format=%s HEAD)
echo "`$commit `$subject"
"@

$remoteScript | ssh $HostAlias "BRANCH='$Branch' EXPECTED_VERSION='$ExpectedVersion' bash -s"
