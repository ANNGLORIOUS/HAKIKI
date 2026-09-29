from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from cryptography.fernet import Fernet

from apps.accounts.models import User
from apps.core.utils import normalize_msisdn, parse_social, mask_value
from apps.listings.models import Page, PaymentIdentifier
from apps.listings.services import refresh_label
from apps.moderation.models import ModerationAction
from apps.submissions.models import CheckRequest, Evidence, Report, Vouch

KEY = Fernet.generate_key().decode()


class UtilsTests(TestCase):
    def test_msisdn_formats_match(self):
        for raw in ["0712345678", "712345678", "254712345678", "+254 712 345 678"]:
            self.assertEqual(normalize_msisdn(raw), "+254712345678")
        with self.assertRaises(ValueError):
            normalize_msisdn("12345")

    def test_handles_and_links_map_to_one_page(self):
        self.assertEqual(parse_social("tiktok", "https://www.tiktok.com/@ShopKE?lang=en"), "shopke")
        self.assertEqual(parse_social("tiktok", "@shopke"), "shopke")
        self.assertEqual(parse_social("instagram", "instagram.com/shopke/"), "shopke")
        with self.assertRaises(ValueError):
            parse_social("tiktok", "https://vm.tiktok.com/ZMabc/")
        with self.assertRaises(ValueError):
            parse_social("instagram", "https://tiktok.com/@shopke")

    def test_mask(self):
        self.assertEqual(mask_value("+254712345678"), "+254 *** 678")


@override_settings(FIELD_ENCRYPTION_KEY=KEY, REPORT_THRESHOLD=3)
class LabelTests(TestCase):
    def setUp(self):
        self.page = Page.objects.create(platform="instagram", handle="shopke")

    def _user(self, n):
        return User.objects.create_user(f"u{n}", f"u{n}@x.com", "pw", phone_verified=True, email_verified=True)

    def _report(self, user, status="published", evidence="supported"):
        r = Report.objects.create(reporter=user, page=self.page, category="non_delivery", description="x", status=status)
        Evidence.objects.create(report=r, file=ContentFile(b"x", "a.png"), status=evidence)
        return r

    def test_progression(self):
        self.assertEqual(refresh_label(self.page).public_label, "no_reports")
        CheckRequest.objects.create(page=self.page)
        self.assertEqual(refresh_label(self.page).public_label, "needs_checking")
        self._report(self._user(1), status="submitted", evidence="not_reviewed")
        self.assertEqual(refresh_label(self.page).public_label, "reports_review")
        # one published report is still not a negative label
        Report.objects.all().update(status="published")
        Evidence.objects.all().update(status="supported")
        self.assertEqual(refresh_label(self.page).public_label, "reports_review")
        self._report(self._user(2)); self._report(self._user(3))
        p = refresh_label(self.page)
        self.assertEqual(p.public_label, "reported_multiple")
        self.assertTrue(p.indexable)

    def test_same_reporter_counts_once(self):
        u = self._user(1)
        for _ in range(4):
            self._report(u)
        self.assertEqual(refresh_label(self.page).public_label, "reports_review")

    def test_dispute_overrides_and_history(self):
        r = self._report(self._user(1))
        r.status = "disputed"; r.save()
        self.assertEqual(refresh_label(self.page).public_label, "disputed")
        self.assertEqual(self.page.label_history.count(), 1)


@override_settings(FIELD_ENCRYPTION_KEY=KEY, HMAC_SECRET="s")
class PaymentTests(TestCase):
    def test_same_number_different_formats_links(self):
        a, c1 = PaymentIdentifier.get_or_create_from_raw("send_money", "0712345678", "JOHN DOE")
        b, c2 = PaymentIdentifier.get_or_create_from_raw("send_money", "+254 712 345 678")
        self.assertTrue(c1); self.assertFalse(c2); self.assertEqual(a.pk, b.pk)
        self.assertEqual(a.reveal(), "+254712345678")
        self.assertNotIn("712345678", a.masked)
        self.assertEqual(PaymentIdentifier.hash_for("send_money", "0712345678"), a.value_hash)


class AuditTests(TestCase):
    def test_immutable(self):
        u = User.objects.create_user("m", "m@x.com", "pw")
        a = ModerationAction.objects.create(actor=u, action="x", target_type="report", target_id=1)
        with self.assertRaises(PermissionError):
            a.reason = "edit"; a.save()
        with self.assertRaises(PermissionError):
            a.delete()
