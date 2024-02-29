FROM nixos/nix as builder

RUN mkdir /app
WORKDIR /app

COPY shell.nix shell.nix
COPY requirements.nix requirements.nix

RUN mkdir -p /output/store
RUN nix-env -f shell.nix -i -A buildInputs
RUN nix-env -f shell.nix -i -A dependencies --profile /output/profile
RUN cp -va $(nix-store -qR /output/profile) /output/store

COPY requirements.txt requirements.txt

ENV PATH="/app/.venv/bin:${PATH}"
RUN python -m venv .venv && pip install wheel && pip install --no-cache-dir -r requirements.txt

COPY package.json .
COPY package-lock.json .

RUN npm install

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
ENV PATH="/app/.venv/bin:${PATH}"
RUN python -m venv .venv && pip install wheel && pip install --no-cache-dir -r requirements.txt

COPY manage.py .
COPY server server

RUN mkdir -p node_modules/_reactivated/
RUN mkdir -p static/
COPY --from=builder /app/node_modules/_reactivated/renderer.js node_modules/_reactivated/
COPY --from=builder /app/node_modules/_reactivated/renderer.js.map node_modules/_reactivated/
COPY --from=builder /app/collected collected

ENV PYTHONUNBUFFERED 1
ENV PATH="/app/.venv/bin:$PATH"
ENV ENVIRONMENT=production
RUN rm server/settings/__init__.py && echo 'export DJANGO_SETTINGS_MODULE=server.settings.$ENVIRONMENT' > /etc/profile
ENTRYPOINT ["/bin/sh", "-lc"]
# SSH commands are weird with fly for now, so we use this dirty script at the root level.
RUN echo "source /etc/profile; cd /app; python manage.py migrate" > /migrate.sh && chmod +x /migrate.sh
RUN echo "source /etc/profile; cd /app; python manage.py dumpdata --indent=4" > /backup.sh && chmod +x /backup.sh

CMD ["gunicorn server.wsgi --forwarded-allow-ips='*' --bind 0.0.0.0:8080 --workers 1 --preload --timeout 90"]
