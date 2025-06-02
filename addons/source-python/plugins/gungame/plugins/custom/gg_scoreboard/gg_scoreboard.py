# ../gungame/plugins/custom/gg_scoreboard/gg_scoreboard.py

"""Shows player GunGame levels on the scoreboard."""

# =============================================================================
# >> IMPORTS
# =============================================================================
# Python
import binascii
import json

# Source.Python
from core import GAME_NAME, PLATFORM
from events import Event
from filters.entities import EntityIter
from memory import Convention, DataType, find_binary
from memory.hooks import PreHook
from players.helpers import userid_from_pointer
from players.teams import team_managers

# GunGame
from gungame.core.paths import GUNGAME_DATA_PATH
from gungame.core.players.attributes import AttributePostHook
from gungame.core.players.dictionary import player_dictionary
from gungame.core.plugins.manager import gg_plugin_manager
from gungame.core.status import GunGameMatchStatus, GunGameStatus
from gungame.core.teams import team_levels

# Plugin
from .configuration import multi_kill
from .info import info

# =============================================================================
# >> GLOBAL VARIABLES
# =============================================================================
_data_file = GUNGAME_DATA_PATH / info.name + ".json"
with _data_file.open() as _open_file:
    _data = json.load(_open_file).get(GAME_NAME, {}).get(PLATFORM, {})
if not _data:
    msg = f'Game "{GAME_NAME}" on platform "{PLATFORM}" not currently supported'
    raise NotImplementedError(msg)

if PLATFORM == "windows":
    for _key, _value in _data.items():
        _data[_key] = binascii.unhexlify(_value.replace(" ", ""))

server = find_binary("server")

IncrementFragCount = server[_data["IncrementFragCount"]].make_function(
    Convention.THISCALL,
    [DataType.POINTER, DataType.INT],
    DataType.VOID,
)

IncrementDeathCount = server[_data["IncrementDeathCount"]].make_function(
    Convention.THISCALL,
    [DataType.POINTER, DataType.INT],
    DataType.VOID,
)

# =============================================================================
# >> ENTITY HOOKS
# =============================================================================
@PreHook(IncrementFragCount)
def _pre_hook_frag(stack_data):
    if GunGameStatus.MATCH is not GunGameMatchStatus.ACTIVE:
        return

    if "gg_teamplay" in gg_plugin_manager:
        return
    player = player_dictionary[userid_from_pointer(stack_data[0])]
    stack_data[1] = player.level - player.kills


@PreHook(IncrementDeathCount)
def _pre_hook_death(stack_data):
    if GunGameStatus.MATCH is not GunGameMatchStatus.ACTIVE:
        return

    if "gg_teamplay" in gg_plugin_manager:
        return
    player = player_dictionary[userid_from_pointer(stack_data[0])]
    value = _get_deaths(player)
    if value is not None:
        stack_data[1] = value - player.deaths


# =============================================================================
# >> ATTRIBUTE HOOKS
# =============================================================================
@AttributePostHook("multi_kill")
def _hook_multi_kill(player, *args):
    """Set the player's deaths to their multi_kill."""
    if "gg_teamplay" not in gg_plugin_manager:
        value = _get_deaths(player)
        if value is not None:
            player.deaths = value


# =============================================================================
# >> GAME EVENTS
# =============================================================================
@Event("round_start", "round_end")
def _round_start(game_event):
    if GunGameStatus.MATCH is not GunGameMatchStatus.ACTIVE:
        return

    if not gg_plugin_manager.is_team_game:
        return

    for class_name in team_managers:
        for entity in EntityIter(class_name):
            if entity.team not in team_levels:
                continue
            entity.score = team_levels[entity.team]


@Event("player_spawn")
def _set_score_on_spawn(game_event):
    """Set the player's score to their level."""
    if GunGameStatus.MATCH is not GunGameMatchStatus.ACTIVE:
        return

    if "gg_teamplay" in gg_plugin_manager:
        return

    player = player_dictionary[game_event["userid"]]
    if player.level is None:
        return

    player.kills = player.level
    value = _get_deaths(player)
    if value is not None:
        player.deaths = value


# =============================================================================
# >> GUNGAME EVENTS
# =============================================================================
@Event("gg_level_up", "gg_level_down")
def _set_score_on_level(game_event):
    """Set the player's score to their level."""
    if "gg_teamplay" in gg_plugin_manager:
        return

    player = player_dictionary[game_event["leveler"]]
    player.kills = player.level


@Event("gg_team_level_up")
def _set_team_level(game_event):
    for class_name in team_managers:
        for entity in EntityIter(class_name):
            if entity.team != game_event["team"]:
                continue

            entity.score = game_event["new_level"]
            return


# =============================================================================
# >> HELPER FUNCTIONS
# =============================================================================
def _get_deaths(player):
    """Set the player's deaths to their multi_kill."""
    if not player.level:
        return None

    value = int(multi_kill)
    if value not in (1, 2):
        return None

    # Should the actual multi_kill value be used?
    if value == 1:
        return player.multi_kill

    # Should the number of kills remaining be used?
    return player.level_multi_kill - player.multi_kill
