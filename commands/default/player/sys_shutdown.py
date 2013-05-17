from ev import default_cmds

class CmdSysShutdown(default_cmds.CmdShutdown):

    """
    @shutdown

    Usage:
      @shutdown [announcement]

    Gracefully shut down both Server and Portal.
    """
    key = "@shutdown"
    locks = "cmd:pperm(commandy_@shutdown) or pperm(Custodians)"
    help_category = "--- Coder/Sysadmin ---"

