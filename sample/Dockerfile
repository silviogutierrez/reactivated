FROM nixos/nix as builder

RUN mkdir /app
WORKDIR /app

COPY shell.nix shell.nix

RUN mkdir -p /output/store
RUN nix-env -f shell.nix -i -A buildInputs
RUN nix-env -f shell.nix -i -A dependencies --profile /output/profile
RUN cp -va $(nix-store -qR /output/profile) /output/store

COPY package.json .
COPY yarn.lock .
RUN NODE_ENV=development yarn --pure-lockfile
RUN NODE_ENV=production yarn --pure-lockfile --modules-folder /production_node_modules

COPY requirements.txt requirements.txt
RUN pip install setuptools && pip install -r requirements.txt

COPY .babelrc.json .
COPY webpack.config.tsx .
COPY manage.py .
COPY server server
COPY client client
COPY tsconfig.json .

RUN python manage.py generate_client_assets
RUN python manage.py collectstatic --no-input

RUN cp -va $(python -c "import site; print(site.getsitepackages()[0])") /output/python


FROM builder as client
RUN yarn build


FROM builder as renderer
RUN yarn tsc --noEmit && yarn babel client --out-dir client --extensions ".ts,.tsx" --source-maps inline


FROM alpine
ENV PYTHONUNBUFFERED 1
ENV NODE_ENV production

# Nix package is very heavy and includes the full DB.
RUN apk add postgresql-client

COPY --from=builder /output/store /nix/store
COPY --from=builder /output/profile/ /usr/local/

RUN mkdir /app
WORKDIR /app

COPY --from=builder /output/python /nix/python
COPY requirements.txt requirements.txt
RUN rm -rf $(python -c "import site; print(site.getsitepackages()[0])") && ln -sf /nix/python $(python -c "import site; print(site.getsitepackages()[0])")

COPY manage.py .
COPY server server

COPY --from=builder /production_node_modules node_modules
COPY --from=builder /app/assets assets

COPY --from=renderer /app/client client
COPY --from=client /app/dist/*.js assets/dist/
COPY --from=client /app/dist/*.css assets/dist/

RUN ln -s $(dirname `readlink /usr/local/bin/python`)/gunicorn /usr/local/bin/gunicorn;

CMD gunicorn server.wsgi --forwarded-allow-ips="*" --bind 0.0.0.0:$PORT --workers 1 --preload
