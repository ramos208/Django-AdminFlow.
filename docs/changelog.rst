Changelog
=========

All notable changes to this project are documented here.
The format follows `Keep a Changelog <https://keepachangelog.com/>`_.

----

`1.0.1`_ — 2026-07-25
----------------------

Added
~~~~~

* Fixed README screenshot images — use absolute GitHub raw URLs so they render on PyPI

.. _`1.0.1`: https://github.com/edgar/django-adminflow/releases/tag/v1.0.1

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

.. _`1.0.0`: https://github.com/edgar/django-adminflow/releases/tag/v1.0.0
