from ev import default_cmds

class CmdSysUnLink(default_cmds.CmdUnLink):
    """
    @unlink - unconnect objects

    Usage:
      @unlink <Object>

    Unlinks an object, for example an exit, disconnecting
    it from whatever it was connected to.
    """
    # this is just a child of CmdLink

    key = "@unlink"
    locks = "cmd:pperm(command_@unlink) or pperm(Custodians)"
    help_category = "--- Coder/Sysadmin ---"

