"""Command-line entrypoint for the starter project."""

from __future__ import annotations

from .project import DEFAULT_CONTEXTS, PRIMARY_DATASETS, PROJECT_NAME, PROJECT_SUMMARY


def build_summary() -> str:
    contexts = ", ".join(DEFAULT_CONTEXTS)
    datasets = "\n".join(f"- {name}" for name in PRIMARY_DATASETS)
    return (
        f"{PROJECT_NAME}\n"
        f"{PROJECT_SUMMARY}\n\n"
        f"Default contexts: {contexts}\n\n"
        f"Primary datasets:\n{datasets}\n"
    )


def main() -> None:
    print(build_summary())


if __name__ == "__main__":
    main()
