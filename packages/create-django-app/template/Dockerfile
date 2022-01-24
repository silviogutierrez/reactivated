FROM nixos/nix

RUN mkdir /app
WORKDIR /app

COPY shell.nix shell.nix

RUN nix-env -f shell.nix -i -A buildInputs

COPY requirements.txt requirements.txt

RUN virtualenv .venv && .venv/bin/pip install -r requirements.txt

COPY package.json .
COPY yarn.lock .

RUN yarn

RUN rm -rf node_modules/reactivated/*
COPY node_modules/reactivated node_modules/reactivated

COPY manage.py .
COPY server server
COPY static static
COPY client client
COPY tsconfig.json .

CMD .venv/bin/python manage.py runserver 0.0.0.0:8000
