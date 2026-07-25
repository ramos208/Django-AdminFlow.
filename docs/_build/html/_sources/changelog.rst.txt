Changelog
=========

All notable changes to this project are documented here.
The format follows `Keep a Changelog <https://keepachangelog.com/>`_.

----

`1.0.8`_ — 2026-07-25
----------------------

Added
~~~~~

* Update shields.io badges to robust endpoints for PyPI and GitHub

.. _`1.0.8`: https://github.com/ramos208/Django-AdminFlow./releases/tag/v1.0.8

`1.0.7`_ — 2026-07-25
----------------------

Added
~~~~~

* Use absolute raw GitHub URLs for screenshots and remove Publishing section from README

.. _`1.0.7`: https://github.com/ramos208/Django-AdminFlow./releases/tag/v1.0.7

`1.0.6`_ — 2026-07-25
----------------------

Added
~~~~~

* Use relative image paths in README for native GitHub.com rendering

.. _`1.0.6`: https://github.com/ramos208/Django-AdminFlow./releases/tag/v1.0.6

`1.0.5`_ — 2026-07-25
----------------------

Added
~~~~~

* Updated documentation link to https://django-adminflow.readthedocs.io/en/latest/ across README and PyPI project URLs

.. _`1.0.5`: https://github.com/ramos208/Django-AdminFlow./releases/tag/v1.0.5

`1.0.4`_ — 2026-07-25
----------------------

Added
~~~~~

* Updated Documentation URL to point to https://django-adminflow.readthedocs.io/en/latest/

.. _`1.0.4`: https://github.com/ramos208/Django-AdminFlow./releases/tag/v1.0.4

`1.0.3`_ — 2026-07-25
----------------------

Added
~~~~~

* Updated repo URLs to ramos208/Django-AdminFlow. with trailing period and master branch

.. _`1.0.3`: https://github.com/ramos208/Django-AdminFlow./releases/tag/v1.0.3

`1.0.2`_ — 2026-07-25
----------------------

Added
~~~~~

* Updated all GitHub URLs to ramos208/Django-AdminFlow
* Fixed screenshot image links on PyPI README
* Fixed ReadTheDocs edit-on-GitHub links in conf.py

.. _`1.0.2`: https://github.com/ramos208/Django-AdminFlow./releases/tag/v1.0.2

`1.0.1`_ — 2026-07-25
----------------------

Added
~~~~~

* Fixed README screenshot images — use absolute GitHub raw URLs so they render on PyPI

.. _`1.0.1`: https://github.com/ramos208/Django-AdminFlow./releases/tag/v1.0.1

`1.0.0`_ — 2026-07-23
-----------------------

Added
~~~~~

* Modern minimalist admin UI — sidebar navigation, Inter font, Material Symbols icons,
  responsive layout
* Dashboard with system stats cards (DB engine, Django version, Python version,
  registered model count) and per-app model grid
* Toast notification system for login success / action feedback
* **2FA integration** (``django-otp``):

  * TOTP support (Google Authenticator, Authy, 1Password)
  * Email OTP support
  * Backup codes (static OTP)
  * Multi-device management per user
  * Admin bulk actions: *Enable 2FA*, *Generate backup codes*
  * ``AdminFlowUserAdminMixin``, ``get_2fa_inlines()``, ``unregister_otp_models()``

* **Audit history integration** (``django-simple-history``):

  * Field-level diff rendering (red strikethrough → green)
  * Timeline view per record
  * ``HistoryRequestMiddleware`` integration for automatic user tracking

* **Import / Export integration** (``django-import-export``):

  * ``MultiSheetExportImportMixin``
  * ``combined_sheets`` API for grouping related models
  * Multi-sheet XLSX export (one sheet per resource, requires ``openpyxl``)
  * Nested JSON export (child records embedded inside parent records)
  * Multi-sheet XLSX import (atomic per sheet)
  * Export page with field-selection chips grouped by sheet
  * Import/Export buttons on the changelist toolbar

* Optional dependency groups: ``[otp]``, ``[history]``, ``[import-export]``, ``[all]``
* ``ADMINFLOW_TITLE`` setting
* Per-model ``icon`` attribute for Material Symbols sidebar icons
* i18n — all UI strings wrapped in ``{% translate %}``
* ``pyproject.toml`` with full PyPI classifiers, optional extras, and project URLs

.. _`1.0.0`: https://github.com/ramos208/Django-AdminFlow./releases/tag/v1.0.0
