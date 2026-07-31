"""EmBody protocol codec."""

__all__ = ["__version__"]


def __getattr__(name: str) -> str:
    """Resolve __version__ lazily (PEP 562).

    importlib.metadata pulls in the email parser and costs ~25ms at import time, which
    every consumer of this library would otherwise pay just to import a codec. Doing it
    here also keeps `version` and `PackageNotFoundError` out of the package namespace.
    """
    if name == "__version__":
        # Deferred on purpose - see the docstring above.
        from importlib.metadata import PackageNotFoundError  # noqa: PLC0415
        from importlib.metadata import version  # noqa: PLC0415

        try:
            return version("embody-codec")
        except PackageNotFoundError:  # pragma: no cover - only when running uninstalled
            return "unknown"
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted([*globals(), "__version__"])
