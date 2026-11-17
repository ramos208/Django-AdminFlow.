# AdminFlow Django Admin Package
from importlib import metadata

try:
    __version__ = metadata.version("django-adminflow")
except metadata.PackageNotFoundError:
    __version__ = "1.0.15"
