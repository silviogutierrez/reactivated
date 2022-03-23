FROM nixos/nix as builder

RUN mkdir /app
WORKDIR /app

COPY shell.nix shell.nix

RUN mkdir -p /output/store
RUN nix-env -f shell.nix --option filter-syscalls false -i -A buildInputs --profile /output/profile;
RUN cp -va $(nix-store -qR /output/profile) /output/store

FROM alpine

RUN apk add bash
RUN mkdir /app
WORKDIR /app

COPY --from=builder /output/store /nix/store
COPY --from=builder /output/profile/ /usr/local/

RUN echo -en "#!/bin/sh\nsource scripts/setup_environment.sh\npython manage.py migrate\nexec \"\$@\"\n" > /entrypoint.sh && chmod +x /entrypoint.sh

USER guest

ENV REACTIVATED_SOCKET=/tmp/reactivated.sock
ENV TMPDIR=/tmp
ENV HOME=/tmp

ENTRYPOINT ["/entrypoint.sh"]

CMD python manage.py runserver 0.0.0.0:8000
