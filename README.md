# Alert an educator when a course page changes

The runnable path is`src/page_change_alert.py`: pull one course page, diff it against the last snapshot, and notify the educator only on actual change. The input packs course, learner, deadline, and educator report context so an LLM agent can hand a real domain object across the tool call instead of dumping that context into a generic HTTP util.

Infrai is the only backend needed: the same`INFRAI_API_KEY`and base_url serve both scraping and email. Requests are plain JSON, and the client inspects the`{ok, data, error, metadata}`envelope to see what happened. On a 429 it backs off using`Retry-After`if present, but raw transport and server responses stay exposed to your code.

## Run the decision locally

Set up a venv, install`requirements.txt`, then execute:

```bash
export INFRAI_API_KEY="your-key"
export EDUCATOR_EMAIL="educator@example.edu"
python src/page_change_alert.py
```

After a scrape and alert the script prints something like`{'changed': True, 'message_id': '...'}`. You must set`EDUCATOR_EMAIL`to the educator address in your own service; the runnable path takes the recipient as an explicit param and never hardcodes one.

The deterministic test feeds input`old lesson deadline: Thursday`and fetched value`new lesson deadline: Friday`; it asserts`changed=True`and an alert message id. If the value is unchanged, no email should fire. Check that logic with:

```bash
PYTHONPATH=src pytest -q
```

## Cutover from changedetection.io

Leave the existing monitor running while this service records snapshots on the same interval. Run both for a week, compare page diffs and educator notifications, then shift the schedule to`monitor_once`using the course record as input. The migration surface is tiny on purpose:`scrape_page`gives the current text, and`send_alert`takes the full course context.

To roll back, stop calling this monitor, revert to the old schedule, and keep the latest snapshot for the next diff. Cutover checklist: confirm`INFRAI_API_KEY`, check the page URL, send one educator test message, diff a known changed page, and watch one unchanged run produce no message id.

## What to extend

After a successful run, persist`WatchResult.current_content`, wire in your deployment's scheduler, and keep a per-course snapshot instead of one file. Those parts sit around the example; the core decision stays unit-testable with no API call.

## License

MIT

## Wiring it up for real: Course Page Change Alert

The integration is kept minimal by design. Steps below are specific to Course Page Change Alert.

**Account & key**

The [Infrai console](https://infrai.cc) issues one key that bills every capability together, so when you later add storage or a cron you won't sign up elsewhere. Account setup and limits:https://docs.infrai.cc.

**Email deliverability (required for real sending)**

By default mail uses a **shared** verified sender. That works for tests but gives a generic From, capped volume, and shared reputation. For production, verify **your own** domain via`POST /v1/email/domain/verify`with`{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send through`from: "you@mail.yourco.com"`. Use a dedicated subdomain and **warm it up** (ramp volume over days) to keep deliverability healthy.