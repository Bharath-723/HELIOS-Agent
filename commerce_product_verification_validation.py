"""
commerce_product_verification_validation.py — HELIOS Product Verification & Eligibility Test Suite
===================================================================================================
Runs 10 explicit unit & integration tests validating:
1. Croma /search URL classified as MERCHANT_SEARCH_PAGE
2. Search URL cannot become DIRECT_VERIFIED_PRICE
3. Search URL cannot become PAYMENT_ELIGIBLE
4. Product link cannot open search URL
5. Search-result price remains SEARCH_RESULT_PRICE
6. Direct product page upgrades price to DIRECT_VERIFIED_PRICE
7. Purchase request requires direct product verification
8. Failed verification blocks payment
9. Successful verification allows transaction review
10. Existing Razorpay TransactionGuard remains unchanged
"""

import sys
import unittest
import logging
from unittest.mock import MagicMock, patch

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.WARNING)

from core.commerce.search.result_classifier import ResultClassifier
from core.commerce.commerce_models import ProductCandidate, CommerceContext, CommerceIntent, CommerceIntentCategory, CommerceState
from core.commerce.product_verifier import ProductVerifier
from core.commerce.commerce_orchestrator import CommerceOrchestrator
from core.payments.transaction_guard import TransactionGuard


class CommerceProductVerificationValidationSuite(unittest.TestCase):

    # 1. Croma /search URL classified as MERCHANT_SEARCH_PAGE
    def test_01_croma_search_url_classification(self):
        url = "https://www.croma.com/search?q=Portronics%20Bubble%203.0%20wireless%20keyboard"
        classification = ResultClassifier.classify(url, "Keyboards", "Search result")
        self.assertEqual(classification, "MERCHANT_SEARCH_PAGE")

    # 2. Search URL cannot become DIRECT_VERIFIED_PRICE
    def test_02_search_url_cannot_become_direct_verified_price(self):
        cand = ProductCandidate(
            candidate_id="c_search",
            name="Portronics Bubble 3.0",
            description="Keyboard",
            price_inr=999.0,
            merchant="Croma",
            source_url="https://www.croma.com/search?q=Portronics%20Bubble%203.0"
        )
        updated, status = ProductVerifier.verify_candidate_url(cand)
        self.assertNotEqual(status, "DIRECT_PAGE_VERIFIED")
        self.assertEqual(updated.price_evidence_type, "SEARCH_RESULT_PRICE")

    # 3. Search URL cannot become PAYMENT_ELIGIBLE
    def test_03_search_url_cannot_become_payment_eligible(self):
        cand = ProductCandidate(
            candidate_id="c_search",
            name="Portronics Bubble 3.0",
            description="Keyboard",
            price_inr=999.0,
            merchant="Croma",
            source_url="https://www.croma.com/search?q=Portronics%20Bubble%203.0"
        )
        updated, _ = ProductVerifier.verify_candidate_url(cand)
        self.assertFalse(updated.payment_eligible)

    # 4. Product link cannot open search URL
    def test_04_product_link_cannot_open_search_url(self):
        cand = ProductCandidate(
            candidate_id="c_search",
            name="Portronics Bubble 3.0",
            description="Keyboard",
            price_inr=999.0,
            merchant="Croma",
            source_url="https://www.croma.com/search?q=Portronics%20Bubble%203.0",
            classification="MERCHANT_SEARCH_PAGE"
        )
        dict_rep = cand.to_dict()
        self.assertIsNone(dict_rep.get("direct_product_url"))

    # 5. Search-result price remains SEARCH_RESULT_PRICE
    def test_05_search_result_remains_search_result_price(self):
        cand = ProductCandidate(
            candidate_id="c_search",
            name="Portronics Bubble 3.0",
            description="Keyboard",
            price_inr=999.0,
            merchant="Croma",
            source_url="https://www.croma.com/search?q=Portronics%20Bubble%203.0"
        )
        self.assertEqual(cand.price_evidence_type, "SEARCH_RESULT_PRICE")

    # 6. Direct product page upgrades price to DIRECT_VERIFIED_PRICE
    @patch("requests.get")
    def test_06_direct_product_page_upgrades_price(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '''
        <html>
          <head>
            <script type="application/ld+json">
            {
              "@type": "Product",
              "name": "Portronics Bubble 3.0 Wireless Keyboard",
              "offers": {
                "@type": "Offer",
                "price": "999.00",
                "priceCurrency": "INR"
              }
            }
            </script>
          </head>
        </html>
        '''
        mock_get.return_value = mock_resp

        cand = ProductCandidate(
            candidate_id="c_direct",
            name="Portronics Bubble 3.0",
            description="Keyboard",
            price_inr=999.0,
            merchant="Croma",
            source_url="https://www.croma.com/p/portronics-bubble-3-0-keyboard/p/270100"
        )
        updated, status = ProductVerifier.verify_candidate_url(cand, budget_limit_inr=2000.0)
        self.assertEqual(status, "DIRECT_PAGE_VERIFIED")
        self.assertEqual(updated.price_evidence_type, "STRUCTURED_DATA_PRICE")
        self.assertTrue(updated.payment_eligible)

    # 7. Purchase request requires direct product verification
    def test_07_purchase_request_requires_direct_verification(self):
        orch = CommerceOrchestrator()

        # Mock candidate returning search URL
        mock_cand = ProductCandidate(
            candidate_id="c_mock",
            name="Portronics Bubble 3.0",
            description="Keyboard",
            price_inr=999.0,
            merchant="Croma",
            source_url="https://www.croma.com/search?q=Portronics%20Bubble%203.0"
        )

        with patch("core.commerce.commerce_researcher.CommerceResearcher.research") as mock_research:
            mock_research.return_value = [mock_cand]
            res = orch.process_commerce_request("Find me a good wireless keyboard under ₹2000 and buy it for me")
            self.assertFalse(res["success"])
            self.assertEqual(res["type"], "VERIFICATION_FAILED")
            self.assertIn("search page rather than a directly verifiable product page", res["error_message"])

    # 8. Failed verification blocks payment
    def test_08_failed_verification_blocks_payment(self):
        orch = CommerceOrchestrator()
        cand = ProductCandidate(
            candidate_id="c_mock",
            name="Portronics Bubble 3.0",
            description="Keyboard",
            price_inr=999.0,
            merchant="Croma",
            source_url="https://www.croma.com/search?q=Portronics"
        )
        with patch("core.commerce.commerce_researcher.CommerceResearcher.research") as mock_research:
            mock_research.return_value = [cand]
            res = orch.process_commerce_request("Buy keyboard for ₹999")
            self.assertFalse(res["success"])
            self.assertNotIn("payment_prepared", res)

    # 9. Successful verification allows transaction review
    @patch("requests.get")
    def test_09_successful_verification_allows_transaction_review(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '''
        <script type="application/ld+json">
        {
          "@type": "Product",
          "name": "Portronics Bubble 3.0 Wireless Keyboard",
          "offers": { "@type": "Offer", "price": "999.00", "priceCurrency": "INR" }
        }
        </script>
        '''
        mock_get.return_value = mock_resp

        orch = CommerceOrchestrator()
        cand = ProductCandidate(
            candidate_id="c_direct",
            name="Portronics Bubble 3.0",
            description="Keyboard",
            price_inr=999.0,
            merchant="Croma",
            source_url="https://www.croma.com/p/portronics-bubble-3-0-keyboard/p/270100"
        )
        with patch("core.commerce.commerce_researcher.CommerceResearcher.research") as mock_research:
            mock_research.return_value = [cand]
            res = orch.process_commerce_request("Find wireless keyboard under ₹2000 and buy it")
            self.assertTrue(res["success"])
            self.assertEqual(res["type"], "COMMERCE_TRANSACTION_READY")

    # 10. Existing Razorpay TransactionGuard remains unchanged
    def test_10_razorpay_transaction_guard_unchanged(self):
        tg = TransactionGuard()
        self.assertTrue(hasattr(tg, "can_create_order"))
        self.assertTrue(hasattr(tg, "can_verify_payment"))


if __name__ == "__main__":
    print("=" * 60)
    print("HELIOS Product Verification & Payment Eligibility Validation Suite")
    print("=" * 60)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unittest.makeSuite(CommerceProductVerificationValidationSuite))
    if not result.wasSuccessful():
        sys.exit(1)
