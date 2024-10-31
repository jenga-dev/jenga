jenga
#####

|Build-Status| |Codecov| |Codefactor| |LICENCE|

A basic Python-based, CLI build system for BGII:EET games on MacOS.

.. code-block:: bash

  jenga run_full_build ~/Documents/my_eet_build/big_content_classic_systems.json


.. contents::

.. section-numbering:



Installation
============

To install, simply run:

.. code-block:: bash

  pip install bg-jenga


Use
===

Jenga installs a CLI command with the same name. You can run it with the ``--help`` flag to get a list of available commands and options:

.. code-block:: bash

  jenga --help


Also, run ``jenga --install-completion`` to install shell completion for the tool. This will enable you to use the ``TAB`` key to auto-complete commands and options.


Basic Workflow
--------------

1. Setting up mod directories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First, set up a directory where all zipped mods will be stored. Its location should populate the ``ZIPPED_MOD_CACHE_DIR_PATH`` configuration option in the config file (see below).

Then, set up a directory where all extracted mods will be stored. Its location should populate the ``EXTRACTED_MOD_CACHE_DIR_PATH`` configuration option in the config file (see below). **DO NOT** extract the mods yourself. Jenga will do that for you, and will use the chance to learn about the mods' structure and attributes by examining the mod folder structure and the contents of the main ``.tp2`` file and the ``.ini`` file, if it exists (this data will be stored in ``.jenga_hint.json`` files in the extracted mod directories).

Finally, set up the directories for the BGII:EET game installations. The locations of the game installations should populate the ``BGIIEE_DIR_PATHS`` configuration option in the config file (see below).

2. Setting up you config file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Here is an example of a JSON config file, which should be placed in ``~/.config/jenga/cfg.json``:

.. code-block:: json

    {
        "WEIDU_EXEC_PATH": "/Users/dirkgently/Library/Application Support/wit/weidu/macos/x86_64/weidu",
        "BGIIEE_DIR_PATHS": {
            "TARGET": "/Applications/Baldur's Gate II Enhanced Edition",
            "CLEAN_SOURCE": "/Applications/Baldur's Gate II Enhanced Edition_clean",
            "EET_SOURCE": "/Applications/Baldur's Gate II Enhanced Edition_EET",
            "BGEE_SOURCE": "/Applications/Baldur's Gate Enhanced Edition"
        },
        "ZIPPED_MOD_CACHE_DIR_PATH": "/Users/dirkgently/documents/bgee/zipped_mods",
        "EXTRACTED_MOD_CACHE_DIR_PATH": "/Users/dirkgently/bgee/extracted_mods",
        "DEFAULT_LANG": "en_US",
        "NUM_RETRIES": 1,
        "STOP_ON_WARNING": false,
        "STOP_ON_ERROR": true
    }


3. Converting a WeiDU log to a JSON build file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Note:* From now on, whenever JSON is mentioned, you can also take it to mean YAML, as both formats are supported for build files.

The first step in the process is to convert a WeiDU log file to a JSON build file. This can be done using the ``weidu_log_to_json_build_file`` command. For example:

.. code-block:: bash

  jenga weidu_log_to_json_build_file "/Applications/Baldur's Gate II Enhanced Edition/Weidu.log" --output "/Users/dirkgently/documents/bgee/jenga_files/my_150_mod_eet_build_2024.json"

Converts a WeiDU log file to a JSON build file. Optionally, specify an output path for the build file.  If not provided, a file named ``<date:time>_jenga_build_from_weidu_log.json`` will be created in the   │ same directory as the WeiDU log file.


4. Reordering and customizing the build file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here is an example of a JSON build file:

.. code-block:: json

    {
        "config": {
            "build_name": "reordered_shay_mac_24_by_subtle_06-24",
            "game": "BG2:EE",
            "lang": "en_US",
            "force_lang_in_weidu_conf": true,
            "pause_every_x_mods": 1,
            "skip_installed_mods": true,
            "prefer_mod_index": true,
            "confirm_each_install": true
        },
        "mods": [
            {
                "mod": "EET",
                "version": "V13.4",
                "language_int": "0",
                "install_list": "0",
                "components": [
                    {
                        "number": "0",
                        "description": "EET core (resource importation)"
                    }
                ]
            },
            {
                "mod": "LEUI-BG1EE",
                "version": "4.9",
                "language_int": "0",
                "install_list": "0 1",
                "components": [
                    {
                        "number": "0",
                        "description": "lefreut's Enhanced UI (BG1EE skin) - Core component"
                    },
                    {
                        "number": "1",
                        "description": "lefreut's Enhanced UI (BG1EE skin) - BG2 vanilla bams for spells"
                    }
                ]
            },
            ...
        ]
    }


5. Run Jenga to extract all zipped mods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

6. Build the mod index
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

  populate-mod-index


7. Run the build
^^^^^^^^^^^^^^^^

.. code-block:: bash

  jenga run_full_build ~/Documents/my_eet_build/big_content_classic_systems.json


8. Resume a partial build
^^^^^^^^^^^^^^^^^^^^^^^^^

If the build fails, you can resume it from the last state file that was saved. For example:

.. code-block:: bash

  jenga resume_partial_build ~/Documents/my_eet_build/big_content_classic_systems.json --state-file-path ~/Documents/my_eet_build/big_content_classic_systems.json.state


If ``--state-file-path`` is not provided, Jenga will look for the latest state file - for the specific build detailed in the provided build file - in the game directory.


Commands:
---------

- ``run_full_build <build_file_path>``

  Run a full build of a modded BG:EET game.

  - ``<build_file_path>``: The path to the build file.

- ``resume_partial_build <build_file_path> [--state-file-path <state_file_path>]``

  Resume a partial build of a modded BG:EET game.

  - ``<build_file_path>``: The path to the build file.
  - ``--state-file-path, -s <state_file_path>``: (Optional) The path to the state file to resume from.

- Additional commands can be explored using ``jenga --help``.


Configuration
=============

Jenga has two levels of configuration:

Tool Configuration
------------------

Global configuration for the ``jenga`` tool is loaded from two sources: First, from the ``~/.config/jenga/cfg.json`` file. Then, from any environment variables prefixed with ``JENGA_``. The environment variables take precedence over the file.

Tool configuration options are:

Build Configuration
Jenga processes build configuration primarily through WeiDU log files which are transformed into JSON files that define the mods and build order. You can configure the build settings by using functionalities such as:



Build Configuration
-------------------

Build specific configuraiton is determined by the ``config`` section in the build file. The following options are available:


Here is an example of a JSON build file:

.. code-block:: json

    {
        "config": {
            "build_name": "reordered_shay_mac_24_by_subtle_06-24",
            "game": "BG2:EE",
            "lang": "en_US",
            "force_lang_in_weidu_conf": true,
            "pause_every_x_mods": 1,
            "skip_installed_mods": true,
            "prefer_mod_index": true,
            "confirm_each_install": true
        },
        "mods": [
            ...
        ]
    }


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
