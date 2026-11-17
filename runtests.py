#!/usr/bin/env python3
import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner


def configure():
    if settings.configured:
        return
    settings.configure(
        DEBUG=True,
        SECRET_KEY="adminflow-test-secret-key",
        ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
        INSTALLED_APPS=[
            "adminflow",
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "simple_history",
        ],
        MIDDLEWARE=[
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
            "simple_history.middleware.HistoryRequestMiddleware",
        ],
        ROOT_URLCONF="tests.test_adminflow",
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [],
                "APP_DIRS": True,
                "OPTIONS": {
                    "context_processors": [
                        "django.template.context_processors.debug",
                        "django.template.context_processors.request",
                        "django.contrib.auth.context_processors.auth",
                        "django.contrib.messages.context_processors.messages",
                        "adminflow.context_processors.adminflow_settings",
                    ],
                },
            },
        ],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        STATIC_URL="/static/",
        MEDIA_URL="/media/",
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    )


def main():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    sibling_history = os.path.join(os.path.dirname(repo_root), "django-simple-history-relation")
    if os.path.isdir(sibling_history) and sibling_history not in sys.path:
        sys.path.insert(0, sibling_history)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    configure()
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2)
    failures = test_runner.run_tests(["tests"])
    sys.exit(bool(failures))


if __name__ == "__main__":
    main()

