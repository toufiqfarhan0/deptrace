devex

maria: Heads-up — the sample-app README in /examples/onboarding has an old auth snippet. Customers copying it hit 401s.

josh: ah, which line? can you paste the snippet?

maria: path: examples/onboarding/README.md. Current curl example uses `-H 'x-api-key: $KEY'` and the JS snippet does `client.setApiKey(KEY)`. Our SDK expects `Authorization: Bearer ...` and the JS SDK init is different now.

maria: problematic curl:
```
curl -X POST https://api.redwood.ai/v1/generate \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: $REDWOOD_KEY' \
  -d '{"prompt":"hello"}'
```

maria: and JS example currently in README: `const client = new RedwoodClient(); client.setApiKey(process.env.REDWOOD_KEY);` — that API was removed in v0.9, so folks get silent failures or immediate 401.

tara: ugh, classic snippet drift. we should update to the canonical patterns and add a tiny test that runs the curl/JS example during CI. also add a note about token env var name.

ken: agree. also worth calling out SDK parity: python example uses `client = Redwood(api_key=...)` while JS uses `new RedwoodClient({ token: ... })` in new SDK. README should show both matching the official SDK surface.

sam: I'll open a PR with fixes. plan: replace curl with `Authorization: Bearer $REDWOOD_API_KEY`, swap JS sample to `const client = new RedwoodClient({ token: process.env.REDWOOD_API_KEY });` and add a one-line retry hint.

maria: thanks. can we also add an explicit note about the SDK handling retries vs sample app? people copy the sample retry wrapper and then double-retry. mention that app-level retry should be idempotent only.

josh: +1. propose a short comment block in README: "SDK will do exponential backoff for 5xx by default; if you implement app retries, gate on idempotency and set a max attempts = 2."

sam: PR opened: https://github.com/redwood-inference/examples/pull/412 — includes README edits, updated curl + js + python snippets, and a tiny GitHub Action that runs the curl example against sandbox creds (no real token).

devex-bot: Issue #987 created for followups: add unit that lints README snippets for current SDK API and schedule a monthly check.

tara: can we also add a lint rule to docs CI to fail if sample code references removed methods (like `setApiKey`)? even a regex-based check would cut down drift.

ken: regex check + runnable snippet test sounds good. low effort, high signal.

maria: sweet. after sam's PR merges, I'll re-run onboarding walkthrough and update the quickstart template too. thanks y'all :thumbsup:

sam: will merge after a smoke test, then add the CI token rotation note.

josh: small follow-up — update the onboarding ticket with the new env var name `REDWOOD_API_KEY` so support articles line up.

maria: done — filed doc ticket DOC-1453.

ken: nice. closing the thread, feel free to ping if anything flares up.