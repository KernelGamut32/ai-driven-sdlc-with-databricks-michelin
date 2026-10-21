"""Code tests on the approved fixture, without Spark.

tests/fixtures/fixture_expected_amounts.csv holds 22 invoice lines of the fixture with their
hand-calculated tax and gross amounts. The expected amounts were calculated by hand from the
business contract and validated by the instructor. They are the oracle: never edit an expected
value to make a test pass.
"""
import unittest

from o2i import rules
from tests import fixture_data


class FixtureAmountTests(unittest.TestCase):

    def test_amounts_equal_the_hand_calculation(self):
        amounts = fixture_data.load("fixture_expected_amounts")
        self.assertEqual(len(amounts), 22)
        for a in amounts:
            with self.subTest(case=a["CaseID"], row=a["RawRowID"]):
                self.assertEqual(rules.tax_amount(a["NetAmount"], a["TaxRate"]), a["ExpectedTaxAmount"])
                self.assertEqual(rules.gross_amount(a["NetAmount"], a["TaxRate"]), a["ExpectedGrossAmount"])


if __name__ == "__main__":
    unittest.main()
