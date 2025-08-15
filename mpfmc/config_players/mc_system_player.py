"""Contains the system command config player class"""
from collections import namedtuple
from copy import deepcopy
from typing import Dict, List
from subprocess import run, Popen, PIPE, CalledProcessError
from mpfmc.core.mc_config_player import McConfigPlayer

SystemBlock = namedtuple("SystemBlock", ["priority", "context"])


class McSystemPlayer(McConfigPlayer):
    """Base class for the System command Player that runs on the mpf-mc side of things.
    It receives all of its instructions via BCP from a MpfSoundPlayer instance
    running as part of MPF.

    The sound_player: section of a config file (either the machine-wide or
    a mode-specific config) looks like this:

    sound_player:
        <event_name>:
            <sound_name>:
                <sound_settings>: ...

    The express config just puts a sound_name next to an event.

    sound_player:
        some_event: sound_name_to_play

    If you want to control other settings (such as track, priority, volume,
    loops, etc.), enter the sound name on the next line and the settings
    indented under it, like this:

    sound_player:
        some_event:
            sound_name_to_play:
                volume: 0.35
                max_queue_time: 1 sec

Here are several various examples:

    sound_player:
        some_event:
            sound1:
                volume: 0.65

        some_event2:
            sound2:
                volume: -4.5 db
                priority: 100
                max_queue_time: 500 ms

        some_event3: sound3

    """
    config_file_section = 'mc_system_player'
    show_section = 'mc_systems'

    def __init__(self, machine) -> None:
        """initialize variable player."""
        super().__init__(machine)
        # self.log = logging.getLogger('McSystemPlayer')
        self.blocks = {}    # type: Dict[str, List[SystemBlock]]

    # pylint: disable=invalid-name,too-many-branches
    def play(self, settings, context, calling_context, priority=0, **kwargs):  # noqa: MC0001
        """Plays a validated sounds: section from a sound_player: section of a
        config file or the sounds: section of a show.

        The config must be validated. Validated config looks like this:

        <sound_name>:
            <settings>: ...

        <settings> can be:

        action:
        priority:
        volume:
        ducking:
        loops:
        max_queue_time:
        block:

        Notes:
         -  Ducking settings only apply to sound assets without ducking config
            (i.e. sound asset ducking overrides sound_player ducking)
         -  Markers cannot currently be specified/overridden in the sound_player
            (they must be specified in the sounds section of a config file).

        """
        #settings = deepcopy(settings)
        for command_name, s in settings.items():
            command = s['command']
            shell = s.get('shell', True)
            params = s.get('params', [])
            block = s.get('block', False)

            if not command:
                self.machine.log.error("McSystemPlayer: missing command for %s" % command_name)
                return
            
            self.machine.log.info("McSystemPlayer: launching command %s (%s)" % (command_name, command))

            try:
                # Construire la commande complète
                full_command = [command] + (params if params else [])

                # Run the command
                if block:
                    # Exécution bloquante
                    result = run(
                        full_command,
                        shell=shell,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    self.machine.log.info(f"McSystemPlayer: command successufully run: {full_command}, Result: {result.stdout}")
                else:
                    # Exécution non bloquante
                    Popen(
                        full_command,
                        shell=shell,
                        stdout=PIPE,
                        stderr=PIPE,
                        text=True
                    )
                    self.machine.log.info(f"McSystemPlayer: command launched in non blocking mode: {full_command}")        
            except CalledProcessError as e:
                self.machine.log.error(f"McSystemPlayer: error while executing command {full_command}: {e.stderr}")
            except Exception as e:
                self.machine.log.error(f"McSystemPlayer: unexpected error: {str(e)}")        


    def get_express_config(self, value):
        """Express config for commands is simply a string (command with arguments)."""
        # breakpoint()
        return {"command": value}

"""
    # pylint: disable=too-many-branches
    def validate_config(self, config):
        ""Validates the sound_player: section of a config file (either a
        machine-wide config or a mode config).

        Args:
            config: A dict of the contents of the sound_player section
            from the config file. It's assumed that keys are event names, and
            values are settings for what the sound_player should do when that
            event is posted.

        Returns: A dict a validated entries.

        This method overrides the base method since the sound_player has
        unique options.

        ""
        # first, we're looking to see if we have a string, a list, or a dict.
        # if it's a dict, we look to see whether we have the name of some sound

        validated_config = dict()

        for event, settings in config.items():
            #breakpoint()

            if isinstance(settings, str):
                settings = self.get_express_config(settings)

            if not isinstance(settings, dict):
                raise ValueError("McSystemPlayer: An invalid setting for event '{}' ".format(event))
            
            validated_config[event] = {
                'command': self._validate_config_item(settings, 'command'),
                'shell': self._validate_config_item(settings, 'shell'),
                'block': self._validate_config_item(settings, 'block'),
                'params': self._validate_config_item(settings, 'params'),
            }

        return validated_config
"""


McPlayerCls = McSystemPlayer
