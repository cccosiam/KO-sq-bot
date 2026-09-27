from models import BotConfig
import json
import msgspec


def _normalize_config(config_body: dict):
    servers = {}
    for server_id, server_config in config_body.get("servers", {}).items():
        leaderboards = {}
        for leaderboard_name, leaderboard_config in server_config.get("leaderboards", {}).items():
            normalized = dict(leaderboard_config)
            normalized.setdefault("name", leaderboard_name)
            normalized.setdefault("lb_name_in_string", False)
            normalized.setdefault("room_size", normalized.get("players_per_mogi", 0))
            normalized.setdefault("valid_formats", [])
            normalized.setdefault("pinged_member_ids", [])
            normalized.setdefault("queue_messages", True)
            normalized.setdefault("sec_between_queue_msgs", 0)

            website_credentials = dict(normalized.get("website_credentials", {}))
            website_credentials.setdefault("game", None)
            normalized["website_credentials"] = website_credentials

            time_settings = dict(normalized.get("time_settings", {}))
            normalized["time_settings"] = time_settings

            leaderboards[leaderboard_name] = normalized

        servers[server_id] = {
            "admin_roles": server_config.get("admin_roles", []),
            "staff_roles": server_config.get("staff_roles", []),
            "leaderboards": leaderboards,
        }

    return {
        "token": config_body.get("token", ""),
        "application_id": config_body.get("application_id", 0),
        "servers": servers,
    }


def get_config(filename: str):
    with open(filename, 'r') as cjson:
        config_body = json.load(cjson)
    normalized_config = _normalize_config(config_body)
    config = msgspec.convert(normalized_config, BotConfig, strict=False)
    return config
