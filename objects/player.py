from ev import utils, search_object, search_player
from ev import Player as EvenniaPlayer, ansi
import time
import sys

class Player(EvenniaPlayer):
    def basetype_setup(self):
        """
        This sets up the default properties of an Object,
        just before the more general at_object_creation.
        """
        super(Player, self).basetype_setup()
        # Clear any locks set by the default base
        self.locks.replace('')
        # Create friend system variables
        self.db.friends_list = set()
        self.db.friends_requests = set()
        # Empty stats
        self.set_attribute('stats_last_login_time', None)
        self.set_attribute('stats_last_logout_time', None)

    def at_post_login(self, sessid):
        # Update same statistics
        self.db.stats_last_login_time = time.time()
        if self.db.stats_times_login:
            self.db.stats_times_login += 1
        else:
            self.db.stats_times_login = 1

    def at_display_alerts(self, sessid):
        """
        This is called in order to display any general alerts (Such as whether any friends are online, or you have unread mail)
        It's intended to be called after any other output, so that it is not scrolled off by large amounts of text.
        """
        self.execute_cmd("@friends", sessid=sessid)
        if self.db.msg_unseen:
            self.msg('{Y[You have unread messages.  Type "@page" to read them.  See "help @page" for more information]', sessid=sessid)

    def at_display_context(self, sessid):
        """
        Called when the session's context changes (New room, just logged in, etc.)
        This routine is expected to inform the user about where they are and what's going on.  Typically this just means calling 'look'
        """
        character = self.get_puppet(sessid=sessid)
        if character:
            if self.db.pref_automap == None or self.db.pref_automap:
                character.execute_cmd('map', sessid=sessid)
            character.execute_cmd('look', sessid=sessid)
        else:
            self.execute_cmd('look', sessid=sessid)

    def at_disconnect(self, reason=None):
        # Update some statistics
        self.db.stats_last_logout_time = time.time()

    def msg(self, outgoing_string, from_obj=None, data=None, sessid=None):
        if self.db.pref_color != None and not self.db.pref_color:
            outgoing_string = ansi.parse_ansi(outgoing_string, strip_ansi=True)
        self.dbobj.msg(outgoing_string, from_obj=from_obj, data=data, sessid=sessid)

    def bad(self):
        """
        Audits whether the object is corrupted in some way.

        If the object is valid, then None is returned.  If it's broken, then a string
        is returned containing a reason why.
        """
        try:
            if self.db.characters:
                for character in self.db.characters:
                    if character.get_owner() != self:
                        return "some owned characters don't agree with ownership"
        except:
            return "exception raised during audit: " + sys.exc_info()[0]

    def do_puppet(self, sessid, new_character):
        """
        Similar to puppet_object(), only it does some checks first, and outputs status
        information to the session (Whether it succeeds or fails to puppet, it informs
        the player)
        """
        if self.get_puppet(sessid) == new_character:
            self.msg("{R[You already act as %s{R]" % (new_character.get_desc_styled_name(self)), sessid=sessid)
            return
        if new_character in self.no_slot_chars():
            self.msg("{R[%s{R does not have a character slot.  Either delete a character, or acquire more character slots]" % (new_character.get_desc_styled_name(self)), sessid=sessid)
            self.msg("{R[If you believe this is an error, contact{rstaff@latitude.muck.ca{R]", sessid=sessid)
            return
        if not new_character.access(self, "puppet"):
            self.msg("{R[You are not allowed to control that character]" % (new_character.get_desc_styled_name(self)), sessid=sessid)
            self.msg("{R[If you believe this is an error, contact{rstaff@latitude.muck.ca{R]", sessid=sessid)
            return
        if new_character.player and new_character.player != self and new_character.player.is_connected:
            self.msg("{R[%s{R is already acted by another player]" % (new_character.get_desc_styled_name(self)), sessid=sessid)
            return
        if new_character.player:
            # Steal the character (As a safeguard, we allow taking players from other sessions, subject to security checks above.)
            new_character.msg("{R[{c%s{R is now acted from another session]" % (new_character.name), sessid=new_character.sessid)
            self.do_unpuppet(new_character.sessid)
            self.msg("{Y[Taking over {c%s{Y from another session...]" % new_character.name, sessid=sessid)
        if not self.puppet_object(sessid, new_character):
            self.msg("{R[You cannot become {R%s{R]" % new_character.get_desc_styled_name(self), sessid=sessid)

    def do_unpuppet(self, sessid):
        """
        Similar to unpuppet_object(), only it does some checks first, and outputs
        status information to the session (Whether it succeeds or fails to unpuppet,
        it informs the player)
        """
        old_char = self.get_puppet(sessid)
        if not old_char:
            self.msg('{R[You are already OOC]', sessid=sessid)
            return
        if self.unpuppet_object(sessid):
            self.msg("\n{G[You go OOC]\n", sessid=sessid)
            self.at_display_context(sessid=sessid)
        else:
            raise RuntimeError("Could not unpuppet!")

    def last_puppet(self):
        """
        Find the most recently puppeted character, or return None.
        """
        most_recent = None
        for character in self.get_characters():
            if not character.db.stats_last_puppet_time:
                continue
            if not most_recent or character.db.stats_last_puppet_time > most_recent.db.stats_last_puppet_time:
                most_recent = character
        return most_recent

    def no_slot_chars(self):
        """
        Returns the characters that we don't have enough slots for.  Characters with
        no slot (due to the player having insufficient slots) should not be puppeted,
        but they're still owned by the player.  (For example, paging them will still
        reach the player.  They'll still show in friend lists, etc.)
        """
        characters = self.get_characters()
        max_characters = self.max_characters()
        if len(characters) < max_characters:
            return []
        # Overbudget
        characters = sorted(characters, cmp=lambda b, a: cmp(a.db.stats_last_puppet_time, b.db.stats_last_puppet_time) or cmp(a.id, b.id))
        return characters[max_characters:]

    def get_desc_styled_name(self, looker=None):
        if self.status_online():
            return '{b' + self.key
        else:
            return '{B' + self.key

    def status_online(self):
        """
        Returns the amount of time a player has been online.

        It takes 'friend system' privacy into account, returning 'None' if only private characters are puppeted.
        """
        # If we're actually offline then we'll show that way.
        if not self.sessions:
            return None
        # If we have any un-hidden puppets, then we'll show as online
        puppets = self.get_all_puppets()
        if puppets:
            only_optout = True
            for char in puppets:
                if not char.db.friends_optout:
                    only_optout = False
                    break
        else:
            # If we have no puppets, then we'll show as online.
            only_optout = False
        if only_optout:
            return None
        # Looks like we're online and we want to show that way.  Return seconds online of the longest lived session.
        now = time.time()
        online_time = float('-inf')
        for session in self.sessions:
            session_online = now - session.conn_time
            if session_online > online_time:
                online_time = session_online
        return online_time

    def status_idle(self):
        """
        Returns the idle time of the player, in seconds.

        Returns None if the player is offline.
        """
        if self.status_online():
            now = time.time()
            idle_time = float('inf')
            # Return the session with the lowest idle time
            for session in self.sessions:
                session_idle = now - session.cmd_last_visible
                if session_idle < idle_time:
                    idle_time = session_idle
            return idle_time
        else:
            return None

    def max_characters(self):
        """
        Get the maximum number of characters this player is allowed to have associated with their account
        """
        # Admins can have as many characters as they want
        if 'Janitors' in self.permissions or 'Custodians' in self.permissions:
            return float('inf')
        # Start with the default number of characters
        max_characters = 3
        # Apply bonuses
        if self.db.account_bonus_list and 'CHAR_SLOT' in self.db.account_bonus_list:
            max_characters += self.db.account_bonus.count('CHAR_SLOT')
        if self.db.account_bonus_set and 'LAT1' in self.db.account_bonus_set:
            max_characters += 6
        return max_characters

    def get_characters(self, online_only=False):
        """
        Return a list of characters owned by this player.
        """
        if online_only:
            character_candidates = self.get_all_puppets()
        else:
            character_candidates = self.db.characters or []
        return set(char for char in character_candidates if char.get_owner() == self)

    def is_friends_with(self, player):
        """
        Retuns whether a this player is friends with another player.  (Friendship is always mutual)
        """
        if not player or player == self:
            return False
        return self in player.db.friends_list and player in self.db.friends_list

    def get_friend_players(self, online_only=False):
        """
        Get a list of this player's friend players.  (Friendship is always mutual)
        """
        # If there are any deleted players in the friend list, clear them out
        if None in self.db.friends_list:
            self.db.friends_list.remove(None)
        # Although it's a touching sentiment, you can't add yourself to your friend list and expect it to work
        if self in self.db.friends_list:
            self.db.friends_list.remove(self)
        # Generate the list of friends
        friend_players = set()
        for friend in self.db.friends_list:
            if self.is_friends_with(friend):
                if not online_only or friend.status_online():
                    friend_players.add(friend)
        return friend_players

    def get_friend_characters(self, online_only=False):
        """
        Get a list of all the characters of this player's friends.
        Friendship between players is always mutual, but individual characters can be flagged as hidden from the friend system.
        """
        # Build up a set of characters and return
        friend_characters = set()
        for friend_player in self.get_friend_players():
            for friend_character in friend_player.get_characters(online_only=online_only):
                if friend_character.db.friends_optout:
                    continue
                if online_only and not (friend_character.status_online() or friend_character.player):
                    continue
                friend_characters.add(friend_character)
        return friend_characters

    def get_friends_optout(self):
        """
        Returns whether any currently connected characters are opped out from the friend system.
        """
        for char in self.get_all_puppets():
            if char.db.friends_optout:
                return True
        return False

