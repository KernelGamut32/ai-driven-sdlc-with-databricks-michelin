"""Code tests for the business rules in plain Python (o2i.rules).

These tests need Python and nothing else: no Spark, no connection, no installed package.
Run them with:  python tools/run_tests.py     or:  python -m unittest

Every expected value comes from the business contract (docs/business_contract.md) or from a hand
calculation. No expected value was produced by the code under test.
"""
import unittest
from decimal import Decimal as D

from o2i import rules


class StatusTests(unittest.TestCase):
    """Rule R2: the status is compared trimmed and in upper case."""

    def test_normalize_status_trims_and_uppercases(self):
        cases = [("POSTED", "POSTED"), ("Posted ", "POSTED"), (" posted", "POSTED"), ("draft", "DRAFT"),
                 ("   ", ""), (None, None)]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(rules.normalize_status(raw), expected)

    def test_posted_in_any_case_and_with_spaces_is_posted(self):
        for raw in ("POSTED", "Posted", "posted", "POSTED ", " POSTED", "Posted "):
            with self.subTest(raw=raw):
                self.assertEqual(rules.classify_status(raw), "POSTED")

    def test_draft_and_cancelled_are_not_posted(self):
        for raw in ("DRAFT", "draft", "Draft ", "CANCELLED", "Cancelled", "cancelled"):
            with self.subTest(raw=raw):
                self.assertEqual(rules.classify_status(raw), "NOT_POSTED")

    def test_any_other_value_is_unexpected(self):
        for raw in ("PENDING", "BOOKED", "ON HOLD", "PST", "POSTED X", "", "   ", None):
            with self.subTest(raw=raw):
                self.assertEqual(rules.classify_status(raw), "UNEXPECTED")


class AmountTests(unittest.TestCase):
    """The derived amounts: decimal arithmetic, rounding half up, signs preserved."""

    def test_tax_without_a_rate_is_zero(self):
        self.assertEqual(rules.tax_amount(D("793.04"), None), D("0.00"))
        self.assertEqual(rules.gross_amount(D("793.04"), None), D("793.04"))

    def test_a_rate_of_zero_is_a_rate(self):
        self.assertEqual(rules.gross_amount(D("4510.70"), D("0.0000")), D("4510.70"))

    def test_gross_amount_of_a_credit_keeps_its_sign(self):
        self.assertEqual(rules.gross_amount(D("-367.15"), D("0.2000")), D("-440.58"))

    def test_tax_rounds_half_up_on_a_tie(self):
        self.assertEqual(rules.tax_amount(D("3.00"), D("0.0550")), D("0.17"))            # 0.165
        self.assertEqual(rules.tax_amount(D("0.50"), D("0.2100")), D("0.11"))            # 0.105
        self.assertEqual(rules.gross_amount(D("3.00"), D("0.0550")), D("3.17"))

    def test_tax_of_a_credit_rounds_away_from_zero_on_a_tie(self):
        self.assertEqual(rules.tax_amount(D("-3.00"), D("0.0550")), D("-0.17"))          # -0.165
        self.assertEqual(rules.gross_amount(D("-3.00"), D("0.0550")), D("-3.17"))

    def test_amounts_have_two_decimals(self):
        for value in (rules.tax_amount(D("367.15"), D("0.2000")), rules.gross_amount(D("367.15"), None)):
            with self.subTest(value=value):
                self.assertEqual(value.as_tuple().exponent, -2)

    def test_money_is_never_a_float(self):
        with self.assertRaises(TypeError):
            rules.gross_amount(367.15, D("0.2000"))
        with self.assertRaises(TypeError):
            rules.tax_amount(D("367.15"), 0.2)


if __name__ == "__main__":
    unittest.main()
