# Changelog

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
