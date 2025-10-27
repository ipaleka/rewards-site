Provisioning
============

``Ansible`` is Python package used to deploy rewards-site infrastructure.

This guide is made for ``Ubuntu Server 24.04.03 LTS`` hosts, but it's applicable for many other Debian based Linux/GNU distros.


Local machine requirements
--------------------------

Ansible installation
^^^^^^^^^^^^^^^^^^^^

The most recent stable Ansible version is available through ``pip`` and its Python 3 version for Debian systems is called python3-pip.

.. code-block:: bash

  sudo apt-get install python3-pip

.. code-block:: bash

  pip3 install ansible --user


Server requirements/setup
-------------------------

Production
^^^^^^^^^^

SSH access
""""""""""

For majority of VPS providers, **root** user is already configured and ssh access is allowed by provided public key.


Virtual machine
^^^^^^^^^^^^^^^

Local network setup
"""""""""""""""""""

Configuration for Ubuntu 20.04 server:

.. code-block:: bash
  :caption: /etc/netplan/00-installer-config.yaml

  network:
    ethernets:
      enp0s3:
        addresses:
        - 192.168.1.82/24
        gateway4: 192.168.1.1
        nameservers:
          addresses:
          - 8.8.8.8
          - 4.4.4.4
          search: []
    version: 2

Configuration from above is activated by `sudo netplan apply`.


SSH access
""""""""""

Server should have ``openssh-server`` installed and running. Many GNU/Linux have Python 2 preinstalled, but on Ubuntu 16.04 it should be manually installed. Regularly Python 2 is only needed on the local machine, but for some jobs Ansible needs it on the servers too.

.. code-block:: bash

  sudo apt-get install openssh-server python3


For testing purposes in VM environment, a temporary user should be created. Upon first start it will enable the root login by running:

.. code-block:: bash

    tempuser@ubuntu:~# sudo passwd root


In Ubuntu ssh login for root is restricted, so it should be temporary allowed:

.. code-block:: bash

  sudo nano /etc/ssh/sshd_config
  PermitRootLogin yes


Default identity public key copying (use -i identity_file for different identity) from the local machine is issued by:

.. code-block:: bash

    ssh-copy-id root@192.168.1.82


Temporary user should be deleted afterwards:

.. code-block:: bash

    ssh root@192.168.1.82 "userdel tempuser; rm -rf /home/tempuser"


Project provisioning
--------------------

.. code-block:: bash

  # testing (virtual machine)
  ansible-playbook -i hosts --limit=testing site_playbook.yml

  # production
  ansible-playbook -i hosts --limit=production site_playbook.yml


For debugging purpose, add `-vv` or `-vvvv` for more verbose output:

.. code-block:: bash

  ansible-playbook -vv -i hosts --limit=testing site_playbook.yml


Update project code
^^^^^^^^^^^^^^^^^^^

After code has changed, issue the following command to apply those changes:

.. code-block:: bash

  ansible-playbook -i hosts --limit=production --tags=update-project-code site_playbook.yml


Sync cache and web severs
^^^^^^^^^^^^^^^^^^^^^^^^^

Sync web and cache server with:

.. code-block:: bash

  cd opt
  rsync -av --exclude "archive/*" --exclude "logs/*" --rsync-path="sudo rsync" asastats@167.114.67.118:/var/www/asastats.com/data/ ./data && sudo rsync -av -og --chown=whenmoon:webapps ./data/ /var/www/asastats.com/data
  rsync -av --rsync-path="sudo rsync" asastats@167.114.67.118:/var/www/asastats.com/static/thumbnails/ ./thumbnails && sudo rsync -av -og --chown=whenmoon:webapps ./thumbnails/ /var/www/asastats.com/static/thumbnails
