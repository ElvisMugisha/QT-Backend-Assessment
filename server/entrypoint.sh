#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    # Simple wait loop
    while ! pg_isready -h $SQL_HOST -p $SQL_PORT -q -U $SQL_USER; do
      sleep 1
    done

    echo "PostgreSQL started"
fi

# Run migrations
# In a real CD pipieline, migrations are committed.
# Here we generate them on the fly if missing to ensure "accounts" table exists.
python manage.py makemigrations accounts
python manage.py migrate

# Start Gunicorn
# Bind to 0.0.0.0:8000
exec gunicorn qt_assessment.wsgi:application --bind 0.0.0.0:8000 --workers 3
