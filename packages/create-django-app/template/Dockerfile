FROM nixos/nix as builder

RUN mkdir /app
WORKDIR /app

COPY shell.nix shell.nix

RUN mkdir -p /output/store
RUN nix-env -f shell.nix -i -A buildInputs
RUN nix-env -f shell.nix -i -A dependencies --profile /output/profile
RUN cp -va $(nix-store -qR /output/profile) /output/store

COPY requirements.txt requirements.txt

RUN virtualenv .venv && .venv/bin/pip install -r requirements.txt

COPY package.json .
COPY yarn.lock .

RUN yarn

# RUN rm -rf node_modules/reactivated/*
# COPY node_modules/reactivated node_modules/reactivated

COPY manage.py .
COPY server server
COPY static static
COPY client client
COPY tsconfig.json .

RUN .venv/bin/python manage.py generate_client_assets
RUN .venv/bin/python manage.py build
RUN .venv/bin/python manage.py collectstatic --no-input
RUN rm collected/dist/*.map


FROM alpine

# Nix package is very heavy and includes the full DB.
RUN apk add postgresql-client

COPY --from=builder /output/store /nix/store
COPY --from=builder /output/profile/ /usr/local/

RUN mkdir /app
WORKDIR /app

ENV NODE_ENV production

COPY requirements.txt requirements.txt
RUN virtualenv .venv && .venv/bin/pip install -r requirements.txt

COPY manage.py .
COPY server server

RUN mkdir -p node_modules/.bin/
COPY --from=builder /app/node_modules/.bin/renderer.js node_modules/.bin/
COPY --from=builder /app/node_modules/.bin/renderer.js.map node_modules/.bin/
COPY --from=builder /app/collected collected

ENV PYTHONUNBUFFERED 1

CMD .venv/bin/gunicorn server.wsgi --forwarded-allow-ips="*" --bind 0.0.0.0:8080 --workers 1 --preload --timeout 90
