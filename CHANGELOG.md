# Changelog

## [1.0.15] — 2026-11-17

- **Dynamic Grouped Sidebar Navigation (`ADM-006`)**: Added opt-in grouped sidebar navigation via `ADMINFLOW_NAVIGATION` or `ADMINFLOW_NAVIGATION_PROVIDER` with sub-navigation menus, server-side permission filtering, safe URL validation, keyboard accessibility, and sessionStorage accordion state persistence.
- **Enhanced System Checks**: Added Django system checks (`adminflow.W001`, `adminflow.E001`, `adminflow.E002`) validating `INSTALLED_APPS` ordering, navigation configuration, and model icon definitions.
- **Qualified Model Icon Resolver**: Extended `adminflow_icon` filter to resolve `app_label.object_name` qualified keys and callable resolvers.
- **Custom User Model Compatibility**: Made 2FA authentication views, user admin, and forms fully compatible with custom user models without hardcoded assumptions about `username` or `email` fields.
- **Relation-Aware Audit History Integration**: Updated history extras and templates to integrate with `django-simple-history-relation>=3.13.1`, featuring standalone version comparison view (`simple_history/compare_versions.html`) and current snapshot version badges.
- **Narrow Template Extension Points**: Added `change_form_messages`, `extra_change_form_head`, `change_form_header_meta`, `index_header_actions`, and `index_extra_panels` template blocks to prevent message duplication and allow seamless host extension.

## [1.0.14] — 2026-09-24

- **Custom "View Site" Link**: Added `ADMINFLOW_VIEW_SITE_URL` and `ADMINFLOW_SITE_URL` settings with automatic fallback to `.env` (`VIEW_SITE_URL`, `SITE_URL`). Opens in new tab from user profile dropdown and customizes "Return to site" on logged-out pages.
- **Login Layout Versions**: Added `ADMINFLOW_LOGIN_VERSION = 1` (split-screen hero) and `ADMINFLOW_LOGIN_VERSION = 2` (clean centered card without left banner).
- **Brand Monogram Logo Fallback**: Added automatic initial / initials badge fallback on sidebar, mobile navigation, and login pages when logo is missing, invalid, or fails to load (`onerror`).
- **Modern Checkbox & Toggle Cards**: Redesigned checkboxes and boolean fields across standard forms, inlines, and 2FA device setup into interactive toggle cards.
- **Flatpickr 12-Hour Time Format**: Fixed literal `"g"` formatting in 12-hour time inputs, ensuring proper token conversion (`h:i K` / `H:i`) with `time_24hr` support.
- **Expanded Model Field Types & Widget Support**: Added rich support for `JSONField`, `ReadOnlyPasswordHashWidget` security cards, password change views, and generic inlines alongside 2FA inlines.

## [1.0.13] — 2026-07-25

- Default to and enforce light theme across AdminFlow


## [1.0.12] — 2026-07-25

- Fix browser tab title rendering in admin/base.html to include current page title


## [1.0.11] — 2026-07-25

- Add urls.py configuration (adminflow_verify_2fa_view) to documentation and README


## [1.0.10] — 2026-07-25

- Fix FieldError on custom User models that use email as USERNAME_FIELD and do not have a username field


## [1.0.9] — 2026-07-25

- Update docs/index.rst badges to robust endpoints matching README


## [1.0.8] — 2026-07-25

- Update shields.io badges to robust endpoints for PyPI and GitHub


## [1.0.7] — 2026-07-25

- Use absolute raw GitHub URLs for screenshots and remove Publishing section from README


## [1.0.6] — 2026-07-25

- Use relative image paths in README for native GitHub.com rendering


## [1.0.5] — 2026-07-25

- Updated documentation link to https://django-adminflow.readthedocs.io/en/latest/ across README and PyPI project URLs


## [1.0.4] — 2026-07-25

- Updated Documentation URL to point to https://django-adminflow.readthedocs.io/en/latest/


## [1.0.3] — 2026-07-25

- Updated repo URLs to ramos208/Django-AdminFlow. with trailing period and master branch


## [1.0.2] — 2026-07-25

- Updated all GitHub URLs to ramos208/Django-AdminFlow
- Fixed screenshot image links on PyPI README
- Fixed ReadTheDocs edit-on-GitHub links in conf.py


## [1.0.1] — 2026-07-25

- Fixed README screenshot images — use absolute GitHub raw URLs so they render on PyPI


All notable changes are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] — 2026-07-23

- Initial stable release
- Modern minimalist admin UI (sidebar, Inter font, responsive)
- Full 2FA: TOTP, email OTP, backup codes, multi-device (django-otp)
- Audit history with field-level diffs (django-simple-history)
- Multi-sheet XLSX export/import (one sheet per related model)
- Nested JSON export (children embedded inside parent records)
- `MultiSheetExportImportMixin` for plug-and-play multi-resource export
- Styled Import / Export buttons, export page with field chips
- All `ADMINFLOW_*` theme settings + context processor
- Optional dependency groups: `[otp]`, `[history]`, `[import-export]`, `[all]`
