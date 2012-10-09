from ev import default_cmds

class CmdGet(default_cmds.CmdGet):
    """
    get

    Usage:
      get <obj>

    Picks up an object from your location and puts it in
    your inventory.
    """
    key = "get"
    locks = "cmd:all()"
    help_category = "Actions"
