FROM nixos/nix:2.33.2 as builder

# Allow Nix to work under QEMU emulation (e.g. building linux/amd64 on arm64 for
# local `fly deploy --local-only` builds when remote builders are unavailable).
RUN echo 'filter-syscalls = false' >> /etc/nix/nix.conf

RUN mkdir /app
WORKDIR /app

COPY shell.nix shell.nix
COPY requirements.nix requirements.nix

RUN mkdir -p /output/store
RUN nix-env -f shell.nix -i -A buildDeps
RUN nix-env -f shell.nix -i -A dependencies --profile /output/profile
RUN cp -va $(nix-store -qR /output/profile) /output/store

COPY pyproject.toml uv.lock ./
COPY monorepo* monorepo/

ENV PATH="/app/.venv/bin:${PATH}"
# Resolve python3 to its absolute /nix/store path so the venv interpreter
# symlink survives into the final image. `python3` alone points at the builder's
# /root/.nix-profile, which is never copied to the runtime stage — only the store
# closure (/output/store -> /nix/store) is, so gunicorn's shebang would 127.
RUN uv venv .venv --python "$(readlink -f "$(command -v python3)")"
# Install from the lockfile. deploy.sh repoints reactivated at ./monorepo/python
# and refreshes uv.lock, so --frozen resolves reactivated from the local build.
RUN uv sync --frozen --no-dev --no-editable

COPY package.json .
COPY package-lock.json .

RUN npm install
RUN npm install ./monorepo/node.tgz
COPY complex-types.ts node_modules/react-markdown/lib/complex-types.ts

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


FROM alpine:3.23.3

# Nix package is very heavy and includes the full DB.
RUN apk add postgresql-client

COPY --from=builder /output/store /nix/store
COPY --from=builder /output/profile/ /usr/local/

RUN mkdir /app
WORKDIR /app

ENV NODE_ENV production

COPY --from=builder /app/.venv .venv
ENV PATH="/app/.venv/bin:${PATH}"

COPY manage.py .
COPY server server

RUN mkdir -p node_modules/_reactivated/
RUN mkdir -p static/
COPY --from=builder /app/node_modules/_reactivated/renderer.mjs node_modules/_reactivated/
COPY --from=builder /app/node_modules/_reactivated/renderer.mjs.map node_modules/_reactivated/
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
