# ../gungame/plugins/custom/gg_scoreboard/configuration.py

"""Creates the gg_scoreboard configuration."""

# =============================================================================
# >> IMPORTS
# =============================================================================
# GunGame
from gungame.core.config.manager import GunGameConfigManager

# Plugin
from .info import info


# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = (
    'multi_kill',
)


# =============================================================================
# >> CONFIGURATION
# =============================================================================
with GunGameConfigManager(info.name) as config:

    with config.cvar('multi_kill') as multi_kill:
        multi_kill.add_text()
