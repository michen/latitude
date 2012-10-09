from ev import default_cmds

class CmdSysReset(default_cmds.CmdReset):
    """
    Reset and reboot the system

    Usage:
      @reset

    A cold reboot. This works like a mixture of @reload and @shutdown,
    - all shutdown hooks will be called and non-persistent scrips will
    be purged. But the Portal will not be affected and the server will
    automatically restart again.
    """
    key = "@reset"
    aliases = ['@reboot']
    locks = "cmd:pperm(reload) or pperm(Custodians)"
    help_category = "--- Coder/Sysadmin ---"

