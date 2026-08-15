devex

maya: Heads-up — quickstart README has a broken link to the Python sample app and an outdated snippet using the old sync client. Link 404: https://github.com/redwood-inference/sample-apps/python-quickstart -> 404
maya: snippet shows `from redwood import RedwoodClient` and `client.generate(...)` but current SDK uses `from redwood import Client` and async usage is `async with Client(...) as client:`
jon: ugh, hit this while onboarding Sejal earlier today.
jon: can you paste the broken snippet so i can file a docs PR?
maya: ```python
from redwood import RedwoodClient
client = RedwoodClient(api_key="$REDWOOD_API_KEY")
resp = client.generate("Hello")
print(resp.text)
```
kevin: ok that looks like the pre-1.3 example. we switched to async context manager pattern last quarter.
sam: also the README doesn't mention retry/backoff behaviour or the httpx http2 requirement for streaming — folks get mysterious streaming failures.
ci-bot: link-checker: ERROR: 1 broken link found in docs/quickstarts/python/README.md -> https://github.com/redwood-inference/sample-apps/python-quickstart (404)
jon: i'll open a docs PR to update the snippet & point to the new examples path, assigning the sample-app update to @kevin.
kevin: pushing a quick patch to sample-apps now. preview patch below — will also update README link target.
kevin: ```diff
- from redwood import RedwoodClient
- client = RedwoodClient(api_key=os.getenv("REDWOOD_API_KEY"))
- resp = client.generate("Hello")
+ from redwood import Client
+ import asyncio
+
+ async def main():
+     async with Client(api_key=os.getenv("REDWOOD_API_KEY")) as client:
+         resp = await client.generate("Hello")
+         print(resp.text)
+
+ asyncio.run(main())
```
kevin: also adding a short note about retryable errors — 429/503 are retried by the SDK by default. linking to internal retries doc: https://docs.redwood.ai/retries
maya: can we also fix the typing in the example? it currently uses `str | None` which breaks on py<3.10 and with `from __future__ import annotations` oddities.
sam: recommend `Optional[str]` in examples to be compatible across py37-310 users. also add `# type: ignore` where we can't easily unify.
jon: quickstart smoke test: after sample-app update can someone run `docs-quickstart-smoke`? CI job is flaky.
ci-bot: triggered job `docs-quickstart-smoke` (run id 98321) -> failed at step `pip install -r requirements.txt`: httpx 0.23.* conflicts with httpx[http2] in our container.
kevin: i'll update sample-apps requirements to `httpx[http2]>=0.24` and pin `redwood-sdk>=1.4.0` in the example. will open PR for both docs and sample-apps.
maya: thanks. once PRs land, we should add an e2e check that executes the README snippet (run the snippet in a disposable env) to catch drift earlier.
sam: agreed — i'll add a tiny pytest that runs the snippet in a container and asserts it returns a 2xx-ish result (mocked).
jon: awesome, thanks everyone. tagging @docs and @devex to follow release.
maya: :thumbsup:
