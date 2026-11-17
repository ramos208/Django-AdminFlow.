Customisation
=============

AdminFlow exposes all its branding and behaviour through ``settings.py`` variables.
Every setting has a sensible default so you only need to add what you want to change.

.. warning::

   ``adminflow.context_processors.adminflow_settings`` **must** be in ``TEMPLATES``
   for any of these settings to take effect in the UI:

   .. code-block:: python

      TEMPLATES = [{
          ...
          "OPTIONS": {
              "context_processors": [
                  ...
                  "adminflow.context_processors.adminflow_settings",  # ← required
              ],
          },
      }]

----

All Settings
------------

Branding
~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Setting
     - Default
     - Description
   * - ``ADMINFLOW_TITLE``
     - ``"AdminFlow"``
     - Text in the sidebar header and browser tab title
   * - ``ADMINFLOW_COMPANY``
     - ``"AdminFlow"``
     - Company name shown in the admin footer
   * - ``ADMINFLOW_LOGO``
     - *(not set)*
     - Filename relative to ``MEDIA_URL`` (e.g. ``"logo.svg"`` → ``/media/logo.svg``). If omitted, displays an automatic monogram badge.
   * - ``ADMINFLOW_VIEW_SITE_URL``
     - ``"/"``
     - Custom URL for "View Site" profile button and logged out redirect. Supports reading from ``.env`` (``VIEW_SITE_URL`` / ``SITE_URL``).

.. code-block:: python

   import os

   ADMINFLOW_TITLE   = "My SaaS App"
   ADMINFLOW_COMPANY = "Acme Corp"
   ADMINFLOW_LOGO    = "branding/logo.svg"   # optional

   # Option A: Read directly from .env
   ADMINFLOW_VIEW_SITE_URL = os.getenv("VIEW_SITE_URL", "https://myapp.example.com")

   # Option B: Hardcode custom route or external frontend URL
   ADMINFLOW_VIEW_SITE_URL = "/dashboard/"  # or "https://myapp.example.com"

Login Page
~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 30 35

   * - Setting
     - Default
     - Description
   * - ``ADMINFLOW_LOGIN_VERSION``
     - ``1``
     - ``1`` for split enterprise hero panel, ``2`` for clean centered card without left banner
   * - ``ADMINFLOW_LOGIN_TITLE``
     - ``"Master Your Enterprise Flow"``
     - Hero heading on the login page
   * - ``ADMINFLOW_LOGIN_SUBTITLE``
     - *(long default text)*
     - Subheading under the login title

.. code-block:: python

   ADMINFLOW_LOGIN_VERSION  = 1   # 1: split layout, 2: centered clean card (no left side)
   ADMINFLOW_LOGIN_TITLE    = "Welcome back"
   ADMINFLOW_LOGIN_SUBTITLE = "Sign in to manage your application."

Theme Colours
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 20 40

   * - Setting
     - Default
     - Description
   * - ``ADMINFLOW_PRIMARY_COLOR``
     - ``"#1f2021"``
     - Primary action colour (buttons, links, active states)
   * - ``ADMINFLOW_SECONDARY_COLOR``
     - ``"#475569"``
     - Secondary / muted colour
   * - ``ADMINFLOW_SUCCESS_COLOR``
     - ``"#10B981"``
     - Success badge / toast colour
   * - ``ADMINFLOW_WARNING_COLOR``
     - ``"#F59E0B"``
     - Warning badge / toast colour
   * - ``ADMINFLOW_DANGER_COLOR``
     - ``"#EF4444"``
     - Error / delete action colour

.. code-block:: python

   ADMINFLOW_PRIMARY_COLOR   = "#2563eb"   # blue
   ADMINFLOW_SUCCESS_COLOR   = "#16a34a"   # green
   ADMINFLOW_DANGER_COLOR    = "#dc2626"   # red

Sidebar
~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 20 40

   * - Setting
     - Default
     - Description
   * - ``ADMINFLOW_SIDEBAR_COLOR``
     - ``"#0f172a"``
     - Sidebar background colour
   * - ``ADMINFLOW_SIDEBAR_TEXT_COLOR``
     - ``"#94a3b8"``
     - Inactive navigation item text colour
   * - ``ADMINFLOW_SIDEBAR_ACTIVE_TEXT_COLOR``
     - ``"#ffffff"``
     - Active / hover navigation item text colour
   * - ``ADMINFLOW_SIDEBAR_COLLAPSIBLE``
     - ``True``
     - Allow the sidebar to be collapsed by clicking the toggle
   * - ``ADMINFLOW_SIDEBAR_WIDTH``
     - ``280``
     - Sidebar width in pixels when expanded

.. code-block:: python

   ADMINFLOW_SIDEBAR_COLOR             = "#1e293b"
   ADMINFLOW_SIDEBAR_TEXT_COLOR        = "#94a3b8"
   ADMINFLOW_SIDEBAR_ACTIVE_TEXT_COLOR = "#ffffff"
   ADMINFLOW_SIDEBAR_COLLAPSIBLE       = True
   ADMINFLOW_SIDEBAR_WIDTH             = 260

UI & Layout
~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 20 40

   * - Setting
     - Default
     - Description
   * - ``ADMINFLOW_BORDER_RADIUS``
     - ``"16px"``
     - CSS border-radius applied to cards, inputs, and buttons
   * - ``ADMINFLOW_FONT``
     - ``"Inter"``
     - Google Font loaded for the entire admin UI
   * - ``ADMINFLOW_ENABLE_COMMAND_PALETTE``
     - ``True``
     - Enable the Cmd+K / Ctrl+K quick-search command palette

.. code-block:: python

   ADMINFLOW_BORDER_RADIUS          = "8px"      # sharper corners
   ADMINFLOW_FONT                   = "Roboto"
   ADMINFLOW_ENABLE_COMMAND_PALETTE = False       # disable if not needed

Two-Factor Auth
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Setting
     - Default
     - Description
   * - ``ADMINFLOW_DJANGO_OTP``
     - ``True``
     - Show the OTP verification screen after login when a user has a confirmed device

.. code-block:: python

   ADMINFLOW_DJANGO_OTP = True   # set False to disable the 2FA flow UI

----

Per-Model Icon
--------------

Set the ``icon`` attribute on any ``ModelAdmin`` to show a
`Material Symbols <https://fonts.google.com/icons>`_ icon in the sidebar:

.. code-block:: python

   from django.contrib import admin
   from .models import Customer, Order, Product

   @admin.register(Customer)
   class CustomerAdmin(admin.ModelAdmin):
       icon = "person"

   @admin.register(Order)
   class OrderAdmin(admin.ModelAdmin):
       icon = "shopping_cart"

   @admin.register(Product)
   class ProductAdmin(admin.ModelAdmin):
       icon = "inventory_2"

Alternatively, map model names or ``"app_label.model_name"`` keys (or pass a callable)
via ``ADMINFLOW_MODEL_ICONS`` in ``settings.py``:

.. code-block:: python

   ADMINFLOW_MODEL_ICONS = {
       "auth.user": "manage_accounts",
       "customer": "contact_mail",
       "order": "shopping_cart",
   }

Browse icon names at https://fonts.google.com/icons — use the **Symbols** (outline) variant name.

----

Grouped Sidebar Navigation
--------------------------

By default, AdminFlow groups sidebar links by Django app using ``admin.site.get_app_list(request)``.
To organize authorized models into custom collapsible categories or nested sections, configure
``ADMINFLOW_NAVIGATION`` (or ``ADMINFLOW_NAVIGATION_PROVIDER``) in ``settings.py``.

Model links are always filtered through Django Admin's view/change permissions first; unauthorized
models are never shown, and unsafe URL schemes are rejected.

Declarative Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   ADMINFLOW_NAVIGATION = [
       {
           "key": "users",
           "label": "Users & Access",
           "icon": "manage_accounts",
           "models": ["auth.User", "auth.Group"],
           "model_labels": {"auth.Group": "Teams & Groups"},
       },
       {
           "key": "catalog",
           "label": "Catalog & Reference",
           "icon": "list_alt",
           "sections": [
               {"label": "Products", "models": ["shop.Category", "shop.Product"]},
               {"label": "Locations", "models": ["geo.Region", "geo.City"]},
           ],
       },
       {
           "key": "system",
           "label": "System & Other",
           "icon": "settings",
           "default": True,  # catch-all for any remaining authorized models
       },
   ]

Callable Provider
~~~~~~~~~~~~~~~~~

You can also point ``ADMINFLOW_NAVIGATION`` (or ``ADMINFLOW_NAVIGATION_PROVIDER``) to a callable
or dotted import path ``(request, apps) -> list[dict]``:

.. code-block:: python

   ADMINFLOW_NAVIGATION_PROVIDER = "myapp.navigation.build_admin_navigation"

----

Template Extension Hooks
------------------------

AdminFlow templates provide narrow blocks so host projects do not need to copy full templates:

* ``admin/base.html``:
  - ``{% block sidebar_nav %}`` — override or wrap sidebar navigation items
  - ``{% block sidebar_system_links %}`` — customize the bottom System links section
  - ``{% block topbar_actions %}`` — add action buttons next to the top-bar notification bell
* ``admin/change_form.html``:
  - ``{% block extra_change_form_head %}`` — load custom CSS/JS after form widget ``{{ media }}``
  - ``{% block change_form_header_meta %}`` — display metadata under the form title (automatically renders ``current_history_version`` when present)
  - ``{% block change_form_messages %}`` — customize the change-form toast notification area
* ``admin/index.html``:
  - ``{% block index_header_actions %}`` — add action buttons to the dashboard header
  - ``{% block index_extra_panels %}`` — insert custom cards/panels above the app grid

----

App Label in Sidebar
--------------------

AdminFlow uses each app's ``verbose_name`` from ``AppConfig`` as the sidebar group label:

.. code-block:: python

   # myapp/apps.py
   from django.apps import AppConfig

   class MyAppConfig(AppConfig):
       name         = "myapp"
       verbose_name = "Customer Relations (CRM)"   # ← shown in sidebar

----

Export Format Override
-----------------------

``MultiSheetExportImportMixin`` defaults to **xlsx** and **json** when ``combined_sheets``
is set. Override per-admin class:

.. code-block:: python

   from import_export.formats.base_formats import XLSX

   class ProductAdmin(MultiSheetExportImportMixin, ImportExportModelAdmin):
       export_formats_override = [XLSX]    # xlsx only
       # export_formats_override = None    # restore all formats
