"""Project metadata used by the starter CLI and docs."""

PROJECT_NAME = "polymer_rediscover"

PROJECT_SUMMARY = (
    "FDA-aware ranking of polymer excipients for oral solid dosage forms."
)

DEFAULT_CONTEXTS = (
    "oral tablet",
    "oral capsule",
    "oral solid dispersion carrier",
)

PRIMARY_DATASETS = (
    "PI1M or other large polymer corpora for representation learning",
    "FDA Inactive Ingredient Database for approved-use context",
    "DailyMed SPL for API and inactive ingredient co-occurrence",
)
