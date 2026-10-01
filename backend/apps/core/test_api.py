import io
import tempfile
from unittest.mock import patch

from cryptography.fernet import Fernet
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.listings.models import Page
from apps.moderation.models import Dispute, ModerationAction
from apps.submissions.models import Evidence, Report

KEY = Fernet.generate_key().decode()
MEDIA = tempfile.mkdtemp()


def png(color=(200, 0, 0)):
    b = io.BytesIO()
    Image.new("RGB", (60, 60), color).save(b, "PNG")
    return b.getvalue()


def upload(name="proof.png", data=None):
    return SimpleUploadedFile(name, data or png(), content_type="image/png")


@override_settings(FIELD_ENCRYPTION_KEY=KEY, HMAC_SECRET="s", MEDIA_ROOT=MEDIA, REPORT_THRESHOLD=3)
class ApiBase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from config.celery import app
        app.conf.task_always_eager = True
        app.conf.task_eager_propagates = True

    def setUp(self):
        cache.clear()
        self.n = 0

    def user(self, verified=True, **kw):
        self.n += 1
        return User.objects.create_user("u%d@x.com" % self.n, "u%d@x.com" % self.n, "pw12345!x",
                                        phone_verified=verified, email_verified=verified, **kw)

    def client_for(self, user=None):
        c = APIClient()
        if user:
            c.force_authenticate(user)
        return c

    def report(self, user, handle="shopke", number="0712345678", **extra):
        data = {"platform": "instagram", "handle": handle, "category": "non_delivery",
                "description": "I paid 3000 and the seller blocked me after payment.",
                "payment_type": "send_money", "payment_value": number, "registered_name": "JOHN DOE",
                "files": upload(), "kinds": "mpesa_message"}
        data.update(extra)
        return self.client_for(user).post("/api/reports/", data, format="multipart")


class AuthTests(ApiBase):
    def test_private_endpoints_return_401_when_logged_out(self):
        c = self.client_for()
        for path in ["/api/auth/me/", "/api/me/reports/"]:
            self.assertEqual(c.get(path).status_code, 401, path)
        self.assertEqual(c.get("/api/search/", {"q": "@x"}).status_code, 200)  # public stays public
        self.assertEqual(c.get("/api/pages/instagram/x/").status_code, 200)

    def test_register_verify_email_and_phone(self):
        c = APIClient()
        with patch("apps.accounts.views.deliver") as d:
            r = c.post("/api/auth/register/", {"email": "A@X.com", "password": "Str0ng-pass-99"}, format="json")
            self.assertEqual(r.status_code, 201)
            code = d.call_args[0][2]
        c.credentials(HTTP_AUTHORIZATION="Token " + r.data["token"])
        self.assertEqual(c.post("/api/auth/email/verify/", {"code": "000000"}).status_code, 400)
        self.assertTrue(c.post("/api/auth/email/verify/", {"code": code}).data["email_verified"])
        with patch("apps.accounts.views.deliver") as d:
            c.post("/api/auth/phone/send/", {"phone": "0712 345 678"}, format="json")
            self.assertEqual(d.call_args[0][1], "+254712345678")
            pcode = d.call_args[0][2]
        me = c.post("/api/auth/phone/verify/", {"code": pcode}).data
        self.assertTrue(me["is_verified_reporter"])
        self.assertNotIn("712345678", str(me))  # phone is masked in API output
        self.assertEqual(c.post("/api/auth/login/", {"email": "a@x.com", "password": "Str0ng-pass-99"}, format="json").status_code, 200)
        self.assertEqual(c.post("/api/auth/login/", {"email": "a@x.com", "password": "nope"}, format="json").status_code, 400)

    def test_code_locks_after_five_wrong_guesses(self):
        u = self.user(verified=False)
        c = self.client_for(u)
        with patch("apps.accounts.views.deliver") as d:
            c.post("/api/auth/email/send/")
            code = d.call_args[0][2]
        wrong = "111111" if code != "111111" else "222222"
        for _ in range(5):
            c.post("/api/auth/email/verify/", {"code": wrong})
        self.assertEqual(c.post("/api/auth/email/verify/", {"code": code}).status_code, 400)


class ReportTests(ApiBase):
    def test_unverified_user_blocked(self):
        self.assertEqual(self.report(self.user(verified=False)).status_code, 403)
        self.assertEqual(self.client_for().post("/api/reports/", {}).status_code, 401)

    def test_create_report_and_screening(self):
        u = self.user()
        r = self.report(u)
        self.assertEqual(r.status_code, 201, r.data)
        rep = Report.objects.get()
        self.assertEqual(rep.status, "under_review")  # screened, never auto-published
        self.assertEqual(rep.page.handle, "shopke")
        ev = rep.evidence.get()
        self.assertNotIn("proof", ev.file.name)  # original file name not kept
        self.assertTrue(ModerationAction.objects.filter(action="report.screened").exists())
        # a single report never makes a negative label
        self.assertEqual(rep.page.public_label, "reports_review")
        # tracking
        mine = self.client_for(u).get("/api/me/reports/").data
        self.assertEqual(mine[0]["status_text"], "Under review by a moderator")

    def test_duplicate_and_bad_files(self):
        u = self.user()
        self.assertEqual(self.report(u).status_code, 201)
        self.assertEqual(self.report(u).status_code, 400)  # same page again
        bad = SimpleUploadedFile("evil.png", b"<script>alert(1)</script>", content_type="image/png")
        r = self.report(u, handle="other", files=bad)
        self.assertEqual(r.status_code, 400)
        self.assertFalse(Page.objects.filter(handle="other").exists())  # nothing saved on failure

    def test_exif_stripped(self):
        exif = Image.Exif()
        exif[0x010F] = "SecretCamera"
        b = io.BytesIO()
        Image.new("RGB", (40, 40), (1, 2, 3)).save(b, "JPEG", exif=exif.tobytes())
        u = self.user()
        self.assertEqual(self.report(u, files=SimpleUploadedFile("p.jpg", b.getvalue(), content_type="image/jpeg")).status_code, 201)
        stored = Image.open(Evidence.objects.get().file.path)
        self.assertEqual(len(stored.getexif()), 0)

    def test_link_and_handle_resolve_to_same_page(self):
        self.report(self.user(), handle="https://www.instagram.com/ShopKE/?igsh=abc")
        self.report(self.user(), handle="@shopke")
        self.assertEqual(Page.objects.count(), 1)
        self.assertEqual(Report.objects.count(), 2)

    def test_daily_limit(self):
        u = self.user()
        for i in range(5):
            self.assertEqual(self.report(u, handle="shop%d" % i, number="071234567%d" % i).status_code, 201)
        self.assertEqual(self.report(u, handle="shop9").status_code, 429)


class SearchTests(ApiBase):
    def publish_three(self):
        for i in range(3):
            self.report(self.user(), number="0712345678" if i else "+254 712 345 678")
        Report.objects.update(status="published")
        Evidence.objects.update(status="supported")
        from apps.listings.services import refresh_label
        refresh_label(Page.objects.get(), reason="test")

    def test_unknown_page_and_number(self):
        c = self.client_for()
        r = c.get("/api/search/", {"q": "@nobody"}).data
        self.assertFalse(r["found"]); self.assertTrue(r["safety_tips"])
        r = c.get("/api/search/", {"q": "0799999999"}).data
        self.assertFalse(r["matched"])

    def test_pending_reports_not_counted_publicly(self):
        self.report(self.user())
        c = self.client_for()
        self.assertFalse(c.get("/api/search/", {"q": "0712345678"}).data["matched"])
        page = c.get("/api/pages/instagram/shopke/").data
        self.assertEqual(page["reports_published"], 0)
        self.assertEqual(page["label"], "reports_review")
        self.assertFalse(page["indexable"])

    def test_published_reports_and_number_match_in_any_format(self):
        self.publish_three()
        c = self.client_for()
        for q in ["0712345678", "+254712345678", "254 712 345 678", "712345678"]:
            r = c.get("/api/search/", {"q": q}).data
            self.assertTrue(r["matched"], q)
            self.assertEqual((r["report_count"], r["page_count"]), (3, 1))
        page = c.get("/api/pages/instagram/shopke/").data
        self.assertEqual(page["label"], "reported_multiple")
        self.assertEqual(page["reports_with_supported_evidence"], 3)
        self.assertTrue(page["indexable"])  # passed threshold, so search engines may index it
        self.assertEqual(c.get("/api/search/", {"q": "https://instagram.com/shopke"}).data["results"][0]["label"], "reported_multiple")

    def test_public_output_never_leaks_private_data(self):
        self.publish_three()
        c = self.client_for()
        blob = str(c.get("/api/pages/instagram/shopke/").data) + str(c.get("/api/search/", {"q": "0712345678"}).data)
        for secret in ["712345678", "JOHN DOE", "@x.com", "u1", "value_hash", "value_encrypted"]:
            self.assertNotIn(secret, blob)
        self.assertIn("+254 *** 678", blob)

    def test_linked_pages(self):
        self.publish_three()
        self.report(self.user(), handle="shop2")
        Report.objects.update(status="published")
        page = self.client_for().get("/api/pages/instagram/shopke/").data
        self.assertEqual(page["linked_pages_count"], 1)


class VouchAndCheckTests(ApiBase):
    def test_vouch_needs_proof_and_is_once(self):
        u = self.user()
        c = self.client_for(u)
        body = {"platform": "tiktok", "handle": "@goodshop", "comment": "Got my order"}
        self.assertEqual(c.post("/api/vouches/", body, format="multipart").status_code, 400)
        self.assertEqual(c.post("/api/vouches/", dict(body, proof=upload()), format="multipart").status_code, 201)
        self.assertEqual(c.post("/api/vouches/", dict(body, proof=upload()), format="multipart").status_code, 400)
        page = self.client_for().get("/api/pages/tiktok/goodshop/").data
        self.assertEqual(page["vouches"], 0)  # pending until a moderator approves

    def test_check_request_sets_needs_checking_only(self):
        c = self.client_for(self.user(verified=False))
        r = c.post("/api/check-requests/", {"platform": "tiktok", "handle": "newshop"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.client_for().get("/api/pages/tiktok/newshop/").data["label"], "needs_checking")


class DisputeTests(ApiBase):
    def setUp(self):
        super().setUp()
        self.owner = self.user()
        self.mod1 = self.user(role="moderator")
        self.mod2 = self.user(role="moderator")
        self.report(self.user())
        self.rep = Report.objects.get()
        self.rep.status = "published"; self.rep.save()
        page = self.rep.page
        page.owner, page.verified_owner = self.owner, True
        page.save()

    def test_full_dispute_and_appeal_flow(self):
        stranger = self.client_for(self.user())
        self.assertEqual(stranger.post("/api/reports/%d/dispute/" % self.rep.pk, {"statement": "x" * 30}).status_code, 403)
        c = self.client_for(self.owner)
        r = c.post("/api/reports/%d/dispute/" % self.rep.pk, {"statement": "This is false, here is my delivery record."}, format="multipart")
        self.assertEqual(r.status_code, 201, r.data)
        self.rep.refresh_from_db()
        self.assertEqual(self.rep.status, "disputed")  # stays visible
        self.assertEqual(self.client_for().get("/api/pages/instagram/shopke/").data["label"], "disputed")
        self.assertEqual(self.client_for().get("/api/pages/instagram/shopke/").data["reports_published"], 1)

        did = Dispute.objects.get().pk
        d = {"decision": "remains", "note": "Evidence still supports the report."}
        self.assertEqual(self.client_for(self.owner).post("/api/moderation/disputes/%d/decide/" % did, d).status_code, 403)
        self.assertEqual(self.client_for(self.mod1).post("/api/moderation/disputes/%d/decide/" % did, d).status_code, 200)
        self.rep.refresh_from_db()
        self.assertEqual(self.rep.status, "published")

        a = c.post("/api/disputes/%d/appeal/" % did, {"statement": "New proof: attached courier waybill number."})
        self.assertEqual(a.status_code, 201)
        self.assertEqual(c.post("/api/disputes/%d/appeal/" % did, {"statement": "again " * 10}).status_code, 400)
        aid = a.data["id"]
        d2 = {"decision": "removed", "note": "Courier waybill confirms delivery."}
        self.assertEqual(self.client_for(self.mod1).post("/api/moderation/appeals/%d/decide/" % aid, d2).status_code, 403)  # same moderator
        self.assertEqual(self.client_for(self.mod2).post("/api/moderation/appeals/%d/decide/" % aid, d2).status_code, 200)
        self.rep.refresh_from_db()
        self.assertEqual(self.rep.status, "resolved")
        page = self.client_for().get("/api/pages/instagram/shopke/").data
        self.assertEqual((page["label"], page["reports_published"]), ("resolved", 0))
        actions = set(ModerationAction.objects.values_list("action", flat=True))
        self.assertTrue({"dispute.opened", "report.remains", "appeal.opened", "report.removed"} <= actions)


class ClaimTests(ApiBase):
    def test_claim_code(self):
        u = self.user()
        c = self.client_for(u)
        r = c.post("/api/pages/tiktok/@myshop/claim/")
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.data["code"].startswith("HAKIKI-"))
        self.assertEqual(c.post("/api/pages/tiktok/@myshop/claim/").data["code"], r.data["code"])  # idempotent
        self.assertFalse(Page.objects.get(handle="myshop").verified_owner)  # needs moderator
