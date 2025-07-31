FROM ubuntu@sha256:1b8d8ff4777f36f19bfe73ee4df61e3a0b789caeff29caa019539ec7c9a57f95

RUN apt update
RUN apt install -y curl xz-utils
RUN useradd -m guest
RUN mkdir /nix && mkdir /app && chown guest /nix && chown guest /app && mkdir /reactivated && chown guest /reactivated
RUN mkdir /etc/nix && echo 'filter-syscalls = false' >> /etc/nix/nix.conf

WORKDIR /app
USER guest
ENV USER=guest

RUN curl -L https://nixos.org/nix/install | sh

ENV PATH="/home/guest/.nix-profile/bin:/reactivated/scripts/:${PATH}"
ENV TMPDIR=/tmp

COPY --chown=guest package.json /reactivated/package.json
COPY --chown=guest scripts/create-django-app.sh /reactivated/scripts/install
COPY --chown=guest template /reactivated/template
COPY --chown=guest monorepo* /reactivated/monorepo/

ENV IS_DOCKER=true

RUN install populate_cache && rm -rf populate_cache
