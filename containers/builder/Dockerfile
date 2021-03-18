FROM nixos/nix as builder

RUN mkdir /app
WORKDIR /app

COPY nix nix
COPY shell.nix shell.nix

RUN mkdir -p /output/store
RUN nix-env -f shell.nix -i -A buildInputs
RUN nix-env -f shell.nix -i -A dependencies --profile /output/profile
RUN cp -va $(nix-store -qR /output/profile) /output/store

COPY requirements.txt .
COPY setup.py .
COPY README.md .
COPY packages packages

RUN pip install setuptools && pip install -r requirements.txt

COPY package.json .
COPY yarn.lock .

RUN NODE_ENV=development yarn --pure-lockfile
RUN NODE_ENV=production yarn --pure-lockfile --modules-folder /production_node_modules
