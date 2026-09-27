from dataclasses import dataclass, field
from typing import Optional

@dataclass
class GoogleSheetsCredentials:
    spreadsheet_id: str  # the ID from the sheet's URL: docs.google.com/spreadsheets/d/<THIS PART>/edit
    sheet_name: str = "Sheet1"  # name of the tab/worksheet within the spreadsheet
    credentials_file: str = "service_account.json"  # path to the Google service account JSON key file

@dataclass
class TimeSettings:
    queue_open_time: int # number of minutes before scheduled time of the queue that players can start joining
    joining_time: int # number of minutes after queue_open_time that players have to join the queue
    extension_time: int # number of minutes the queue can be extended to get a divisible # of teams

@dataclass
class LeaderboardConfig:
    name: str = ""
    lb_name_in_string: bool = False # if this is true, it will show the lb name in the event string,
                                    # for example if lb name is 24p, it will say "24p 2v2" instead of "2v2"
    google_sheet: GoogleSheetsCredentials = field(default_factory=lambda: GoogleSheetsCredentials(spreadsheet_id=""))
    time_settings: TimeSettings = field(default_factory=lambda: TimeSettings(queue_open_time=0, joining_time=0, extension_time=0))
    room_size: int = 0
    valid_formats: list[int] = field(default_factory=list)
    join_channel: int = 0
    list_channel: int = 0
    pinged_member_ids: list[int] = field(default_factory=list) # discord IDs of members that get pinged into every room thread
    queue_messages: bool = True
    sec_between_queue_msgs: int = 0
    
@dataclass
class ServerConfig:
    admin_roles: list[int]
    staff_roles: list[int]
    leaderboards: dict[str, LeaderboardConfig]

@dataclass
class BotConfig:
    token: str
    application_id: int
    servers: dict[int, ServerConfig]