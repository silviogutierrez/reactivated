FROM nixos/nix as builder

RUN mkdir /app
WORKDIR /app

COPY shell.nix shell.nix
RUN nix-env -f shell.nix -i -A buildInputs


RUN mkdir /app/bar && chown 30001:30001 /app/bar && mkdir -p /run/postgresql && chown 30001:30001 /run/postgresql

RUN echo -en "#!/bin/sh\ninitdb /database\npg_ctl -D /database start -l /dev/null\nexec \"\$@\"\n" > /entrypoint.sh && chmod +x /entrypoint.sh

USER 30001
# RUN initdb /app/bar


ENV PGPORT=1
ENV PGDATABASE="database"

ENTRYPOINT ["/entrypoint.sh"]
CMD sh
# CMD pg_ctl -D /app/bar start && createdb database && bash
