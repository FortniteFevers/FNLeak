# Football Data Exports

This folder is for committed football-data.org API exports used by the static pages.

The app currently loads the raw bundled response from:

```text
football-data/wc-2026-teams.json
```

Generate it with:

```bash
FOOTBALL_DATA_API_KEY=your_key npm run export:football-data
```

The exporter writes:

```text
manifest.json
wc-2026-teams.json
all-players.json
```

It also writes the same structure to `public/football-data/`, which is the copy Vercel serves in production.
