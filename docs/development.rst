Development
===========

Setup
-----

The requirements necessary to use this project on a development machine are:

.. code-block:: bash

  sudo apt-get install git python3 python3-venv postgresql postgresql-contrib


Python environment
^^^^^^^^^^^^^^^^^^

Create Python virtual environment:

.. code-block:: bash

  python3 -m venv rewards


Set some environment variables upon activation:

.. code-block:: bash
  :caption: /home/ipaleka/dev/venvs/rewards/bin/activate

  export DJANGO_SETTINGS_MODULE=rewardsweb.settings.development


Activate Python environment:

.. code-block:: bash

  source rewards/bin/activate


Adding an alias can be useful:

.. code-block:: bash
  :caption: ~/.bashrc

  alias 'rwds'='cd /home/ipaleka/dev/rewards_site/rewardsweb;source /home/ipaleka/dev/venvs/rewards/bin/activate'


Initial packages installation:

.. code-block:: bash

  (rewards) ipaleka@debian:~/dev/rewards_site/rewardsweb$ pip install -r requirements/development.txt


Run developemnt server
----------------------

.. code-block:: bash

  python manage.py runserver


PostgreSQL
----------

PostgreSQL setup in development
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Database creation on development machine:

.. code-block:: bash

  root@debian:~# su - postgres
  postgres@debian:~# createdb rewards_db


Database user setup on development machine (CREATEDB is needed for running tests, while
pg_trgm extension is used for determining the similarity of text based on trigram matching):

.. code-block:: bash

  postgres@debian:~# psql
  postgres=# CREATE USER rewards_user WITH ENCRYPTED PASSWORD 'mypassword';
  postgres=# ALTER USER rewards_user CREATEDB;
  postgres=# ALTER DATABASE rewards_db OWNER TO rewards_user;
  postgres=# CREATE EXTENSION IF NOT EXISTS pg_trgm;


Finally, under rewards web Python environemnt:

.. code-block:: bash

  python manage.py makemigrations
  python manage.py migrate


DaisyUI
-------

Follow the instructions found
`here <https://daisyui.com/docs/install/django/>`. One of the alternatives to **watchman**
is **entr** (you can install it on Debain based systems with `sudo apt-get install entr`),
invoke the following trigger build/watch command to use it:

.. code-block:: bash

  $ ls core/static/css/*.css | entr core/static/css/tailwindcss -i core/static/css/input.css -o core/static/css/style.css --minify


SonarQube
^^^^^^^^^

`SonarQube <https://docs.sonarsource.com/sonarqube-community-build>`_
is an automated code review and static analysis tool designed to detect coding issues.
You can find the installation instructions
`here <https://docs.sonarsource.com/sonarqube-community-build/try-out-sonarqube>`.


Starting server
"""""""""""""""

.. code-block:: bash

  $ ~/opt/repos/sonarqube-25.9.0/bin/linux-x86-64/sonar.sh console


Starting scanner
""""""""""""""""

You should add scanner executable to your PATH. `download`_ For example, by adding the following
line to your ``~/.bashrc``:

.. code-block:: bash

  export PATH=$PATH:~/opt/repos/sonar-scanner-7.2/bin


After a token `token`_ is created. start scanning by running the scanner from the root directory of the project with:

.. code-block:: bash

  $ sonar-scanner -Dsonar.projectKey=rewards.asastats.com -Dsonar.host.url=http://localhost:9000 -Dsonar.token=squ_5d45cb850753a0a512d4bc639771601a31a6a4c8


For additional information read the scanner `documentation`_.

.. _documentation: https://docs.sonarqube.org/latest/analysis/scan/sonarscanner/
.. _token: http://localhost:9000/account/security
.. _download: https://docs.sonarsource.com/sonarqube-server/latest/analyzing-source-code/scanners/sonarscanner/


Tests
-----

Python
^^^^^^

Run all tests:

.. code-block:: bash

  cd /home/ipaleka/dev/rewards_site/rewardsweb
  source /home/ipaleka/dev/venvs/rewards/bin/activate
  python -m pytest -v  # or just pytest -v


Run tests matching pattern:

.. code-block:: bash

  pytest -v -k test_contributor_model  # pytest -vvv for more verbose output

