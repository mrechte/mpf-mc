from mpf.config_players.plugin_player import PluginPlayer


class MpfMcSystemPlayer(PluginPlayer):
    """Base class for part of the sound player which runs as part of MPF.

    Note: This class is loaded by MPF and everything in it is in the context of
    MPF, not the mpf-mc. MPF finds this instance because the mpf-mc setup.py
    has the following entry_point configured (see mpf-mc pyproject.toml):
        mc_system_player = "mpfmc.config_players.plugins.mc_system_player:register_with_mpf"

    """
    config_file_section = 'mc_system_player'
    show_section = 'mc_systems'

    def get_express_config(self, value):
        """Parse express config."""
        # breakpoint()
        return {"command": value}


player_cls = MpfMcSystemPlayer


def register_with_mpf(machine):
    """Registers the mc system player plug-in with MPF"""
    return 'mc_system', MpfMcSystemPlayer(machine)
