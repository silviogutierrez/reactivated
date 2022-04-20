FROM ubuntu
RUN apt update
RUN apt install -y curl xz-utils
RUN useradd -m guest
RUN mkdir /nix && mkdir /app && chown guest /nix && chown guest /app && mkdir /reactivated && chown guest /reactivated

WORKDIR /app
USER guest
ENV USER=guest
RUN curl -L https://nixos.org/nix/install | sh

ENV PATH="/home/guest/.nix-profile/bin:/reactivated/scripts/:${PATH}"
ENV REACTIVATED_SOCKET=/tmp/reactivated.sock
ENV TMPDIR=/tmp

COPY package.json /reactivated/package.json
COPY scripts/create-django-app.sh /reactivated/scripts/install
COPY template /reactivated/template

ENV IS_DOCKER=true

RUN install populate_cache && rm -rf populate_cache
