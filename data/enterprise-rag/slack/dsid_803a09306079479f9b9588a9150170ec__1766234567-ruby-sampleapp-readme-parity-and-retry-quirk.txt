devex

mia: Trying to onboard folks with the community sampleapp and I hit a small UX mismatch.
The README shows `Redwood::Client.new(api_key: ENV['REDWOOD_API_KEY'])` but our ruby SDK examples/docs elsewhere use `Redwood.configure { |c| c.api_key = ENV['REDWOOD_API_KEY'] }` — a bit confusing for new users.

ryan: Which gem/version is the sampleapp using? 0.8.x or the local main branch?

mia: It's pointing at the local sdk (Gemfile: `gem 'redwood', path: '../ruby-sdk'`). I think README bits were copied from JS and not updated.

sophia: Oof, that sounds like my oversight. I landed some README edits in PR #428 but didn't sync the sampleapp. Can you paste the error you saw?

mia: Repro steps:
1) set REDWOOD_API_KEY
2) `bundle exec ruby examples/generate.rb`

Sometimes it returns 401, sometimes a 500/429 and it doesn't retry automatically. Minimal snippet:

```ruby
client = Redwood::Client.new(api_key: ENV['REDWOOD_API_KEY'])
resp = client.generate(prompt: "hi")
# occasionally raises Redwood::Errors::ServerError or returns 500 body
```

ryan: The ruby SDK's retry behavior is intentionally conservative. Retries live in `lib/redwood/http.rb` and by default we don't retry non-idempotent endpoints. Generation is considered non-idempotent unless the caller provides an idempotency_key.

mia: That makes sense, but JS SDK automatically uses idempotency keys (or at least retries on 5xx by default with safe heuristics). For onboarding parity, could we add a short example in the sampleapp README showing how to enable retries + idempotency? New users hit this and assume the SDK will retry for them.

sophia: Agreed. We should add a snippet and an ENV example. I sketched something in PR #428 — idea:

```ruby
client = Redwood::Client.new(api_key: ENV['REDWOOD_API_KEY'], retries: { max: 3, backoff_factor: 1.5 })
resp = client.generate(prompt: "hi", idempotency_key: ENV['REDWOOD_IDEMPOTENCY_KEY'])
```

That would be explicit and teach them the safer pattern.

marco: FYI CI is flaking on a retry-related integration test — https://ci.redwood/1234 looks related to this change.

eng-bot: deploy-bot: Deployed branch `ruby-sampleapp-readme` to staging at 1766234599

ryan: I'll pick up #428 for review this afternoon. Also recommend we add a small note in the onboarding quickstart about the env var name (REDWOOD_API_KEY) and how to pin the gem via Gemfile (to avoid local path surprises).

mia: I pushed an update to the branch: pinned `ruby-sdk >= 0.8.0`, added the retry+idempotency example, and clarified the auth env var. Also added a one-line comment about bundler vs local path usage.

sophia: Nice. Assigning to @ryan and myself for final review. :eyes:

ryan: Ack, will review and run the sampleapp locally. If green, I'll merge and cherry-pick to release branch.

mia: Thanks everyone. Happy to follow up if CI or users still hit issues. :thumbsup:
