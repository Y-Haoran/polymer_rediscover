"""Download and parse DailyMed SPL XML labels."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
import zipfile

from .normalization import dosage_form_category, normalize_dosage_form, normalize_route, normalize_text
from .tabular import write_tsv

DAILYMED_METADATA_URL = (
    "https://dailymed-data.nlm.nih.gov/public-release-files/dm_spl_zip_files_meta_data.zip"
)
DAILYMED_LABELS_PAGE = "https://dailymed.nlm.nih.gov/dailymed/spl-resources-all-drug-labels.cfm"
DAILYMED_SETID_ZIP_URL = "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?setid={setid}&type=zip"

DEFAULT_METADATA_DIR = Path("data/dailymed/raw")
DEFAULT_LABEL_DIR = Path("data/dailymed/raw/labels")
DEFAULT_PROCESSED_DIR = Path("data/dailymed/processed")
NS = {"hl7": "urn:hl7-org:v3"}


def fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=120) as response:
        return response.read()


def download_metadata_zip(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / "dm_spl_zip_files_meta_data.zip"
    destination.write_bytes(fetch_bytes(DAILYMED_METADATA_URL))
    return destination


def resolve_current_monthly_update_url(page_html: str) -> str:
    match = re.search(
        r'href="(https://dailymed-data\.nlm\.nih\.gov/[^"]*dm_spl_monthly_update_[^"]+\.zip)"',
        page_html,
        re.I,
    )
    if not match:
        raise ValueError("could not find current DailyMed monthly update link")
    return match.group(1)


def download_current_monthly_update(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    page_html = fetch_text(DAILYMED_LABELS_PAGE)
    url = resolve_current_monthly_update_url(page_html)
    destination = output_dir / Path(url).name
    destination.write_bytes(fetch_bytes(url))
    return destination


def download_label_zip(setid: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    url = DAILYMED_SETID_ZIP_URL.format(setid=setid)
    destination = output_dir / f"{setid}.zip"
    destination.write_bytes(fetch_bytes(url))
    return destination


def fetch_setids_from_file(setid_file: Path, output_dir: Path, limit: int = 0) -> list[Path]:
    setids = [
        line.strip()
        for line in setid_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if limit > 0:
        setids = setids[:limit]
    return [download_label_zip(setid, output_dir) for setid in setids]


def xml_payload_from_file(path: Path) -> bytes:
    if path.suffix.lower() == ".xml":
        return path.read_bytes()
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if name.lower().endswith(".xml"):
                    return archive.read(name)
        raise FileNotFoundError(f"no XML found inside {path}")
    raise ValueError(f"unsupported DailyMed input file: {path}")


def text_of(element: ET.Element | None) -> str:
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def attr_of(element: ET.Element | None, attribute: str) -> str:
    if element is None:
        return ""
    return element.attrib.get(attribute, "").strip()


def parse_label_xml(xml_bytes: bytes, source_name: str = "") -> tuple[dict[str, str], list[dict[str, str]]]:
    root = ET.fromstring(xml_bytes)
    setid = attr_of(root.find("./hl7:setId", NS), "root")
    version_number = attr_of(root.find("./hl7:versionNumber", NS), "value")
    effective_time = attr_of(root.find("./hl7:effectiveTime", NS), "value")
    title = text_of(root.find("./hl7:title", NS))

    product_node = root.find(
        ".//hl7:section/hl7:subject/hl7:manufacturedProduct/hl7:manufacturedProduct",
        NS,
    )
    route_node = root.find(
        ".//hl7:section/hl7:subject/hl7:manufacturedProduct/"
        "hl7:consumedIn/hl7:substanceAdministration/hl7:routeCode",
        NS,
    )
    form_node = product_node.find("./hl7:formCode", NS) if product_node is not None else None

    route = attr_of(route_node, "displayName")
    dosage_form = attr_of(form_node, "displayName")
    product_name = text_of(product_node.find("./hl7:name", NS) if product_node is not None else None)

    product_row = {
        "setid": setid,
        "version_number": version_number,
        "effective_time": effective_time,
        "title": title,
        "product_name": product_name,
        "route": route,
        "route_normalized": normalize_route(route),
        "dosage_form": dosage_form,
        "dosage_form_normalized": normalize_dosage_form(dosage_form),
        "dosage_form_category": dosage_form_category(dosage_form),
        "source_file": source_name,
    }

    ingredient_rows: list[dict[str, str]] = []
    if product_node is not None:
        for ingredient in product_node.findall("./hl7:ingredient", NS):
            ingredient_class = ingredient.attrib.get("classCode", "").strip()
            role = ingredient_role_from_class_code(ingredient_class)
            if role == "other":
                continue
            substance = ingredient.find("./hl7:ingredientSubstance", NS)
            quantity_numerator = ingredient.find("./hl7:quantity/hl7:numerator", NS)
            quantity_denominator = ingredient.find("./hl7:quantity/hl7:denominator", NS)
            ingredient_rows.append(
                {
                    "setid": setid,
                    "ingredient_role": role,
                    "ingredient_class_code": ingredient_class,
                    "ingredient_name": text_of(substance.find("./hl7:name", NS) if substance is not None else None),
                    "ingredient_name_normalized": normalize_text(
                        text_of(substance.find("./hl7:name", NS) if substance is not None else None)
                    ),
                    "unii": attr_of(substance.find("./hl7:code", NS) if substance is not None else None, "code"),
                    "strength_numerator_value": attr_of(quantity_numerator, "value"),
                    "strength_numerator_unit": attr_of(quantity_numerator, "unit"),
                    "strength_denominator_value": attr_of(quantity_denominator, "value"),
                    "strength_denominator_unit": attr_of(quantity_denominator, "unit"),
                    "source_file": source_name,
                }
            )

    return product_row, ingredient_rows


def ingredient_role_from_class_code(class_code: str) -> str:
    if class_code.startswith("ACT"):
        return "active"
    if class_code == "IACT":
        return "inactive"
    return "other"


def best_product_version(left: dict[str, str], right: dict[str, str]) -> dict[str, str]:
    left_key = (safe_int(left.get("version_number", "")), left.get("effective_time", ""))
    right_key = (safe_int(right.get("version_number", "")), right.get("effective_time", ""))
    return right if right_key > left_key else left


def safe_int(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def parse_label_directory(input_dir: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    product_by_setid: dict[str, dict[str, str]] = {}
    ingredients_by_setid: dict[str, list[dict[str, str]]] = {}
    for path in sorted(input_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".zip", ".xml"}:
            continue
        product, ingredients = parse_label_xml(xml_payload_from_file(path), source_name=path.name)
        setid = product["setid"]
        if not setid:
            continue
        current = product_by_setid.get(setid)
        if current is None:
            product_by_setid[setid] = product
            ingredients_by_setid[setid] = ingredients
            continue
        chosen = best_product_version(current, product)
        if chosen is product:
            product_by_setid[setid] = product
            ingredients_by_setid[setid] = ingredients
    products = [product_by_setid[setid] for setid in sorted(product_by_setid)]
    ingredients = [
        ingredient
        for setid in sorted(ingredients_by_setid)
        for ingredient in ingredients_by_setid[setid]
    ]
    return products, ingredients


def write_parsed_tables(
    products: list[dict[str, str]],
    ingredients: list[dict[str, str]],
    processed_dir: Path,
) -> tuple[Path, Path]:
    products_path = processed_dir / "dailymed_products.tsv"
    ingredients_path = processed_dir / "dailymed_ingredients.tsv"
    write_tsv(
        products_path,
        products,
        [
            "setid",
            "version_number",
            "effective_time",
            "title",
            "product_name",
            "route",
            "route_normalized",
            "dosage_form",
            "dosage_form_normalized",
            "dosage_form_category",
            "source_file",
        ],
    )
    write_tsv(
        ingredients_path,
        ingredients,
        [
            "setid",
            "ingredient_role",
            "ingredient_class_code",
            "ingredient_name",
            "ingredient_name_normalized",
            "unii",
            "strength_numerator_value",
            "strength_numerator_unit",
            "strength_denominator_value",
            "strength_denominator_unit",
            "source_file",
        ],
    )
    return products_path, ingredients_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DailyMed download and parsing tools.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    metadata_parser = subparsers.add_parser("download-metadata", help="Download DailyMed metadata zip.")
    metadata_parser.add_argument("--output-dir", default=str(DEFAULT_METADATA_DIR))

    monthly_parser = subparsers.add_parser(
        "download-current-monthly",
        help="Download the current DailyMed monthly update ZIP.",
    )
    monthly_parser.add_argument("--output-dir", default=str(DEFAULT_METADATA_DIR))

    fetch_parser = subparsers.add_parser("fetch-setids", help="Download label ZIPs for a list of setids.")
    fetch_parser.add_argument("--setid-file", required=True)
    fetch_parser.add_argument("--output-dir", default=str(DEFAULT_LABEL_DIR))
    fetch_parser.add_argument("--limit", type=int, default=0)

    parse_parser = subparsers.add_parser("parse", help="Parse DailyMed XML or ZIP label files.")
    parse_parser.add_argument("--input-dir", default=str(DEFAULT_LABEL_DIR))
    parse_parser.add_argument("--processed-dir", default=str(DEFAULT_PROCESSED_DIR))

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "download-metadata":
        path = download_metadata_zip(Path(args.output_dir))
        print(f"metadata_zip={path}")
        return

    if args.command == "download-current-monthly":
        path = download_current_monthly_update(Path(args.output_dir))
        print(f"monthly_zip={path}")
        return

    if args.command == "fetch-setids":
        paths = fetch_setids_from_file(Path(args.setid_file), Path(args.output_dir), limit=args.limit)
        print(f"downloaded_count={len(paths)}")
        for path in paths:
            print(path)
        return

    products, ingredients = parse_label_directory(Path(args.input_dir))
    products_path, ingredients_path = write_parsed_tables(products, ingredients, Path(args.processed_dir))
    print(f"products={products_path}")
    print(f"ingredients={ingredients_path}")


if __name__ == "__main__":
    main()
