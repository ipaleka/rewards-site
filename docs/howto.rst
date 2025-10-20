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


Run Dicord bot
--------------

.. code-block:: bash

  PYTHONPATH=rewardsweb python -m rewardsbot.bot