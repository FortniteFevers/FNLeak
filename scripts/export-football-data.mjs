import { mkdir, rm, writeFile } from 'node:fs/promises'
import path from 'node:path'

const API_TOKEN = process.env.FOOTBALL_DATA_API_KEY
const API_URL = 'https://api.football-data.org/v4/competitions/WC/teams?season=2026'
const EXPORT_ROOTS = ['football-data', 'public/football-data']

if (!API_TOKEN) {
  console.error('Missing FOOTBALL_DATA_API_KEY.')
  console.error('Run: FOOTBALL_DATA_API_KEY=your_key npm run export:football-data')
  process.exit(1)
}

const response = await fetch(API_URL, {
  headers: {
    'X-Auth-Token': API_TOKEN,
  },
})

if (!response.ok) {
  throw new Error(`football-data.org returned HTTP ${response.status}`)
}

const data = await response.json()
const teams = data.teams || []
const exportedAt = new Date().toISOString()
const rawOutput = {
  ...data,
  exportedAt,
  source: API_URL,
}

const slugify = (value) =>
  String(value || 'unknown')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/&/g, 'and')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')

const getPlayerKey = (team, player) =>
  player.id ||
  `${team.id || slugify(team.name)}-${slugify(player.name)}-${player.dateOfBirth || 'unknown'}`

const playerRecords = []
for (const team of teams) {
  const slug = slugify(team.name)
  const squad = team.squad || []

  for (const player of squad) {
    playerRecords.push({
      ...player,
      playerKey: getPlayerKey(team, player),
      teamId: team.id,
      teamName: team.name,
      teamShortName: team.shortName,
      teamTla: team.tla,
      teamSlug: slug,
    })
  }
}

const manifest = {
  exportedAt,
  source: API_URL,
  teamCount: teams.length,
  playerCount: playerRecords.length,
  files: {
    rawTeamsResponse: 'wc-2026-teams.json',
    allPlayers: 'all-players.json',
  },
}

async function writeJSON(filePath, value) {
  await mkdir(path.dirname(filePath), { recursive: true })
  await writeFile(filePath, `${JSON.stringify(value, null, 2)}\n`)
}

for (const root of EXPORT_ROOTS) {
  await rm(path.join(root, 'teams'), { recursive: true, force: true })
  await rm(path.join(root, 'players'), { recursive: true, force: true })

  await writeJSON(path.join(root, 'manifest.json'), manifest)
  await writeJSON(path.join(root, 'wc-2026-teams.json'), rawOutput)
  await writeJSON(path.join(root, 'all-players.json'), playerRecords)
}

console.log(`Exported ${teams.length} teams and ${playerRecords.length} players.`)
console.log('Wrote raw teams response, all players, and manifest JSON under:')
for (const root of EXPORT_ROOTS) console.log(`- ${root}`)
