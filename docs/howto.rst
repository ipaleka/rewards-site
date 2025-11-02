Howto
=====

Build documenattion
-------------------

.. code-block:: bash

  cd docs
  make html


Requirements to build latexpdf documentation:

.. code-block:: bash

  sudo apt-get install texlive texlive-latex-extra latexmk


Then build the pdf with:

.. code-block:: bash

  make latexpdf


GitHub bot
----------

Create rewards-bot as a GitHub App and then install it under your organization settings page.

Assign created app's token to GITHUB_BOT_TOKEN constant in `rewardsweb/.env` file.


Run Discord bot
---------------

.. code-block:: bash

  PYTHONPATH=rewardsweb python -m rewardsbot.bot