# Product validation gate

Run this gate from a clean product checkout before claiming that a release
meets the Personal AgentOS v1 outcome:

```sh
python3 scripts/product_validate.py --unit --homebrew --compose \
  --output /tmp/agentos-product-validation.json \
  --markdown /tmp/agentos-product-validation.md
```

The report distinguishes four states: `passed` has direct evidence, `failed`
needs a repair issue, `blocked` needs an unavailable external prerequisite,
and `gap` is an intentional post-v1 product-vision item. Reports contain no
API keys, Telegram tokens, document contents, or model transcripts.

Use existing credentials for the live checks only when the owner is present:

```sh
python3 scripts/product_validate.py --live-model --live-telegram
```

`--live-telegram` records the required paired-account acceptance check. The
maintainer sends a new Telegram request after restarting AgentOS and verifies
the shared web history and the delivery trace; no bot token is printed or
stored in the report.

The gate is a release decision aid, not a substitute for product design. The
native desktop and mobile apps, additional messaging channels, and
multi-tenant hosting remain explicit future gaps in the current vision.

When Docker is available, `--compose` builds an isolated Compose project,
waits for `/healthz`, writes an AgentOS note into its named volume, recreates
the container, and checks that the note remains. It then removes the temporary
project and volume.
