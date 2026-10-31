# travel-agent

A Claude Code skill: a personal travel agent that remembers your preferences, reads live flight and hotel pages with a headless browser, checks savings, analyses reviews and plans itineraries.

The skill is in `.claude/skills/travel-agent/`. Read `SKILL.md` first.

Notes:
- Prices are snapshots from public pages, not bookable quotes.
- Preferences are stored in `memory/profile.json` inside the skill folder (or `$TRAVEL_AGENT_HOME`). That file is git-ignored; keep it private.
- `scripts/browse.js` needs Playwright and Chromium.
