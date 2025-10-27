#!/bin/bash
output="$(export SECRET_KEY='{{ global_env_vars['SECRET_KEY'] }}';export DATABASE_NAME={{ global_env_vars['DATABASE_NAME'] }};export DATABASE_USER={{ global_env_vars['DATABASE_USER'] }};export DATABASE_PASSWORD='{{ global_env_vars['DATABASE_PASSWORD'] }}';cd {{ site_path }}/source/{{ app_name }}/;{{ site_path }}/venv/bin/python manage.py {{ item.name }} --settings={{ django_settings }})"
if [[ {{ item.output }} ]] ; then
    exit 0
else
    echo $output
    exit 0
fi
