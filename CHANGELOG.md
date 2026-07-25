# Changelog

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
