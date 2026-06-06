# Football Data Exports

Static JSON exports from football-data.org live here for the deployed Vercel site.

Generate/update them from the project root:

```bash
FOOTBALL_DATA_API_KEY=your_key npm run export:football-data
```

The deployed app reads `wc-2026-teams.json`. `all-players.json` is a flattened convenience export for future features.
