jenga
#####

|Build-Status| |Codecov| |Codefactor| |LICENCE|

A basic Python-based, CLI build system for BGII:EET games.

.. code-block:: bash

  jenga run_full_build ~/Documents/my_eet_build/big_content_classic_systems.json


.. contents::

.. section-numbering:



Installation
============

TBA.


Configuration
=============

TBA.


Use
===

TBA.


Contributing
============

Tool author and maintainer is Shay Palachy Affek (`shay.palachy@gmail.com <mailto:shay.palachy@gmail.com>`_, `@shaypal5 <https://github.com/shaypal5>`_). You are more than welcome to approach him for help. Contributions are very welcomed! :)


Installing for development
--------------------------

Clone:

.. code-block:: bash

  git clone git@github.com:jenga-dev/jenga.git


Install in development mode with test dependencies:

.. code-block:: bash

  cd jenga
  pip install -e . -r tests/requirements.txt


Running the tests
-----------------

To run the tests, call the ``pytest`` command in the repository's root, or:

.. code-block:: bash

  python -m pytest


Adding documentation
--------------------

This project is documented using the `numpy docstring conventions`_, which were chosen as they are perhaps the most widely-spread conventions that are both supported by common tools such as Sphinx and result in human-readable docstrings (in my personal opinion, of course). When documenting code you add to this project, please follow `these conventions`_.

.. _`numpy docstring conventions`: https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt
.. _`these conventions`: https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt

Additionally, if you update this ``README.rst`` file, use ``python setup.py checkdocs`` to validate it compiles.


Credits
=======

Created by `Shay Palachy Affek <https://github.com/shaypal5>`_ (shay.palachy@gmail.com).


.. |PyPI-Status| image:: https://img.shields.io/pypi/v/jenga.svg
  :target: https://pypi.python.org/pypi/jenga

.. |PyPI-Versions| image:: https://img.shields.io/pypi/pyversions/jenga.svg
   :target: https://pypi.python.org/pypi/jenga

.. |Build-Status| image:: https://github.com/jenga-dev/jenga/actions/workflows/ci-test.yml/badge.svg
   :target: https://github.com/jenga-dev/jenga/actions/workflows/ci-test.yml

.. |LICENCE| image:: https://img.shields.io/badge/License-MIT-ff69b4.svg
   :target: https://github.com/jenga-dev/jenga

.. |Codecov| image:: https://codecov.io/github/jenga-dev/jenga/coverage.svg?branch=master
   :target: https://codecov.io/github/jenga-dev/jenga?branch=master

.. |Downloads| image:: https://pepy.tech/badge/jenga
     :target: https://pepy.tech/project/jenga
     :alt: PePy stats

.. |Codefactor| image:: https://www.codefactor.io/repository/github/jenga-dev/jenga/badge?style=plastic
     :target: https://www.codefactor.io/repository/github/jenga-dev/jenga
     :alt: Codefactor code quality
