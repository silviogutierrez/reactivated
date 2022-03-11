#! /usr/bin/env nix-shell
#! nix-shell ../shell.nix -i bash
DJANGO_VERSION=$(python -c "import django; print(django.get_version(), end='')")
sed -i /example/d server/settings/common.py
sed -i /example/d server/urls.py
git rm -r server/example
# shellcheck disable=SC2016
sed -i 's/${context.django_version}/'"$DJANGO_VERSION"'/' client/components/Layout.tsx
sed -i 's/{context.django_version}/'"$DJANGO_VERSION"'/' client/components/Layout.tsx
git rm client/templates/{FormPlayground,DjangoDefault,EditPoll,PollDetail,PollsIndex,Results,PollComments}.tsx
scripts/fix.sh
echo "DELETE from django_migrations WHERE app = 'example'" | python manage.py dbshell
git rm -f "$0"
