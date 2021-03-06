from game.gamesrc.latitude.commands.latitude_command import LatitudeCommand

class CmdUnlock(LatitudeCommand):
    """
    unlock - Unlock things
   
    Usage:
      unlock <object>
        Attempt to unlock <object>, so it can be opened or used.
    """
    key = "unlock"
    locks = "cmd:all()"
    help_category = "Actions"
    arg_regex = r"\s.*?|$"

    # auto_help = False      # uncomment to deactive auto-help for this command.
    # arg_regex = r"\s.*?|$" # optional regex detailing how the part after
                             # the cmdname must look to match this command.

    def func(self):
        if not self.args:
	    self.msg('Unlock what?')
	    return()
        obj = self.character.search(self.args)
	if not obj:
	    return()
	obj.action_unlock(self.character)
