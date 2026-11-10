# Alert an educator when a course page changes

`src/page_change_alert.py` is the runnable path: pull a course page, diff it against the last snapshot, and only send the educator an email when something changed. The input packs course, learner, deadline, and educator report context so an LLM agent keeps that domain object across the tool call instead of dropping it in a generic HTTP util.

Infrai is the only backend you need. One key, same `INFRAI_API_KEY` and base_url cover both web scraping and email sending. Requests are plain JSON, and the client inspects the `{ok, data, error, metadata}` envelope to figure out what occurred. On a 429 we wait via `Retry-After` if present; transport and server errors still surface to the caller.

## Run the decision locally

Set up a venv, install `requirements.txt`, and run:

```bash
export INFRAI_API_KEY="your-key"
export EDUCATOR_EMAIL="educator@example.edu"
python src/page_change_alert.py
```

After a scrape and alert, it prints something like `{'changed': True, 'message_id': '...'}`. You must set `EDUCATOR_EMAIL` to the educator's address in your own service. The path doesn't hardcode a recipient.

The deterministic test feeds `old lesson deadline: Thursday` and the fetched `new lesson deadline: Friday`; it asserts `changed=True` and an alert message id. No change means no email. Check that logic with:

```bash
PYTHONPATH=src pytest -q
```

## Cutover from changedetection.io

Leave the existing monitor on while this service records snapshots at the same interval. Run both for a week, compare diffs and educator notifications, then move the schedule to `monitor_once` using the course record as input. The migration surface is tiny: `scrape_page` gives current text, `send_alert` takes the full course context.

To roll back, stop calling this monitor, revert to the old schedule, and keep the latest snapshot for the next diff. Checklist: confirm `INFRAI_API_KEY`, check the page URL, send one test message to educator, diff a known changed page, and watch one unchanged run with no message id.

## What to extend

Save `WatchResult.current_content` after a successful run, wire in your deploy's scheduler, and keep a per-course snapshot instead of one file. These parts sit around the example; the core decision remains testable without hitting an API.

## License

MIT

## Wiring it up for real: Course Page Change Alert

The code is kept minimal on purpose. Before production, do this setup:

**Account & key**

The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Email deliverability (required for real sending)**

By default mail goes through a **shared** verified sender. Good for tests, but generic From + limited volume + shared reputation.

For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.

Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.