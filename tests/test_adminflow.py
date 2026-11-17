from __future__ import annotations

import subprocess
import time
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.checks import run_checks
from django.template import Context, Template
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import path

from adminflow.context_processors import DEFAULTS, adminflow_settings
from adminflow.navigation import get_grouped_navigation, is_safe_navigation_url
from adminflow.templatetags.adminflow_tags import adminflow_icon, adminflow_navigation_groups
from adminflow.views import _user_display_label, adminflow_login_view, adminflow_verify_2fa_view

urlpatterns = [
    path("admin/verify-2fa/", adminflow_verify_2fa_view, name="adminflow_verify_2fa"),
    path("admin/", admin.site.urls),
]


def sample_callable_provider(request, apps):
    return [
        {
            "key": "custom-group",
            "label": "Custom Group",
            "icon": "layers",
            "sections": [
                {
                    "label": "Sub Section",
                    "models": [
                        {"name": "Users", "url": "/admin/auth/user/"},
                    ],
                }
            ],
        }
    ]


class NavigationUnitTests(SimpleTestCase):
    def _model(self, name: str, app: str = "auth") -> dict:
        return {
            "object_name": name,
            "name": f"{name}s",
            "admin_url": f"/admin/{app}/{name.lower()}/",
        }

    def test_url_safety_validation_rejects_unsafe_schemes(self):
        self.assertTrue(is_safe_navigation_url("/admin/auth/user/"))
        self.assertTrue(is_safe_navigation_url("https://example.com/docs"))
        self.assertTrue(is_safe_navigation_url("http://localhost:8000/admin/"))

        self.assertFalse(is_safe_navigation_url(""))
        self.assertFalse(is_safe_navigation_url(None))
        self.assertFalse(is_safe_navigation_url("//evil.example.com/phish"))
        self.assertFalse(is_safe_navigation_url("javascript:alert(1)"))
        self.assertFalse(is_safe_navigation_url("JAVASCRIPT:alert(1)"))
        self.assertFalse(is_safe_navigation_url("data:text/html,<script>alert(1)</script>"))
        self.assertFalse(is_safe_navigation_url("vbscript:msgbox(1)"))
        self.assertFalse(is_safe_navigation_url("relative/without/leading/slash"))
        self.assertFalse(is_safe_navigation_url("/admin/bad path"))

    def test_disabled_by_default_returns_empty_list(self):
        request = SimpleNamespace(
            path="/admin/",
            user=SimpleNamespace(is_authenticated=True, has_perm=lambda p: True),
        )
        self.assertEqual(get_grouped_navigation(request, apps=[{"app_label": "auth", "models": [self._model("User")]}]), [])

    @override_settings(
        ADMINFLOW_NAVIGATION=[
            {
                "key": "access",
                "label": "Users & Access",
                "icon": "manage_accounts",
                "models": ["auth.Group", "auth.User"],
                "model_labels": {"auth.Group": "Teams & Groups"},
            },
            {
                "key": "reference",
                "label": "Reference Data",
                "icon": "list_alt",
                "sections": [
                    {"label": "Geography", "models": ["geo.Region", "geo.City"]},
                    {"label": "Catalog", "models": ["catalog.Category"]},
                ],
            },
            {
                "key": "system",
                "label": "System & Other",
                "icon": "settings",
                "default": True,
            },
        ]
    )
    def test_declarative_groups_preserve_order_subgroups_labels_and_catchall(self):
        apps = [
            {
                "app_label": "auth",
                "models": [self._model("User", "auth"), self._model("Group", "auth")],
            },
            {
                "app_label": "geo",
                "models": [self._model("City", "geo"), self._model("Region", "geo")],
            },
            {
                "app_label": "plugin",
                "models": [self._model("Webhook", "plugin")],
            },
        ]
        request = SimpleNamespace(
            path="/admin/geo/region/42/change/",
            user=SimpleNamespace(is_authenticated=True, has_perm=lambda p: True),
        )
        groups = get_grouped_navigation(request, apps=apps)
        self.assertEqual([g["key"] for g in groups], ["access", "reference", "system"])

        # Access group follows configured order (Group then User) and applies label override
        access_items = groups[0]["sections"][0]["models"]
        self.assertEqual([m["name"] for m in access_items], ["Teams & Groups", "Users"])
        self.assertFalse(groups[0]["active"])

        # Reference group has nested Geography section (Catalog is omitted because not in authorized apps)
        ref_sections = groups[1]["sections"]
        self.assertEqual([s["label"] for s in ref_sections], ["Geography"])
        self.assertEqual([m["name"] for m in ref_sections[0]["models"]], ["Regions", "Citys"])
        self.assertTrue(ref_sections[0]["models"][0]["active"])
        self.assertTrue(ref_sections[0]["active"])
        self.assertTrue(groups[1]["active"])

        # Catch-all group retains authorized uncategorized models
        sys_items = groups[2]["sections"][0]["models"]
        self.assertEqual([m["name"] for m in sys_items], ["Webhooks"])

    @override_settings(
        ADMINFLOW_NAVIGATION=[
            {
                "key": "security",
                "label": "Security",
                "icon": "shield",
                "models": ["auth.User", "auth.Permission"],
                "items": [
                    {
                        "label": "Audit Dashboard",
                        "url": "/admin/audit-dashboard/",
                        "permission": "auth.view_permission",
                    },
                    {
                        "label": "Unsafe Link",
                        "url": "javascript:alert(1)",
                    },
                ],
            }
        ]
    )
    def test_unauthorized_models_and_unsafe_urls_are_omitted_server_side(self):
        # User only has User in get_app_list (not Permission) and lacks 'auth.view_permission'
        apps = [{"app_label": "auth", "models": [self._model("User", "auth")]}]
        request = SimpleNamespace(
            path="/admin/",
            user=SimpleNamespace(is_authenticated=True, has_perm=lambda perm: False),
        )
        groups = get_grouped_navigation(request, apps=apps)
        self.assertEqual(len(groups), 1)
        items = groups[0]["sections"][0]["models"]
        self.assertEqual([m["name"] for m in items], ["Users"])

    @override_settings(ADMINFLOW_NAVIGATION="tests.test_adminflow.sample_callable_provider")
    def test_dotted_path_callable_provider(self):
        request = SimpleNamespace(
            path="/admin/auth/user/",
            user=SimpleNamespace(is_authenticated=True),
        )
        groups = get_grouped_navigation(request, apps=[])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["key"], "custom-group")
        self.assertTrue(groups[0]["active"])
        self.assertTrue(groups[0]["sections"][0]["models"][0]["active"])

    @override_settings(ADMINFLOW_NAVIGATION=["not-a-dict", {"label": "", "models": []}, {"label": "Valid", "sections": "invalid"}])
    def test_malformed_navigation_config_fails_gracefully(self):
        request = SimpleNamespace(path="/admin/", user=SimpleNamespace(is_authenticated=True))
        self.assertEqual(get_grouped_navigation(request, apps=[]), [])


class SystemChecksAndIconTests(SimpleTestCase):
    @override_settings(
        INSTALLED_APPS=[
            "django.contrib.admin",
            "adminflow",
            "django.contrib.auth",
            "django.contrib.contenttypes",
        ]
    )
    def test_check_warns_when_adminflow_after_django_admin(self):
        messages = run_checks()
        ids = [m.id for m in messages]
        self.assertIn("adminflow.W001", ids)

    @override_settings(
        ADMINFLOW_NAVIGATION="nonexistent.module.provider",
        ADMINFLOW_MODEL_ICONS="invalid-not-a-dict",
    )
    def test_check_reports_invalid_navigation_and_icon_settings(self):
        messages = run_checks()
        ids = [m.id for m in messages]
        self.assertIn("adminflow.E001", ids)
        self.assertIn("adminflow.E002", ids)

    @override_settings(
        ADMINFLOW_MODEL_ICONS={
            "auth.user": "manage_accounts",
            "custommodel": "star",
        }
    )
    def test_adminflow_icon_resolves_app_qualified_and_custom_icons(self):
        self.assertEqual(
            adminflow_icon({"app_label": "auth", "object_name": "User"}),
            "manage_accounts",
        )
        self.assertEqual(adminflow_icon("CustomModel"), "star")
        self.assertEqual(adminflow_icon("UnknownWidgetXYZ"), "grid_view")

    @override_settings(ADMINFLOW_MODEL_ICONS=lambda val: "bolt" if val == "DynamicModel" else None)
    def test_adminflow_icon_supports_callable_resolver(self):
        self.assertEqual(adminflow_icon("DynamicModel"), "bolt")
        self.assertEqual(adminflow_icon("User"), "person")


class TemplateAndViewIntegrationTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            username="admin_root",
            email="admin_root@example.com",
            password="password123",
        )
        self.staff_user = User.objects.create_user(
            username="staff_limited",
            email="staff@example.com",
            password="password123",
            is_staff=True,
        )
        view_group_perm = Permission.objects.get(codename="view_group")
        self.staff_user.user_permissions.add(view_group_perm)

    def test_default_sidebar_renders_without_grouped_navigation_assets(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertNotIn("grouped-navigation.css", html)
        self.assertNotIn("grouped-navigation.js", html)
        self.assertIn('id="admin-sidebar"', html)

    @override_settings(
        ADMINFLOW_NAVIGATION=[
            {
                "key": "iam",
                "label": "Identity <script>alert(1)</script>",
                "icon": "shield",
                "models": ["auth.Group", "auth.User"],
            }
        ]
    )
    def test_grouped_navigation_renders_escaped_labels_and_filters_unauthorized_models(self):
        # Staff user only has permission to view Group, not User
        self.client.force_login(self.staff_user)
        response = self.client.get("/admin/auth/group/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")

        self.assertIn("grouped-navigation.css", html)
        self.assertIn("grouped-navigation.js", html)
        self.assertIn('data-af-grouped-nav="true"', html)
        self.assertIn("Identity &lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn('href="/admin/auth/group/"', html)
        self.assertIn('aria-current="page"', html)
        # User changelist link is omitted for staff_limited
        self.assertNotIn('href="/admin/auth/user/"', html)

        # Direct endpoint access to User changelist remains protected by Django Admin (403)
        denied = self.client.get("/admin/auth/user/")
        self.assertEqual(denied.status_code, 403)

    def test_change_form_renders_single_toast_container_and_supports_hooks(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/auth/group/add/")
        self.assertEqual(response.status_code, 200)

        # Post invalid empty Group form to trigger validation error toast
        post_resp = self.client.post("/admin/auth/group/add/", data={"name": ""})
        self.assertEqual(post_resp.status_code, 200)
        html = post_resp.content.decode("utf-8")
        self.assertEqual(html.count('id="toast-container"'), 1)
        self.assertIn("Validation Error", html)

        # Verify current_history_version hook renders when supplied in context
        tpl = Template(
            '{% extends "admin/change_form.html" %}'
            '{% block extra_change_form_head %}<meta name="custom-widget-hook" content="ok">{% endblock %}'
        )
        rendered = tpl.render(
            Context(
                {
                    **post_resp.context_data,
                    "request": post_resp.wsgi_request,
                    "user": self.superuser,
                    "current_history_version": 7,
                }
            )
        )
        self.assertIn("Current version · v7", rendered)
        self.assertIn('<meta name="custom-widget-hook" content="ok">', rendered)

    def test_custom_user_model_without_email_or_username_fields_works(self):
        custom_user = SimpleNamespace(
            pk=99,
            is_authenticated=True,
            get_username=lambda: "identifier-99",
        )
        self.assertEqual(_user_display_label(custom_user), "identifier-99")

    def test_2fa_verify_view_redirects_cleanly_when_session_missing_or_expired(self):
        # Missing pending_2fa_user_id redirects to reverse('admin:login')
        resp = self.client.get("/admin/verify-2fa/")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "/admin/login/")

        # Expired session clears keys and redirects to login
        session = self.client.session
        session["pending_2fa_user_id"] = self.superuser.pk
        session["pending_2fa_created_at"] = time.time() - 1000
        session.save()

        resp_expired = self.client.get("/admin/verify-2fa/")
        self.assertEqual(resp_expired.status_code, 302)
        self.assertEqual(resp_expired["Location"], "/admin/login/")
        self.assertNotIn("pending_2fa_user_id", self.client.session)

    def test_grouped_navigation_js_behavior(self):
        js_test = r"""
        const assert = require('node:assert/strict');
        const fs = require('node:fs');
        const vm = require('node:vm');
        const source = fs.readFileSync('adminflow/static/adminflow/js/grouped-navigation.js', 'utf8');

        const root = {}, nested = {};
        const makeGroup = (key, parentElement, active = false) => ({
          dataset: { navKey: key },
          parentElement,
          open: active,
          listeners: {},
          hasAttribute: name => name === 'data-active' && active,
          addEventListener(name, cb) { this.listeners[name] = cb; }
        });
        const g1 = makeGroup('g1', root, false);
        const g2 = makeGroup('g2', root, true);
        const sub1 = makeGroup('sub1', nested, true);
        const sub2 = makeGroup('sub2', nested, false);
        const groups = [g1, g2, sub1, sub2];
        const nav = {
          setAttribute() {},
          querySelectorAll: sel => sel.startsWith('details') ? groups : []
        };
        const sidebar = {
          classList: { contains: () => false },
          querySelector: () => nav
        };
        const storage = new Map([['af-admin-nav:g1', 'open'], ['af-admin-nav:sub2', 'open']]);
        vm.runInNewContext(source, {
          document: {
            addEventListener: (_, cb) => cb(),
            getElementById: id => id === 'admin-sidebar' ? sidebar : null
          },
          sessionStorage: {
            getItem: k => storage.get(k),
            setItem: (k, v) => storage.set(k, v)
          }
        });
        assert.equal(g1.open, false);
        assert.equal(g2.open, true);
        assert.equal(sub1.open, true);
        assert.equal(sub2.open, false);

        g1.open = true;
        g1.listeners.toggle();
        assert.equal(g2.open, false);
        assert.equal(storage.get('af-admin-nav:g2'), 'closed');
        """
        proc = subprocess.run(
            ["node", "-e", js_test],
            cwd="/Users/edgar208/Desktop/Github/Django Pypi package/AdminFlow Package",
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)

