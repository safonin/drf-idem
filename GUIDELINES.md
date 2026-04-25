# Development Guidelines

## Architecture invariants

These must be preserved in all changes:

**Atomicity** — never replace `store_if_new()` with separate `exists() + store()` calls. `cache.add()` is an atomic Redis SETNX. Splitting it reintroduces the TOCTOU race condition.

**Key isolation** — always route cache keys through `_make_key(method, path, request_id)`. It SHA-256 hashes the composite value to prevent separator injection attacks. Never concatenate fields directly into a key.

**Input validation** — `request_id` must be validated before any cache interaction. Invalid values return HTTP 400 explicitly; silent ignoring is not acceptable.

**TTL cap** — `MAX_TTL = 60` is enforced in `get_settings()`. Do not bypass it in any code path.

**No Django ORM** — the package is purely Redis-backed. No models, no migrations.

## Adding a new setting

1. Add the key and default to `DEFAULTS` in `settings.py`.
2. If it needs capping or validation, add the logic in `get_settings()` after the `{**DEFAULTS, **user_settings}` merge.
3. Read it everywhere as `cfg = get_settings()["KEY"]`.
4. Test in `test_settings.py` using `override_settings(DRF_IDEM={"KEY": value})` — partial dicts are fine, `get_settings()` merges with DEFAULTS.

## Adding new middleware behavior

- Request routing logic → `middleware.py`
- Redis interactions → `cache.py`
- Config keys → `settings.py`
- Keep `IdempotencyMiddleware.__call__` as the single control point; don't add parallel entry paths.

## Testing

- New middleware path → `test_middleware.py` with `APIClient`
- New cache method → `test_cache.py` with the `IdempotencyCache` fixture
- New setting → `test_settings.py` with `override_settings`
- `conftest.py` has an autouse `clear_cache` fixture; tests do not need manual cleanup
- `LocMemCache` is used in tests (not real Redis), so `get_memory_bytes()` returns 0 — test the method via its return type, not the value

## Code style

- Comments and docstrings may be in Russian (matches existing codebase)
- Private helpers: inline comments are sufficient
- No type annotations required on test functions

## Security checklist for any change

- [ ] New cache keys still go through `_make_key()` (SHA-256 hash)
- [ ] New user input is validated before reaching cache or business logic
- [ ] No code path replaces `store_if_new()` with `exists() + store()`
- [ ] Admin/stats endpoints still require `is_staff=True`
- [ ] TTL cap still enforced in `get_settings()`
