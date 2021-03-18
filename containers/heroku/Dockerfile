FROM nixos/nix as builder

RUN mkdir /app
WORKDIR /app

COPY nix nix
COPY shell.nix shell.nix

RUN mkdir -p /output/store
RUN nix-env -f shell.nix -i -A buildInputs
RUN nix-env -f shell.nix -i -A dependencies --profile /output/profile
RUN cp -va $(nix-store -qR /output/profile) /output/store

COPY requirements.txt requirements.txt

RUN pip install setuptools && pip install -r requirements.txt

COPY package.json .
COPY yarn.lock .

RUN NODE_ENV=development yarn --pure-lockfile
RUN NODE_ENV=production yarn --pure-lockfile --modules-folder /production_node_modules

COPY .babelrc.json .
COPY webpack.config.tsx .
COPY manage.py .
COPY server server
COPY static static
COPY client client
COPY tsconfig.json .
COPY typings typings
COPY scripts scripts

RUN python manage.py generate_interfaces
RUN python manage.py generate_client_assets
RUN python manage.py generate_icons_sprite
RUN python manage.py collectstatic --no-input


# Renderer
# FROM builder as renderer
# RUN yarn renderer:build
# 
# 
# # Client
# FROM builder as client
# ENV NODE_ENV production
# 
# ARG DISABLE_SENTRY
# ARG RELEASE_VERSION
# ARG BUILD_VERSION
# ARG TAG_VERSION
# ARG SENTRY_AUTH_TOKEN
# ARG SENTRY_ORG
# ARG SENTRY_PROJECT
# 
# RUN yarn build
# 
# # Server
# FROM alpine
# 
# # Nix package is very heavy and includes the full DB.
# RUN apk add postgresql-client
# 
# COPY --from=builder /output/store /nix/store
# COPY --from=builder /output/profile/ /usr/local/
# 
# RUN mkdir /app
# WORKDIR /app
# 
# ENV NODE_ENV production
# 
# COPY manage.py .
# COPY server server
# COPY static static
# COPY scripts scripts
# 
# COPY --from=builder /production_node_modules node_modules
# COPY --from=builder /app/collected collected
# 
# COPY --from=renderer /app/client client
# COPY --from=client /app/dist/*.js collected/dist/
# COPY --from=client /app/dist/*.css collected/dist/
# 
# COPY requirements.txt requirements.txt
# RUN pip install setuptools && pip install -r requirements.txt
# 
# COPY containers/server/entrypoint.sh .
# RUN chmod +x entrypoint.sh
# 
# ENV PYTHONUNBUFFERED 1
# 
# ARG RELEASE_VERSION
# RUN echo $RELEASE_VERSION > RELEASE_VERSION
# 
# ARG BUILD_VERSION
# RUN echo $BUILD_VERSION > BUILD_VERSION
# 
# ARG TAG_VERSION
# RUN echo $TAG_VERSION > TAG_VERSION
# 
# ENTRYPOINT ["./entrypoint.sh"]
# CMD gunicorn server.wsgi --forwarded-allow-ips="*" --bind 0.0.0.0:8000 --workers 1 --preload
