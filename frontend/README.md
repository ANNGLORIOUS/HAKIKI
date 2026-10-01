
## Backend patch contents
- `apps/listings/public.py`: adds the `indexable` flag
- `config/settings.py`: adds `NUM_PROXIES`; the default API permission is now "logged in" (public views opt in), which fixes a 500 error on `/api/auth/me` for logged-out visitors
- `apps/core/test_api.py`: adds a test for that fix (26 tests total)

After copying, add `NUM_PROXIES=1` to your backend `.env`.
