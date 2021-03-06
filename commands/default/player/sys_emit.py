from ev import default_cmds
from game.gamesrc.latitude.commands.latitude_command import LatitudeCommand

class CmdSysEmit(LatitudeCommand):
    """
    @emit - Emit a message

    Usage:
      @emit[/switches] [<obj>, <obj>, ... =] <message>
        Emits a message to the selected objects or to your immediate surroundings.
        If the object is a room, send to its contents.

      @emit/players [<obj>, <obj>, ... =] <message>
      @remit [<obj>, <obj>, ... =] <message>
        Same as @emit, but only works for room objects.

      @emit/room [<obj>, <obj>, ... =] <message>
      @pemit [<obj>, <obj>, ... =] <message>
        Same as @emit, but only works for player objects.

    Switches:
      contents : send to the contents of matched objects too
    """
    key = "@emit"
    aliases = ["@remit", "@pemit"]
    locks = "cmd:perm(command_@emit) or perm(Janitors)"
    help_category = "=== Admin ==="
    arg_regex = r"(/\w+?(\s|$))|\s|$"
    logged = True

    def func(self):
        "Implement the command"

        caller = self.player
        args = self.args

        if not args:
            string = "Usage: "
            string += "\n@emit[/switches] [<obj>, <obj>, ... =] <message>"
            string += "\n@remit           [<obj>, <obj>, ... =] <message>"
            string += "\n@pemit           [<obj>, <obj>, ... =] <message>"
            caller.msg(string)
            return

        rooms_only = 'rooms' in self.switches
        players_only = 'players' in self.switches
        send_to_contents = 'contents' in self.switches

        # we check which command was used to force the switches
        if self.cmdstring == '@remit':
            rooms_only = True
        elif self.cmdstring == '@pemit':
            players_only = True

        if not self.rhs:
            message = self.args
            objnames = [caller.location.key]
        else:
            message = self.rhs
            objnames = self.lhslist

        # send to all objects
        for objname in objnames:
            obj = caller.search(objname, global_search=True)
            if not obj:
                return
            if rooms_only and not obj.location == None:
                caller.msg("%s is not a room. Ignored." % objname)
                continue
            if players_only and not obj.has_player:
                caller.msg("%s has no active player. Ignored." % objname)
                continue
            obj.msg(message)
            if send_to_contents:
                for content in obj.contents:
                    content.msg(message)
                caller.msg("Emitted to %s and its contents." % objname)
            else:
                caller.msg("Emitted to %s." % objname)

