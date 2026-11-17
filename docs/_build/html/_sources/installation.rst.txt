Installation
============

Requirements
------------

* Python 3.10 or higher
* Django 4.2 or higher

AdminFlow's core UI has **no mandatory 3rd party dependencies** beyond Django itself.
Optional integrations (2FA, history, import/export) pull in additional packages only
when you choose the matching extras.

----

Installing AdminFlow
--------------------

Core UI only
~~~~~~~~~~~~

Installs the admin template skin with no extra dependencies:

.. code-block:: bash

   pip install django-adminflow

With Two-Factor Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pulls in ``django-otp`` and its TOTP/email/static plugins:

.. code-block:: bash

   pip install "django-adminflow[otp]"

With Audit History
~~~~~~~~~~~~~~~~~~

Pulls in ``django-simple-history-relation``:

.. code-block:: bash

   pip install "django-adminflow[history]"

With Import / Export
~~~~~~~~~~~~~~~~~~~~

Pulls in ``django-import-export``, ``tablib[xlsx]``, and ``openpyxl``:

.. code-block:: bash

   pip install "django-adminflow[import-export]"

Everything at once
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install "django-adminflow[all]"

----

Dependency Reference
--------------------

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Extra
     - Packages installed
     - Purpose
   * - ``[otp]``
     - ``django-otp>=1.4``
     - Two-factor authentication
   * - ``[history]``
     - ``django-simple-history-relation>=3.13.1``
     - Audit trail with field-level & ManyToMany diffs
   * - ``[import-export]``
     - ``django-import-export>=4.0``, ``tablib[xlsx]>=3.5``, ``openpyxl>=3.1``
     - XLSX and JSON data import/export
   * - ``[all]``
     - All of the above
     - Full feature set

----

Next Steps
----------

* :doc:`quickstart` — add AdminFlow to your project in 5 minutes
* :doc:`two-factor-auth` — set up 2FA for your users
* :doc:`import-export` — export related models as multi-sheet XLSX or nested JSON
