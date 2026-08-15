devex

tobias (DevEx): Ran through the quickstart during a new hire walkthrough and hit broken Python + Go snippets in README. raising here so we can patch and add CI checks.
mira (SDK): ouch, which snippets exactly? paste error and the code block if you can.
tobias (DevEx): Python snippet currently shows: 
```py
from redwood import Client
client = Client(api_key=os.getenv('REDWOOD_TOKEN'))
resp = client.generate('Summarize this')
print(resp.text)
```

tobias (DevEx): runtime error: AttributeError: 'Client' object has no attribute 'generate'. Also env var REDWOOD_TOKEN isn't in the quickstart env list. The Go example uses a package path that was renamed and an outdated method name too.
samir (docs): we missed a cross-lang API change when we updated the JS SDK docs. The SDK split changed naming across all languages (chat vs completions) and the auth env var standardized to RW_API_KEY.
mira (SDK): yeah we unified auth to RW_API_KEY in v0.9 and the Python client exposes RedwoodClient.chat.create now. We should add before/after examples and a short migration note. Also call out default retry change (was 3 -> now 0) in the quickstart to reduce surprise 429s.
tobias (DevEx): proposed fixes — Python before/after: 
```py
# before (broken)
from redwood import Client
client = Client(api_key=os.getenv('REDWOOD_TOKEN'))
resp = client.generate('Summarize this')
print(resp.text)

# after (fixed)
from redwood import RedwoodClient
client = RedwoodClient(api_key=os.getenv('RW_API_KEY'), retry={'max_retries': 2})
resp = client.chat.create(messages=[{'role':'user','content':'Summarize this'}])
print(resp.choices[0]['message']['content'])
```

tobias (DevEx): Go before/after: 
```go
// before (broken)
import "redwood"
client := redwood.NewClient(os.Getenv("REDWOOD_TOKEN"))
res, _ := client.Generate("hello")
fmt.Println(res.Text)

// after (fixed)
import "github.com/redwood-inference/go-sdk"
client := sdk.NewRedwoodClient(sdk.Config{APIKey: os.Getenv("RW_API_KEY"), Retry: sdk.RetryConfig{MaxRetries:2}})
res, _ := client.Chat.Create(sdk.ChatRequest{Messages: []sdk.Message{{Role:"user", Content:"hello"}}})
fmt.Println(res.Choices[0].Message.Content)
```

mira (SDK): I'll open an SDK PR to add a friendly runtime check for legacy env var names (REDWOOD_TOKEN, OLD_API_KEY) that raises a clear error pointing to RW_API_KEY. That should reduce onboarding confusion.
samir (docs): I'll open a docs PR to update Python/Go/JS quickstarts, add a short migration section at the top of the quickstart, and replace any placeholder keys like REDACTED_API_KEY with an explicit example: export RW_API_KEY=your_real_key (and a short security note).
examples-bot: PR opened by samir: "docs: fix quickstart snippets (py/go) + migration note" 10https://github.com/redwood-inference/docs/pull/825
ci-bot: kicked off examples-smoke workflow for branch docs/fix-quickstart (runners: python, go, node).
ci-bot: examples-smoke failed (run 34): detected placeholder env value 'REDACTED_API_KEY' in README (regex fail) -> caught early.
samir (docs): thanks CI! replaced placeholder with instruction to set RW_API_KEY and added a GH Action check to fail when placeholder patterns /(REDACTED|YOUR_KEY|PLACEHOLDER)/i appear in code blocks. pushed fix.
ci-bot: examples-smoke passed (run 35). Python & Go examples executed against staging fixtures.
mira (SDK): merged SDK guard PR and bumped SDK minor. Also added a short deprecation warning when old env vars are present to help users upgrade.
tobias (DevEx): great. can we add a note to onboarding checklist to run the examples smoke locally (or at least confirm they work)? new hires often skip that step.
samir (docs): added a short onboarding checkbox: "Run quickstart examples locally (python/go/node)" and linked the smoke script. backported docs to release/v0.9.x.
tobias (DevEx): closing loop. this kind of multi-language snippet drift is high-impact for first-run DX. thanks everyone :thumbsup: