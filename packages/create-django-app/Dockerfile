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

RUN nix-shell -p git --command 'git config --global user.email "bot@reactivated.io" && git config --global user.name "Reactivated"'

COPY package.json /reactivated/package.json
COPY scripts/create-django-app.sh /reactivated/scripts/create-django-app
COPY template /reactivated/template

RUN create-django-app populate_cache && rm -rf populate_cache
