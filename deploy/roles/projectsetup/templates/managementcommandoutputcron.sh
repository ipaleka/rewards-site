#!/bin/bash
output="$(export SECRET_KEY='{{ secret_key }}';export DATABASE_NAME={{ env_name }};export DATABASE_USER={{ env_name }};export DATABASE_PASSWORD='{{ db_pwd }}';cd {{ site_path }}/source/asastats/;{{ site_path }}/venv/bin/python manage.py {{ item.name }} --settings={{ django_settings }})"
if [[ {{ item.output }} ]] ; then
    exit 0
else
    echo $output
    exit 0
fi
