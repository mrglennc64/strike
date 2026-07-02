#!/usr/bin/env bash
# One-shot deploy for strike.perfecthold.online on a fresh Ubuntu/Debian VPS.
#
#   ssh root@187.77.111.16
#   curl -fsSL https://raw.githubusercontent.com/mrglennc64/strike/main/deploy/bootstrap.sh | ODDS_KEY=YOURKEY bash
#
# ODDS_KEY  (optional) your the-odds-api.com key; if omitted a placeholder is written
#           to /etc/mlb-edge.env and you edit it before the API will return odds.
# LE_EMAIL  (optional) email for Let's Encrypt; if set, TLS is issued automatically.
set -euo pipefail

DOMAIN="strike.perfecthold.online"
APP=/opt/strike
REPO="https://github.com/mrglennc64/strike.git"

echo "==> Installing system packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y git curl nginx python3 python3-venv python3-pip ca-certificates
# Node 20 (vite needs >=18) via NodeSource
if ! command -v node >/dev/null 2>&1 || [ "$(node -v | cut -dv -f2 | cut -d. -f1)" -lt 18 ]; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi

echo "==> Fetching code into $APP"
if [ -d "$APP/.git" ]; then
  git -C "$APP" pull --ff-only
else
  git clone "$REPO" "$APP"
fi
mkdir -p "$APP/data"

echo "==> Backend (venv + deps)"
python3 -m venv "$APP/backend/.venv"
"$APP/backend/.venv/bin/pip" install --quiet --upgrade pip
"$APP/backend/.venv/bin/pip" install --quiet -r "$APP/backend/requirements.txt"

echo "==> Secrets at /etc/mlb-edge.env"
if [ ! -f /etc/mlb-edge.env ]; then
  cat > /etc/mlb-edge.env <<EOF
ODDS_PROVIDER=theoddsapi
ODDS_API_KEY_THEODDSAPI=${ODDS_KEY:-REPLACE_WITH_YOUR_THEODDSAPI_KEY}
ODDS_API_KEY_IO=
MIN_EDGE=0.03
KELLY_FRACTION=0.25
KELLY_CAP=0.05
DEVIG_METHOD=shin
EOF
  chmod 600 /etc/mlb-edge.env
  echo "    wrote /etc/mlb-edge.env (chmod 600)"
else
  echo "    /etc/mlb-edge.env exists, leaving it untouched"
fi

echo "==> Frontend build"
( cd "$APP/frontend" && npm ci && npm run build )

echo "==> Web root (nginx serves /var/www/strike, decoupled from the build dir)"
mkdir -p /var/www/strike
cp -r "$APP/frontend/dist/." /var/www/strike/

echo "==> systemd service (strike-backend.service — the ONE canonical unit)"
cp "$APP/deploy/strike-backend.service" /etc/systemd/system/strike-backend.service
systemctl daemon-reload
systemctl enable strike-backend >/dev/null 2>&1 || true
systemctl restart strike-backend

echo "==> nginx site (additive: does NOT touch other vhosts)"
# Guarded like the env file: certbot rewrites this file in place to add TLS,
# so re-running bootstrap must never clobber a certbot-managed live config.
if [ ! -f /etc/nginx/sites-available/strike.perfecthold.online ]; then
  cp "$APP/deploy/nginx-strike.conf" /etc/nginx/sites-available/strike.perfecthold.online
  ln -sf /etc/nginx/sites-available/strike.perfecthold.online \
         /etc/nginx/sites-enabled/strike.perfecthold.online
else
  echo "    site config exists (possibly certbot-managed), leaving it untouched"
  echo "    repo copy for manual diff: $APP/deploy/nginx-strike.conf"
fi
# NOTE: we intentionally do NOT remove the 'default' site — this box may host other
# sites. The strike vhost is matched by server_name, so it coexists safely.
nginx -t
systemctl reload nginx

echo "==> health check"
sleep 2
curl -fsS http://127.0.0.1:8077/health && echo

if [ -n "${LE_EMAIL:-}" ]; then
  echo "==> TLS via Let's Encrypt"
  apt-get install -y certbot python3-certbot-nginx
  certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$LE_EMAIL" --redirect
fi

echo
echo "Done. Visit: http://$DOMAIN  (the engine is served at /)"
if [ -z "${ODDS_KEY:-}" ] && grep -q REPLACE_WITH /etc/mlb-edge.env; then
  echo "NOTE: edit /etc/mlb-edge.env to add your the-odds-api key, then:  systemctl restart strike-backend"
fi
if [ -z "${LE_EMAIL:-}" ]; then
  echo "For HTTPS:  apt-get install -y certbot python3-certbot-nginx && certbot --nginx -d $DOMAIN"
fi
