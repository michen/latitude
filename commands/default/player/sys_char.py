from game.gamesrc.latitude.utils.evennia_color import *
from game.gamesrc.latitude.utils.search import match_character
from ev import settings, default_cmds, utils, search_object, search_player, create_object

class CmdSysChar(default_cmds.MuxPlayerCommand):
    """
    @char - Manage your characters

    Usage:
      look (Only when OOC)
          Displays a welcome message, along with your character listing, and
          instructions on how to go IC and play.

      @char
      @char/list
          Display a list of all your available characters.

      @ic
      @ic <character name>
      @char/ic <character name>
          Use this to 'become' a character.  Your current session (but none of your
          other sessions, if you happen to be connected multiple times) will assume
          the identity of the selected character, and you'll be able to percieve the
          game world and play.
          If you don't supply a character name, it attempt to will pick one for you
          automatically (Such as the last character you used)

      @ooc
      @char/ooc
          Disconnects yourself from your character, and returns you to the connection
          screen, as though you've just logged in
      
      @char/new <character name>
          Creates a new character.

      @char/del <character name>=<password>
          Murder one of your helpless characters.  :(  You need to enter your password
          to preent accidental deletion.  You monster.

          {rWARNING:{n Deleting a character will not release that character's name.  If
          you want to recreate your character, you'll have to select a new name.
    """

    key = "@char"
    aliases = ['@ic', '@ooc']
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        args = self.args
        switches = [switch.lower() for switch in self.switches]

        if self.cmdstring.lower() == 'look' or self.cmdstring.lower() == 'l':
            self.cmd_look()
            return
        elif self.cmdstring.lower() == '@ic' and not switches:
            self.cmd_ic()
            return
        elif self.cmdstring.lower() == '@ooc' and not switches and not args:
            self.cmd_ooc()
            return
        else:
            if (switches == [ 'list' ] or not switches) and not self.args:
                self.cmd_list()
                return
            elif self.switches == [ 'ic' ]:
                self.cmd_ic()
                return
            elif self.switches == [ 'ooc' ] and not self.args:
                self.cmd_ooc()
                return
            elif self.switches == [ 'new' ] and self.args:
                self.cmd_new()
                return
            elif self.switches == [ 'del' ] and self.lhs:
                self.cmd_del()
                return
        # Unrecognized command
        self.msg("Invalid '%s' command.  See 'help %s' for usage" % (self.cmdstring, self.key))

    def cmd_look(self):
        player = self.caller
        character = self.character
        # Display welcome screen
        self.msg('{w/-----------------------------------------------------------------------------\\')
        self.msg('{w| ' + evennia_color_left("{WWelcome, {w%s{W, to the world of {CLatitude MUD{W;" % player.return_styled_name(self.caller), 75) + ' {w|')
        self.msg('{w| ' + evennia_color_right("{Wa massively multiplayer, online text adventure game.", 75) + ' {w|')
        self.msg('{w|                                                                             |')
        self.msg("{w|   {WTo join the game, use {w@char/ic <character name>{W to select a character.    |")
        self.msg('{w|                                                                             |')
        self.msg('{w|  {WSee {whelp{W for more information, or use {wpub <messsage>{W for the public chat.  |')
        self.msg('{w|-----------------------------------------------------------------------------|')
        disabled = player.no_slot_chars()
        characters = player.get_characters()
        characters.sort(cmp=lambda b, a: cmp(a.db.stats_last_puppet_time, b.db.stats_last_puppet_time) or cmp(a.id, b.id))
        max_characters = player.max_characters()
        if max_characters != float('inf'):
            characters.extend([None] * (player.max_characters() - len(characters)))
        if characters:
            while characters:
                char_canvas = EvenniaColorCanvas()
                char_canvas.evennia_import('\n'.join(['{w|                                                                             |'] * 9))
                # Character #1
                if characters:
                    char_option = characters.pop(0)
                    if char_option:
                        char_canvas.draw_string(2, 1, self.character_block(char_option, disabled=char_option in disabled and 'No character slot'))
                    else:
                        char_canvas.draw_string(2, 1, self.empty_block())
                # Character #2
                if characters:
                    char_option = characters.pop(0)
                    if char_option:
                        char_canvas.draw_string(27, 1, self.character_block(char_option, disabled=char_option in disabled and 'No character slot'))
                    else:
                        char_canvas.draw_string(27, 1, self.empty_block())
                # Character #3
                if characters:
                    char_option = characters.pop(0)
                    if char_option:
                        char_canvas.draw_string(52, 1, self.character_block(char_option, disabled=char_option in disabled and 'No character slot'))
                    else:
                        char_canvas.draw_string(52, 1, self.empty_block())
                self.msg(char_canvas.evennia_export())
            self.msg('{w|                                                                             |')
        else:
            self.msg('{w|                                                                             |')
            self.msg('{w|' + evennia_color_center("{WNo characters yet.", 77) + '{w|')
            self.msg('{w|                                                                             |')
            self.msg('{w|' + evennia_color_center("{WUse {w@char/new <character name>{W to create one.", 77) + '{w|')
            self.msg('{w|' + evennia_color_center("{WSee {whelp @char{W for more information.", 77) + '{w|')
            self.msg('{w|                                                                             |')
        self.msg('{w|-----------------------------------------------------------------------------|')
        self.msg('{w|' + evennia_color_center('{WIf you have any questions or comments, email {wstaff@latitude.muck.ca{W.', 77) + '{w|')
        self.msg('{w\\-----------------------------------------------------------------------------/')
        return

    def cmd_list(self):
        player = self.caller
        characters = player.get_characters()
        characters.sort(cmp=lambda a, b: cmp(a.key,b.key))
        self.msg('Your characters: ' + ', '.join([char.return_styled_name(player) for char in characters]))
        if player.no_slot_chars():
            self.msg('\n{RYou appear to have more characters than character slots.  Some of your characters may be inaccessible.')
            self.msg('{RIf you believe this is an error, please contact {rstaff@latitude.muck.ca{R.')

    def cmd_new(self):
        player = self.caller
        key = self.args
        # Verify that the account has a free character slot
        max_characters = player.max_characters()
        playable_characters = player.get_characters()
        if len(playable_characters) >= player.max_characters():
            self.msg("{RYou may only create a maximum of %i characters." % max_characters)
            return
        # Check the character name
        if re.search('[^a-zA-Z0-9._-]', key) or not (3 <= len(key) <= 20):
            self.msg('{RCharacter names must be between 3 and 20 characters, and only contain english letters, numbers, dot (.), underscore (_), or dash(-)')
            return
        # Verify that the character name is not already taken
        for existing_object in search_object(key, attribute_name='key'):
            if utils.inherits_from(existing_object, "src.objects.objects.Character"):
                self.msg("{RThat character name is already taken.")
                return
        # Verify that this is not the name of a player, unless it's your own
        if key.lower() != player.key.lower():
            if search_player(key):
                self.msg("{RThat name is already taken by a player account.")
                return
        # create the character
        from src.objects.models import ObjectDB
        default_home = ObjectDB.objects.get_id(settings.CHARACTER_DEFAULT_HOME)
        typeclass = settings.BASE_CHARACTER_TYPECLASS
        permissions = settings.PERMISSION_PLAYER_DEFAULT
        new_character = create_object(typeclass, key=key, location=default_home, home=default_home, permissions=permissions)
        # only allow creator (and admins) to puppet this char
        new_character.locks.add("puppet:id(%i) or pid(%i) or perm(Janitors)" % (new_character.id, player.id))
        # Set this new character as owned by this player
        new_character.set_owner(player)
        # Configure the character as a new character in the world
        new_character.db.desc = "This is a Player."
        # Inform the user that we're done.
        self.msg("Created new character %s. Use {w%s/ic %s{n to enter the game as this character." % (new_character.key, self.key, new_character.key))

    def character_block(self, character, disabled=False):
        """
        Create a 24x8 info square for a character
        """
        block_canvas = EvenniaColorCanvas()
        block_canvas.evennia_import((disabled and '{R' or '{W') + self.character_border())
        block_canvas.draw_string(1, 1, evennia_color_center(character.return_styled_name(self.caller), 22, dots=True))
        block_canvas.draw_string(1, 3, evennia_color_left('{nSex: %s{n' % (character.return_styled_gender(self.caller)), 12, dots=True))
        block_canvas.draw_string(14, 3, evennia_color_left('{nSta: {g%s{n' % (character.stat_stamina_max()), 9, dots=True))
        if disabled:
            block_canvas.draw_string(1, 6, evennia_color_center('{r' + disabled, 22, dots=True))
        return block_canvas.evennia_export()

    def empty_block(self):
        """
        Create a 24x8 info square, but for an empty slot with no character
        """
        block_canvas = EvenniaColorCanvas()
        block_canvas.evennia_import('{W' + self.character_border())
        block_canvas.draw_string(1, 3, evennia_color_center('{wEMPTY SLOT', 22, dots=True))
        block_canvas.draw_string(1, 4, evennia_color_center('{W{w@char/new{W to create', 22, dots=True))
        return block_canvas.evennia_export()
        

    def character_border(self):
        return (
            '/' + '-' * 22 + '\\\n' +
            ('|' + ' ' * 22 + '|\n') * 6 +
            '\\' + '-' * 22 + '/'
        )

    def cmd_ic(self):
        player = self.caller
        characters = player.get_characters()
        # Determine which character to occupy
        if self.args:
            target = match_character(self.args)
            if not target or not target in characters:
                self.msg("{RThat's not a valid character selection.")
                return
        else:
            target = player.last_puppet()
            if not target or not target in characters:
                self.msg("{RPlease specify a character.  See {r%s/list{R for a list." % (self.key))
                return
        # Puppet the character (and output success/failure messages)
        player.do_puppet(self.sessid, target)

    def cmd_ooc(self):
        # Unpuppet the character (and output success/failure messages)
        self.caller.do_unpuppet(self.sessid)

    def cmd_del(self):
        player = self.caller
        characters = player.get_characters()
        # Find the character to nuke
        target = match_character(self.lhs)
        if not target:
            self.msg("{RThat's not a valid character selection.")
            return
        # Ensure you have permissions
        if not player.user.check_password(self.rhs):
            self.msg("{RPassword incorrect.")
            return
        if not target.access(player, 'char_delete'):
            self.msg("{RYou're not allowed to delete that character.")
            if target in characters:
                self.msg('{RIf you believe this is an error, please contact {rstaff@latitude.muck.ca{R.')
            return
        # Bye bye character
        target_player = target.player
        target_sessid = target.sessid
        # Bye bye character step 1: Unpuppet any player that's currently puppeted
        if target_player:
            target_player.do_unpuppet(target_sessid)
        # Bye bye character step 2: Send the character into the abyss and alert nearby objects
        if target.location:
            target.location.msg_contents('%s disappears.' % (target.key), exclude=[target])
        target.location = None
        target.set_owner(None)
        # Bye bye character step 3: Finalize the deletion, and alert the player(s) involved.
        target_name = target.key
        #target.delete()
        alertus = {player}
        if target_player:
            alertus.add(target_player)
        for alertme in alertus:
            alertme.msg('{rThe character "%s" has been deleted by {c%s{r.' % (target_name, player.return_styled_name(alertme)))