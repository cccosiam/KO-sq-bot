import asyncio
import time
import discord
import gspread
from google.oauth2.service_account import Credentials
from models import Player, LeaderboardConfig

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# One client per credentials file, so we only authenticate once per service account.
_clients: dict[str, gspread.Client] = {}

# Cached sheet contents, keyed by (credentials_file, spreadsheet_id, sheet_name).
# Avoids hitting the Sheets API on every !can / !ap / !sub call - we fetch the
# whole sheet at once and look players up locally instead of one request per player.
_sheet_cache: dict[str, dict] = {}
_CACHE_TTL_SECONDS = 30


def _get_client(credentials_file: str) -> gspread.Client:
    if credentials_file not in _clients:
        creds = Credentials.from_service_account_file(credentials_file, scopes=_SCOPES)
        _clients[credentials_file] = gspread.authorize(creds)
    return _clients[credentials_file]


def _fetch_player_data(lb: LeaderboardConfig) -> dict[str, tuple[str, int]]:
    """Reads the sheet and returns {lowercased_lounge_name: (original_name, mmr)}.
 
    Assumes columns A/B are Lounge Name, MMR (in that order), with row 1 as
    a header row. Matching is done against a member's display_name (their
    server nickname), which is expected to exactly equal their Lounge Name
    as long as they have the @player role. Blocking/synchronous - call via
    asyncio.to_thread.
    """
    sheet_cfg = lb.google_sheet
    cache_key = f"{sheet_cfg.credentials_file}:{sheet_cfg.spreadsheet_id}:{sheet_cfg.sheet_name}"
    cached = _sheet_cache.get(cache_key)
    now = time.time()
    if cached and (now - cached["fetched_at"]) < _CACHE_TTL_SECONDS:
        return cached["data"]

    client = _get_client(sheet_cfg.credentials_file)
    worksheet = client.open_by_key(sheet_cfg.spreadsheet_id).worksheet(sheet_cfg.sheet_name)
    rows = worksheet.get_all_values()

    data: dict[str, tuple[str, int]] = {}
    for row in rows[1:]:  # skip header row
        if len(row) < 5:
            continue
        name, mmr_raw = row[0].strip(), row[4].strip()
        if not name:
            continue
        try:
            mmr = int(mmr_raw)
        except ValueError:
            continue
        data[name.lower()] = (name, mmr)
 
    _sheet_cache[cache_key] = {"data": data, "fetched_at": now}
    return data


def invalidate_cache():
    """Clears the cached sheet data, forcing the next lookup to re-fetch from Google Sheets."""
    _sheet_cache.clear()


async def sheets_mmr(lb: LeaderboardConfig, members: list[discord.Member]):
    # gspread's API calls are blocking, so run them off the event loop thread
    data = await asyncio.to_thread(_fetch_player_data, lb)
    players: list[Player | None] = []
    for member in members:
        entry = data.get(member.display_name.strip().lower())        
        if entry is None:
            players.append(None)
        else:
            name, mmr = entry
            players.append(Player(member, name, mmr))
    return players


async def get_mmr(lb: LeaderboardConfig, members: list[discord.Member]):
    return await sheets_mmr(lb, members)