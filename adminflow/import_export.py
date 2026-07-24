"""
adminflow.import_export
=======================
Plug-and-play multi-sheet export/import mixin for Django admin.

Usage::

    from adminflow.import_export import MultiSheetExportImportMixin
    from import_export.admin import ImportExportModelAdmin

    class CustomerAdmin(MultiSheetExportImportMixin, ImportExportModelAdmin, ...):
        combined_sheets = [
            ('General Details', CustomerResource, None),
            ('Orders', OrderResource, lambda qs: Order.objects.filter(customer__in=qs)),
        ]

combined_sheets format:
    [(sheet_title, ResourceClass, queryset_lambda_or_None), ...]

Export behaviour:
    - XLSX  → one .xlsx file with one sheet per entry (requires openpyxl)
    - Other → ZIP archive containing one file per entry (e.g. Customers.csv + Orders.csv)

Import behaviour:
    - Multi-sheet .xlsx → each sheet processed by its paired resource
    - Single-sheet / other → falls back to default single-resource import
"""

try:
    import tablib
    HAS_TABLIB = True
except ImportError:
    HAS_TABLIB = False


class MultiSheetExportImportMixin:
    """
    Adds multi-resource export/import to any ImportExportModelAdmin subclass.
    """

    combined_sheets = []  # [(title, ResourceClass, qs_lambda_or_None), ...]

    # Formats shown in the export form. Override in subclass if needed.
    # Defaults to XLSX + JSON when combined_sheets is set; all formats otherwise.
    export_formats_override = None  # set to a list of format classes to force specific formats

    # ── Restrict available export formats ────────────────────────────────────
    def get_export_formats(self):
        from import_export.formats.base_formats import XLSX, JSON
        if self.export_formats_override is not None:
            return [f for f in self.export_formats_override if f().is_available()]
        if self.combined_sheets:
            return [f for f in [XLSX, JSON] if f().is_available()]
        return super().get_export_formats()

    # ── Export page context ───────────────────────────────────────────────────
    def init_request_context_data(self, request, form):
        context = super().init_request_context_data(request, form)
        if not self.combined_sheets:
            return context

        sub_sheets = []
        for title, resource_cls, _ in self.combined_sheets[1:]:
            try:
                resource_kwargs = self.get_export_resource_kwargs(request)
            except Exception:
                resource_kwargs = {}
            instance = resource_cls(**resource_kwargs)
            col_names = [f.column_name for f in instance.get_user_visible_fields()]
            sub_sheets.append({'title': title, 'fields': col_names})

        context['sub_sheets'] = sub_sheets
        context['primary_sheet_title'] = self.combined_sheets[0][0]
        return context

    # ── Override _do_file_export to produce XLSX or ZIP ──────────────────────
    def _do_file_export(self, file_format, request, queryset, export_form=None):
        if not self.combined_sheets or not HAS_TABLIB:
            return super()._do_file_export(file_format, request, queryset, export_form)

        from django.http import HttpResponse
        from import_export.signals import post_export

        try:
            ext = file_format.get_extension().lower()
        except Exception:
            ext = ''

        model_name = self.model._meta.model_name

        if ext == 'xlsx':
            # ── Multi-sheet XLSX ──────────────────────────────────────────
            book = tablib.Databook()
            for title, resource_cls, qs_func in self.combined_sheets:
                qs = qs_func(queryset) if qs_func is not None else queryset
                dataset = resource_cls().export(qs)
                dataset.title = title
                book.add_sheet(dataset)

            data = book.xlsx  # bytes
            response = HttpResponse(
                data,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            response['Content-Disposition'] = (
                f'attachment; filename="{model_name}_export.xlsx"'
            )

        else:
            # ── Truly nested JSON ─────────────────────────────────────────
            # Output structure (children embedded inside each parent):
            # [
            #   {
            #     "id": "1", "name": "Rooney", ...,   ← parent fields
            #     "orders": [                           ← nest_key from sub-sheet title
            #       {"id": "1", "customer_email": ..., ...}
            #     ]
            #   },
            #   ...
            # ]
            import json

            primary_title, primary_cls, _ = self.combined_sheets[0]
            sub_sheets = self.combined_sheets[1:]  # [(title, cls, qs_func), ...]

            all_records = []
            for obj in queryset:
                # Export this single parent
                single_qs = queryset.model.objects.filter(pk=obj.pk)
                parent_ds = primary_cls().export(single_qs)
                if not parent_ds or len(parent_ds) == 0:
                    continue
                parent_row = dict(zip(parent_ds.headers, parent_ds[0]))

                # Nest each sub-sheet under the parent using its title as key
                for sub_title, sub_cls, sub_qs_func in sub_sheets:
                    nest_key = sub_title.lower().replace(' ', '_')
                    if sub_qs_func is not None:
                        child_qs = sub_qs_func(single_qs)
                        child_ds = sub_cls().export(child_qs)
                        children = [
                            dict(zip(child_ds.headers, row))
                            for row in child_ds
                        ]
                    else:
                        children = []
                    parent_row[nest_key] = children

                all_records.append(parent_row)

            raw_json = json.dumps(all_records, indent=2, default=str)
            response = HttpResponse(raw_json, content_type='application/json')
            response['Content-Disposition'] = (
                f'attachment; filename="{model_name}_export.json"'
            )

        post_export.send(sender=None, model=self.model)
        return response


    # ── Import: detect multi-sheet XLSX ──────────────────────────────────────
    def import_action(self, request, *args, **kwargs):
        if not self.combined_sheets or not HAS_TABLIB:
            return super().import_action(request, *args, **kwargs)

        if request.method != 'POST' or 'confirm' not in request.POST:
            return super().import_action(request, *args, **kwargs)

        upload = request.FILES.get('import_file') or request.FILES.get('original_file_name')
        if upload is None:
            return super().import_action(request, *args, **kwargs)

        if not getattr(upload, 'name', '').lower().endswith('.xlsx'):
            return super().import_action(request, *args, **kwargs)

        try:
            raw = upload.read()
            book = tablib.Databook()
            book.load(raw, 'xlsx')
            sheets = book.sheets()
        except Exception:
            return super().import_action(request, *args, **kwargs)

        if len(sheets) < 2:
            return super().import_action(request, *args, **kwargs)

        from django.contrib import messages

        total_new = total_updated = total_error = 0
        for i, (title, resource_cls, _) in enumerate(self.combined_sheets):
            if i >= len(sheets):
                break
            try:
                result = resource_cls().import_data(
                    sheets[i],
                    dry_run=False,
                    raise_errors=False,
                    user=request.user,
                )
                total_new     += result.totals.get('new', 0)
                total_updated += result.totals.get('update', 0)
                total_error   += result.totals.get('error', 0)
            except Exception as e:
                messages.error(request, f"Error importing sheet '{title}': {e}")

        if total_error:
            messages.warning(
                request,
                f"Import finished — {total_new} new, {total_updated} updated, "
                f"{total_error} errors across all sheets.",
            )
        else:
            messages.success(
                request,
                f"Successfully imported all sheets — "
                f"{total_new} new records, {total_updated} updated.",
            )

        from django.http import HttpResponseRedirect
        from django.urls import reverse
        opts = self.model._meta
        return HttpResponseRedirect(
            reverse(f'admin:{opts.app_label}_{opts.model_name}_changelist')
        )
