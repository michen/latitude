from ev import default_cmds

class CmdSysTeleport(default_cmds.CmdTeleport):
    """
    teleport

    Usage:
      @tel/switch [<object> =] <location>

    Switches:
      quiet  - don't echo leave/arrive messages to the source/target
               locations for the move.
      intoexit - if target is an exit, teleport INTO
                 the exit object instead of to its destination

    Teleports an object or yourself somewhere.
    """
    key = "@tel"
    aliases = "@teleport"
    locks = "cmd:perm(command_@teleport) or perm(Janitors)"
    help_category = "=== Admin ==="
    arg_regex = r"(/\w+?(\s|$))|\s|$"
