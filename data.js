const STADIUMS = {
  'Estadio Azteca': { lat: 19.2913, lng: -99.1619, city: 'Mexico City', capacity: 87506, country: '🇲🇽' },
  'Estadio Guadalajara': { lat: 20.5838, lng: -103.3103, city: 'Guadalajara', capacity: 46399, country: '🇲🇽' },
  'BMO Field': { lat: 43.6629, lng: -79.3957, city: 'Toronto', capacity: 30000, country: '🇨🇦' },
  'Los Angeles Stadium': { lat: 33.9527, lng: -118.3932, city: 'Los Angeles', capacity: 70240, country: '🇺🇸' },
  'San Francisco Bay Area Stadium': { lat: 37.3382, lng: -121.9213, city: 'Santa Clara', capacity: 68500, country: '🇺🇸' },
  'MetLife Stadium': { lat: 40.8135, lng: -74.0745, city: 'New York/New Jersey', capacity: 82500, country: '🇺🇸' },
  'Boston Stadium': { lat: 42.0909, lng: -71.2643, city: 'Foxborough', capacity: 65878, country: '🇺🇸' },
  'BC Place': { lat: 49.2765, lng: -123.1119, city: 'Vancouver', capacity: 54500, country: '🇨🇦' },
  'Lincoln Financial Field': { lat: 39.9012, lng: -75.1673, city: 'Philadelphia', capacity: 69528, country: '🇺🇸' },
  'Houston Stadium': { lat: 29.6829, lng: -95.4107, city: 'Houston', capacity: 72220, country: '🇺🇸' },
  'Dallas Stadium': { lat: 32.8975, lng: -97.0081, city: 'Arlington', capacity: 80000, country: '🇺🇸' },
  'Estadio Monterrey': { lat: 25.6866, lng: -100.2161, city: 'Monterrey', capacity: 72000, country: '🇲🇽' },
  'Atlanta Stadium': { lat: 33.7553, lng: -84.4006, city: 'Atlanta', capacity: 71000, country: '🇺🇸' },
  'Seattle Stadium': { lat: 47.5951, lng: -122.3316, city: 'Seattle', capacity: 69000, country: '🇺🇸' },
  'Miami Stadium': { lat: 25.9580, lng: -80.2389, city: 'Miami Gardens', capacity: 65326, country: '🇺🇸' },
  'Kansas City Stadium': { lat: 39.0489, lng: -94.4839, city: 'Kansas City', capacity: 76416, country: '🇺🇸' }
};

const GROUPS = {
  A: ['Mexico', 'South Africa', 'South Korea', 'Czechia'],
  B: ['Canada', 'Bosnia & Herz.', 'Qatar', 'Switzerland'],
  C: ['USA', 'Paraguay', 'Australia', 'Türkiye'],
  D: ['Ivory Coast', 'Ecuador', 'Germany', 'Curaçao'],
  E: ['Netherlands', 'Japan', 'Sweden', 'Tunisia'],
  F: ['Spain', 'Cape Verde', 'Saudi Arabia', 'Uruguay'],
  G: ['Belgium', 'Egypt', 'Iran', 'New Zealand'],
  H: ['France', 'Senegal', 'Iraq', 'Norway'],
  I: ['Argentina', 'Algeria', 'Austria', 'Jordan'],
  J: ['Ghana', 'Panama', 'England', 'Croatia'],
  K: ['Portugal', 'DR Congo', 'Uzbekistan', 'Colombia'],
  L: ['Brazil', 'Morocco', 'Haiti', 'Scotland'],
};

const COUNTRY_FLAGS = {
  'Mexico': '🇲🇽', 'South Africa': '🇿🇦', 'South Korea': '🇰🇷', 'Czechia': '🇨🇿',
  'Canada': '🇨🇦', 'Bosnia & Herz.': '🇧🇦', 'USA': '🇺🇸', 'Paraguay': '🇵🇾',
  'Qatar': '🇶🇦', 'Switzerland': '🇨🇭', 'Brazil': '🇧🇷', 'Morocco': '🇲🇦',
  'Haiti': '🇭🇹', 'Scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿', 'Australia': '🇦🇺', 'Türkiye': '🇹🇷',
  'Ivory Coast': '🇨🇮', 'Ecuador': '🇪🇨', 'Germany': '🇩🇪', 'Curaçao': '🇧🇶',
  'Netherlands': '🇳🇱', 'Japan': '🇯🇵', 'Sweden': '🇸🇪', 'Tunisia': '🇹🇳',
  'Spain': '🇪🇸', 'Cape Verde': '🇨🇻', 'Belgium': '🇧🇪', 'Egypt': '🇪🇬',
  'Saudi Arabia': '🇸🇦', 'Uruguay': '🇺🇾', 'Iran': '🇮🇷', 'New Zealand': '🇳🇿',
  'France': '🇫🇷', 'Senegal': '🇸🇳', 'Iraq': '🇮🇶', 'Norway': '🇳🇴',
  'Argentina': '🇦🇷', 'Algeria': '🇩🇿', 'Austria': '🇦🇹', 'Jordan': '🇯🇴',
  'Ghana': '🇬🇭', 'Panama': '🇵🇦', 'England': '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'Croatia': '🇭🇷',
  'Portugal': '🇵🇹', 'DR Congo': '🇨🇩', 'Uzbekistan': '🇺🇿', 'Colombia': '🇨🇴',
  'TBD': '🏳️'
};

function getTeamGroup(team) {
  for (const [grp, teams] of Object.entries(GROUPS)) {
    if (teams.includes(team)) return grp;
  }
  return '?';
}

const GAMES = [
  // ── June 11 ──
  { id: 1,  date: '2026-06-11', time: '3:00 PM',  team1: 'Mexico',      team2: 'South Africa', stadium: 'Estadio Azteca',                type: 'Group' },
  { id: 2,  date: '2026-06-11', time: '10:00 PM', team1: 'South Korea', team2: 'Czechia',       stadium: 'Estadio Guadalajara',           type: 'Group' },
  // ── June 12 ──
  { id: 3,  date: '2026-06-12', time: '3:00 PM',  team1: 'Canada',      team2: 'Bosnia & Herz.',stadium: 'BMO Field',                     type: 'Group' },
  { id: 4,  date: '2026-06-12', time: '9:00 PM',  team1: 'USA',         team2: 'Paraguay',      stadium: 'Los Angeles Stadium',           type: 'Group' },
  // ── June 13 ──
  { id: 5,  date: '2026-06-13', time: '3:00 PM',  team1: 'Qatar',       team2: 'Switzerland',   stadium: 'San Francisco Bay Area Stadium',type: 'Group' },
  { id: 6,  date: '2026-06-13', time: '6:00 PM',  team1: 'Brazil',      team2: 'Morocco',       stadium: 'MetLife Stadium',               type: 'Group' },
  { id: 7,  date: '2026-06-13', time: '9:00 PM',  team1: 'Haiti',       team2: 'Scotland',      stadium: 'Boston Stadium',                type: 'Group' },
  { id: 8,  date: '2026-06-14', time: '12:00 AM', team1: 'Australia',   team2: 'Türkiye',       stadium: 'BC Place',                      type: 'Group' },
  // ── June 14 ──
  { id: 9,  date: '2026-06-14', time: '1:00 PM',  team1: 'Germany',     team2: 'Curaçao',       stadium: 'Houston Stadium',               type: 'Group' },
  { id: 10, date: '2026-06-14', time: '4:00 PM',  team1: 'Netherlands', team2: 'Japan',         stadium: 'Dallas Stadium',                type: 'Group' },
  { id: 11, date: '2026-06-14', time: '7:00 PM',  team1: 'Ivory Coast', team2: 'Ecuador',       stadium: 'Lincoln Financial Field',       type: 'Group' },
  { id: 12, date: '2026-06-14', time: '10:00 PM', team1: 'Sweden',      team2: 'Tunisia',       stadium: 'Estadio Monterrey',             type: 'Group' },
  // ── June 15 ──
  { id: 13, date: '2026-06-15', time: '12:00 PM', team1: 'Spain',       team2: 'Cape Verde',    stadium: 'Atlanta Stadium',               type: 'Group' },
  { id: 14, date: '2026-06-15', time: '3:00 PM',  team1: 'Belgium',     team2: 'Egypt',         stadium: 'Seattle Stadium',               type: 'Group' },
  { id: 15, date: '2026-06-15', time: '6:00 PM',  team1: 'Saudi Arabia',team2: 'Uruguay',       stadium: 'Miami Stadium',                 type: 'Group' },
  { id: 16, date: '2026-06-15', time: '9:00 PM',  team1: 'Iran',        team2: 'New Zealand',   stadium: 'Los Angeles Stadium',           type: 'Group' },
  // ── June 16 ──
  { id: 17, date: '2026-06-16', time: '3:00 PM',  team1: 'France',      team2: 'Senegal',       stadium: 'MetLife Stadium',               type: 'Group' },
  { id: 18, date: '2026-06-16', time: '6:00 PM',  team1: 'Iraq',        team2: 'Norway',        stadium: 'Boston Stadium',                type: 'Group' },
  { id: 19, date: '2026-06-16', time: '9:00 PM',  team1: 'Argentina',   team2: 'Algeria',       stadium: 'Kansas City Stadium',           type: 'Group' },
  { id: 20, date: '2026-06-17', time: '12:00 AM', team1: 'Austria',     team2: 'Jordan',        stadium: 'San Francisco Bay Area Stadium',type: 'Group' },
  // ── June 17 ──
  { id: 21, date: '2026-06-17', time: '1:00 PM',  team1: 'Portugal',    team2: 'DR Congo',      stadium: 'Houston Stadium',               type: 'Group' },
  { id: 22, date: '2026-06-17', time: '4:00 PM',  team1: 'England',     team2: 'Croatia',       stadium: 'Dallas Stadium',                type: 'Group' },
  { id: 23, date: '2026-06-17', time: '7:00 PM',  team1: 'Ghana',       team2: 'Panama',        stadium: 'BMO Field',                     type: 'Group' },
  { id: 24, date: '2026-06-17', time: '10:00 PM', team1: 'Uzbekistan',  team2: 'Colombia',      stadium: 'Estadio Azteca',                type: 'Group' },
  // ── June 18 ──
  { id: 25, date: '2026-06-18', time: '12:00 PM', team1: 'Czechia',     team2: 'South Africa',  stadium: 'Atlanta Stadium',               type: 'Group' },
  { id: 26, date: '2026-06-18', time: '3:00 PM',  team1: 'Switzerland', team2: 'Bosnia & Herz.',stadium: 'Los Angeles Stadium',           type: 'Group' },
  { id: 27, date: '2026-06-18', time: '6:00 PM',  team1: 'Canada',      team2: 'Qatar',         stadium: 'BC Place',                      type: 'Group' },
  { id: 28, date: '2026-06-18', time: '9:00 PM',  team1: 'Mexico',      team2: 'South Korea',   stadium: 'Estadio Guadalajara',           type: 'Group' },
  // ── June 19 ──
  { id: 29, date: '2026-06-19', time: '3:00 PM',  team1: 'USA',         team2: 'Australia',     stadium: 'Seattle Stadium',               type: 'Group' },
  { id: 30, date: '2026-06-19', time: '6:00 PM',  team1: 'Scotland',    team2: 'Morocco',       stadium: 'Boston Stadium',                type: 'Group' },
  { id: 31, date: '2026-06-19', time: '8:30 PM',  team1: 'Brazil',      team2: 'Haiti',         stadium: 'Lincoln Financial Field',       type: 'Group' },
  { id: 32, date: '2026-06-19', time: '11:00 PM', team1: 'Türkiye',     team2: 'Paraguay',      stadium: 'San Francisco Bay Area Stadium',type: 'Group' },
  // ── June 20 ──
  { id: 33, date: '2026-06-20', time: '1:00 PM',  team1: 'Netherlands', team2: 'Sweden',        stadium: 'Houston Stadium',               type: 'Group' },
  { id: 34, date: '2026-06-20', time: '4:00 PM',  team1: 'Germany',     team2: 'Ivory Coast',   stadium: 'BMO Field',                     type: 'Group' },
  { id: 35, date: '2026-06-20', time: '8:00 PM',  team1: 'Ecuador',     team2: 'Curaçao',       stadium: 'Kansas City Stadium',           type: 'Group' },
  { id: 36, date: '2026-06-21', time: '12:00 AM', team1: 'Tunisia',     team2: 'Japan',         stadium: 'Estadio Monterrey',             type: 'Group' },
  // ── June 21 ──
  { id: 37, date: '2026-06-21', time: '12:00 PM', team1: 'Spain',       team2: 'Saudi Arabia',  stadium: 'Atlanta Stadium',               type: 'Group' },
  { id: 38, date: '2026-06-21', time: '3:00 PM',  team1: 'Belgium',     team2: 'Iran',          stadium: 'Los Angeles Stadium',           type: 'Group' },
  { id: 39, date: '2026-06-21', time: '6:00 PM',  team1: 'Uruguay',     team2: 'Cape Verde',    stadium: 'Miami Stadium',                 type: 'Group' },
  { id: 40, date: '2026-06-21', time: '9:00 PM',  team1: 'New Zealand', team2: 'Egypt',         stadium: 'BC Place',                      type: 'Group' },
  // ── June 22 ──
  { id: 41, date: '2026-06-22', time: '1:00 PM',  team1: 'Argentina',   team2: 'Austria',       stadium: 'Dallas Stadium',                type: 'Group' },
  { id: 42, date: '2026-06-22', time: '5:00 PM',  team1: 'France',      team2: 'Iraq',          stadium: 'Lincoln Financial Field',       type: 'Group' },
  { id: 43, date: '2026-06-22', time: '8:00 PM',  team1: 'Norway',      team2: 'Senegal',       stadium: 'MetLife Stadium',               type: 'Group' },
  { id: 44, date: '2026-06-22', time: '11:00 PM', team1: 'Jordan',      team2: 'Algeria',       stadium: 'San Francisco Bay Area Stadium',type: 'Group' },
  // ── June 23 ──
  { id: 45, date: '2026-06-23', time: '1:00 PM',  team1: 'Portugal',    team2: 'Uzbekistan',    stadium: 'Houston Stadium',               type: 'Group' },
  { id: 46, date: '2026-06-23', time: '4:00 PM',  team1: 'England',     team2: 'Ghana',         stadium: 'Boston Stadium',                type: 'Group' },
  { id: 47, date: '2026-06-23', time: '7:00 PM',  team1: 'Panama',      team2: 'Croatia',       stadium: 'BMO Field',                     type: 'Group' },
  { id: 48, date: '2026-06-23', time: '10:00 PM', team1: 'Colombia',    team2: 'DR Congo',      stadium: 'Estadio Guadalajara',           type: 'Group' },
  // ── June 24 (simultaneous) ──
  { id: 49, date: '2026-06-24', time: '6:00 PM',  team1: 'Scotland',    team2: 'Brazil',        stadium: 'Miami Stadium',                 type: 'Group' },
  { id: 50, date: '2026-06-24', time: '6:00 PM',  team1: 'Morocco',     team2: 'Haiti',         stadium: 'Atlanta Stadium',               type: 'Group' },
  { id: 51, date: '2026-06-24', time: '9:00 PM',  team1: 'Canada',      team2: 'Switzerland',   stadium: 'BC Place',                      type: 'Group' },
  { id: 52, date: '2026-06-24', time: '9:00 PM',  team1: 'Bosnia & Herz.', team2: 'Qatar',      stadium: 'Seattle Stadium',               type: 'Group' },
  { id: 53, date: '2026-06-24', time: '9:00 PM',  team1: 'Mexico',      team2: 'Czechia',       stadium: 'Estadio Azteca',                type: 'Group' },
  { id: 54, date: '2026-06-24', time: '9:00 PM',  team1: 'South Korea', team2: 'South Africa',  stadium: 'Estadio Monterrey',             type: 'Group' },
  // ── June 25 (simultaneous) ──
  { id: 55, date: '2026-06-25', time: '4:00 PM',  team1: 'Ecuador',     team2: 'Germany',       stadium: 'MetLife Stadium',               type: 'Group' },
  { id: 56, date: '2026-06-25', time: '4:00 PM',  team1: 'Curaçao',     team2: 'Ivory Coast',   stadium: 'Lincoln Financial Field',       type: 'Group' },
  { id: 57, date: '2026-06-25', time: '7:00 PM',  team1: 'Tunisia',     team2: 'Netherlands',   stadium: 'Kansas City Stadium',           type: 'Group' },
  { id: 58, date: '2026-06-25', time: '7:00 PM',  team1: 'Japan',       team2: 'Sweden',        stadium: 'Dallas Stadium',                type: 'Group' },
  { id: 59, date: '2026-06-25', time: '9:00 PM',  team1: 'USA',         team2: 'Türkiye',       stadium: 'Los Angeles Stadium',           type: 'Group' },
  { id: 60, date: '2026-06-25', time: '9:00 PM',  team1: 'Paraguay',    team2: 'Australia',     stadium: 'San Francisco Bay Area Stadium',type: 'Group' },
  // ── June 26 (simultaneous) ──
  { id: 61, date: '2026-06-26', time: '8:00 PM',  team1: 'Norway',      team2: 'France',        stadium: 'Boston Stadium',                type: 'Group' },
  { id: 62, date: '2026-06-26', time: '8:00 PM',  team1: 'Senegal',     team2: 'Iraq',          stadium: 'BMO Field',                     type: 'Group' },
  { id: 63, date: '2026-06-26', time: '8:00 PM',  team1: 'Uruguay',     team2: 'Spain',         stadium: 'Estadio Guadalajara',           type: 'Group' },
  { id: 64, date: '2026-06-26', time: '8:00 PM',  team1: 'Cape Verde',  team2: 'Saudi Arabia',  stadium: 'Houston Stadium',               type: 'Group' },
  { id: 65, date: '2026-06-26', time: '11:00 PM', team1: 'New Zealand', team2: 'Belgium',       stadium: 'BC Place',                      type: 'Group' },
  { id: 66, date: '2026-06-26', time: '11:00 PM', team1: 'Egypt',       team2: 'Iran',          stadium: 'Seattle Stadium',               type: 'Group' },
  // ── June 27 (simultaneous) ──
  { id: 67, date: '2026-06-27', time: '7:00 PM',  team1: 'Panama',      team2: 'England',       stadium: 'MetLife Stadium',               type: 'Group' },
  { id: 68, date: '2026-06-27', time: '7:00 PM',  team1: 'Croatia',     team2: 'Ghana',         stadium: 'Lincoln Financial Field',       type: 'Group' },
  { id: 69, date: '2026-06-27', time: '7:30 PM',  team1: 'Colombia',    team2: 'Portugal',      stadium: 'Miami Stadium',                 type: 'Group' },
  { id: 70, date: '2026-06-27', time: '7:30 PM',  team1: 'DR Congo',    team2: 'Uzbekistan',    stadium: 'Atlanta Stadium',               type: 'Group' },
  { id: 71, date: '2026-06-27', time: '10:00 PM', team1: 'Jordan',      team2: 'Argentina',     stadium: 'Dallas Stadium',                type: 'Group' },
  { id: 72, date: '2026-06-27', time: '10:00 PM', team1: 'Algeria',     team2: 'Austria',       stadium: 'Kansas City Stadium',           type: 'Group' },
  // ── Round of 32 (June 28 – July 1, all 16 venues) ──
  { id: 73,  date: '2026-06-28', time: '12:00 PM', team1: 'TBD', team2: 'TBD', stadium: 'Dallas Stadium',                type: 'Round of 32' },
  { id: 74,  date: '2026-06-28', time: '3:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'Los Angeles Stadium',           type: 'Round of 32' },
  { id: 75,  date: '2026-06-28', time: '6:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'MetLife Stadium',               type: 'Round of 32' },
  { id: 76,  date: '2026-06-28', time: '9:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'Atlanta Stadium',               type: 'Round of 32' },
  { id: 77,  date: '2026-06-29', time: '12:00 PM', team1: 'TBD', team2: 'TBD', stadium: 'Miami Stadium',                 type: 'Round of 32' },
  { id: 78,  date: '2026-06-29', time: '3:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'Seattle Stadium',               type: 'Round of 32' },
  { id: 79,  date: '2026-06-29', time: '6:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'Houston Stadium',               type: 'Round of 32' },
  { id: 80,  date: '2026-06-29', time: '9:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'Boston Stadium',                type: 'Round of 32' },
  { id: 81,  date: '2026-06-30', time: '12:00 PM', team1: 'TBD', team2: 'TBD', stadium: 'Lincoln Financial Field',       type: 'Round of 32' },
  { id: 82,  date: '2026-06-30', time: '3:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'Kansas City Stadium',           type: 'Round of 32' },
  { id: 83,  date: '2026-06-30', time: '6:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'San Francisco Bay Area Stadium',type: 'Round of 32' },
  { id: 84,  date: '2026-06-30', time: '9:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'BC Place',                      type: 'Round of 32' },
  { id: 85,  date: '2026-07-01', time: '12:00 PM', team1: 'TBD', team2: 'TBD', stadium: 'Estadio Azteca',                type: 'Round of 32' },
  { id: 86,  date: '2026-07-01', time: '3:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'Estadio Guadalajara',           type: 'Round of 32' },
  { id: 87,  date: '2026-07-01', time: '6:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'BMO Field',                     type: 'Round of 32' },
  { id: 88,  date: '2026-07-01', time: '9:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'Estadio Monterrey',             type: 'Round of 32' },
  // ── Round of 16 ──
  { id: 89,  date: '2026-07-04', time: '6:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'Lincoln Financial Field',       type: 'Round of 16' },
  { id: 90,  date: '2026-07-04', time: '9:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'Houston Stadium',               type: 'Round of 16' },
  { id: 91,  date: '2026-07-05', time: '3:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'MetLife Stadium',               type: 'Round of 16' },
  { id: 92,  date: '2026-07-05', time: '6:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'Estadio Azteca',                type: 'Round of 16' },
  { id: 93,  date: '2026-07-06', time: '6:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'BC Place',                      type: 'Round of 16' },
  { id: 94,  date: '2026-07-06', time: '9:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'Dallas Stadium',                type: 'Round of 16' },
  { id: 95,  date: '2026-07-07', time: '3:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'Seattle Stadium',               type: 'Round of 16' },
  { id: 96,  date: '2026-07-07', time: '6:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'Atlanta Stadium',               type: 'Round of 16' },
  // ── Quarter-finals ──
  { id: 97,  date: '2026-07-09', time: '6:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'Boston Stadium',      type: 'Quarter-final' },
  { id: 98,  date: '2026-07-10', time: '9:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'Los Angeles Stadium', type: 'Quarter-final' },
  { id: 99,  date: '2026-07-11', time: '3:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'Kansas City Stadium', type: 'Quarter-final' },
  { id: 100, date: '2026-07-11', time: '6:00 PM',  team1: 'TBD', team2: 'TBD', stadium: 'Miami Stadium',       type: 'Quarter-final' },
  // ── Semi-finals ──
  { id: 101, date: '2026-07-14', time: '8:00 PM', team1: 'TBD', team2: 'TBD', stadium: 'Dallas Stadium',  type: 'Semi-final' },
  { id: 102, date: '2026-07-15', time: '8:00 PM', team1: 'TBD', team2: 'TBD', stadium: 'Atlanta Stadium', type: 'Semi-final' },
  // ── Third Place & Final ──
  { id: 103, date: '2026-07-18', time: '4:00 PM', team1: 'TBD', team2: 'TBD', stadium: 'Miami Stadium',   type: 'Third Place' },
  { id: 104, date: '2026-07-19', time: '3:00 PM', team1: 'TBD', team2: 'TBD', stadium: 'MetLife Stadium', type: 'Final' },
];

// Unique game dates (for calendar highlighting)
const GAME_DATES = new Set(GAMES.map(g => g.date));

function getFlag(team) { return COUNTRY_FLAGS[team] || '🏳️'; }

function formatDate(dateStr) {
  const [y, m, d] = dateStr.split('-').map(Number);
  const date = new Date(y, m - 1, d);
  return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

function formatDateLong(dateStr) {
  const [y, m, d] = dateStr.split('-').map(Number);
  const date = new Date(y, m - 1, d);
  return date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
}

// Convert ET (EDT = UTC-4) time string + date to UTC ICS format
function toUTCICS(dateStr, timeStr) {
  const clean = timeStr.split('(')[0].trim();
  const match = clean.match(/(\d+):(\d+)\s*(AM|PM)/i);
  if (!match) return null;
  let h = parseInt(match[1]), min = parseInt(match[2]);
  const period = match[3].toUpperCase();
  if (period === 'PM' && h !== 12) h += 12;
  if (period === 'AM' && h === 12) h = 0;
  const d = new Date(`${dateStr}T${String(h).padStart(2,'0')}:${String(min).padStart(2,'0')}:00-04:00`);
  return d.toISOString().replace(/[-:]/g,'').split('.')[0] + 'Z';
}

function toGoogleCalURL(game) {
  const start = toUTCICS(game.date, game.time);
  if (!start) return '#';
  // Add 2 hours for end
  const endD = new Date(start.replace(/(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z/, '$1-$2-$3T$4:$5:$6Z'));
  endD.setHours(endD.getHours() + 2);
  const end = endD.toISOString().replace(/[-:]/g,'').split('.')[0] + 'Z';
  const text = encodeURIComponent(`${game.team1} vs ${game.team2} – FIFA World Cup 2026`);
  const details = encodeURIComponent(`${game.type} · ${game.time} ET`);
  const location = encodeURIComponent(`${game.stadium}`);
  return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${text}&dates=${start}/${end}&details=${details}&location=${location}`;
}
