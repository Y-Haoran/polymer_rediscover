from pathlib import Path
import tempfile
import unittest
import zipfile

from polymer_rediscover.dailymed import parse_label_directory, parse_label_xml, resolve_current_monthly_update_url


SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<document xmlns="urn:hl7-org:v3">
  <id root="doc-1" />
  <title>Demo Product</title>
  <effectiveTime value="20260422" />
  <setId root="set-123" />
  <versionNumber value="3" />
  <component>
    <structuredBody>
      <component>
        <section>
          <subject>
            <manufacturedProduct>
              <manufacturedProduct>
                <name>Demo Product Name</name>
                <formCode displayName="TABLET, FILM COATED" />
                <ingredient classCode="ACTIB">
                  <ingredientSubstance>
                    <code code="APIUNII" />
                    <name>Demo API</name>
                  </ingredientSubstance>
                  <quantity>
                    <numerator value="10" unit="mg" />
                    <denominator value="1" unit="1" />
                  </quantity>
                </ingredient>
                <ingredient classCode="IACT">
                  <ingredientSubstance>
                    <code code="POVUNII" />
                    <name>POVIDONE</name>
                  </ingredientSubstance>
                </ingredient>
              </manufacturedProduct>
              <consumedIn>
                <substanceAdministration>
                  <routeCode displayName="ORAL" />
                </substanceAdministration>
              </consumedIn>
            </manufacturedProduct>
          </subject>
        </section>
      </component>
    </structuredBody>
  </component>
</document>
"""


class DailyMedTests(unittest.TestCase):
    def test_resolve_current_monthly_update_url(self) -> None:
        html = '<a href="https://dailymed-data.nlm.nih.gov/public-release-files/dm_spl_monthly_update_mar2026.zip">x</a>'
        self.assertEqual(
            resolve_current_monthly_update_url(html),
            "https://dailymed-data.nlm.nih.gov/public-release-files/dm_spl_monthly_update_mar2026.zip",
        )

    def test_parse_label_xml(self) -> None:
        product, ingredients = parse_label_xml(SAMPLE_XML.encode("utf-8"), source_name="demo.xml")
        self.assertEqual(product["setid"], "set-123")
        self.assertEqual(product["route_normalized"], "oral")
        self.assertEqual(product["dosage_form_category"], "tablet")
        roles = {row["ingredient_role"] for row in ingredients}
        self.assertEqual(roles, {"active", "inactive"})

    def test_parse_label_directory_reads_zip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp_dir = Path(tmp_dir_name)
            zip_path = tmp_dir / "demo.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("demo.xml", SAMPLE_XML)
            products, ingredients = parse_label_directory(tmp_dir)
            self.assertEqual(len(products), 1)
            self.assertEqual(len(ingredients), 2)


if __name__ == "__main__":
    unittest.main()
