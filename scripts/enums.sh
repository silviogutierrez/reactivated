#!/bin/bash

set -e

DATABASE_NAME="reactivated";
psql postgres -c 'SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid()'
psql postgres -c "DROP DATABASE IF EXISTS \"$DATABASE_NAME\""
psql postgres -c "CREATE DATABASE \"$DATABASE_NAME\""
rm -rf server/apps/samples/migrations/*
touch server/apps/samples/migrations/__init__.py

python manage.py makemigrations
python manage.py migrate

psql reactivated -c "\dt"

export STAGE=two;
python manage.py makemigrations
python manage.py migrate

psql reactivated -c "\dt"
psql reactivated -c "\d+ samples_two"

export STAGE=three;

python manage.py makemigrations
python manage.py migrate

psql reactivated -c "\dt"
psql reactivated -c "\d+ samples_two"

export STAGE=four;

python manage.py makemigrations
python manage.py migrate

psql reactivated -c "\dt"
psql reactivated -c "\d+ samples_two"

export STAGE=five;

python manage.py makemigrations
python manage.py migrate

psql reactivated -c "\dt"
