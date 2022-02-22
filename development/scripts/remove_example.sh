#! /usr/bin/env nix-shell
#! nix-shell ../shell.nix --pure -i bash
sed -i /example/d server/settings/common.py
sed -i /example/d server/urls.py
rm -r server/example
rm client/templates/{DjangoDefault,EditPoll,PollDetail,PollsIndex,Results}.tsx
echo "DELETE from django_migrations WHERE app = 'example'" | python manage.py dbshell
rm "$0"
