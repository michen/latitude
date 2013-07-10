from ev import Object as EvenniaObject
from ev import Exit as EvenniaExit
from ev import Room as EvenniaRoom
from ev import Character as EvenniaCharacter
from ev import utils
import re

class Object(EvenniaObject):
    def basetype_setup(self):
        """
        This sets up the default properties of an Object,
        just before the more general at_object_creation.
        """
        super(Object, self).basetype_setup()
        # Clear the locks assigned by the built in Evennia base class
        self.locks.replace("")
        # Set the default permissions which apply to all objects.
        # This is sparse because the base object class is not intended to be used directly for objects in the world.
        self.locks.add(";".join([
            "call:false()",                  # allow to call commands on this object (Used by the system itself)
            "puppet:id(%s) or pperm(Janitors)" % self.dbref,
        ])) # restricts puppeting of this object

    # ----- Lock Messages -----
    def at_access_failure(self, accessing_obj, access_type):
        if not isinstance(accessing_obj, Object):
            # Don't bother with players, or any other type of object which may be making an access call.
            # For one, we can't get a player's session id to send messages out.
            return
        # Ignore access types used directly by the Evennia engine
        if access_type == 'call':
            return
        # Otherwise, create a default message
        message_table = {
            'get' : "{RYou can't pick that up",
            'drop' : "{RYou can't drop that",
            'rename' : "{RYou can't rename that object",
            'edit' : "{RYou can't edit that object",
            'edit_gender' : "{RYou can't edit the {rgender{R of that object",
            'edit_appearance' : "{RYou can't edit the {rappearance{R of that object",
            'edit_aura' : "{RYou can't edit the {raura{R of that object",
            'edit_flavor' : "{RYou can't edit the {rflavor{R of that object",
            'edit_scent' : "{RYou can't edit the {rscent{R of that object",
            'edit_sound' : "{RYou can't edit the {rsound{R of that object",
            'edit_texture' : "{RYou can't edit the {rtexture{R of that object",
            'edit_writing' : "{RYou can't edit the {rwriting{R on that object",
            'leave' : "{RYou can't leave this area right now.",
            'kick_occupant' : "{RYou aren't allowed to kick a character from that location.",
            'follow' : None, # Follow system handles this by sending a follow request.
            'lead' : None, # Follow system handles this by sending a lead request.
        }
        if access_type in message_table:
            message = message_table[access_type]
        else:
            message = '{RAccess denied ({r%s{R)' % (access_type)
        if message:
            accessing_obj.msg('{R[ %s{R ]' % message, sessid=accessing_obj.sessid)

    def at_access_success(self, accessing_obj, access_type):
        # Check for a message property (sending nothing by default)
        if self.db.access_failure and access_type in self.db.access_failure and self.db.access_failure[access_type] != None:
            accessing_obj.msg(self.db.access_failure[access_type])

    # ----- Auditing -----
    def bad(self):
        """
        Audits whether the object is corrupted in some way, such as being a direct
        instance of the Object class, rather than a child class.

        If the character is valid, then None is returned.  If it's broken, then a
        string is returned containing a reason why.
        """
        if type(self) is Object:
            return "object is a base 'Object' class"
        # Equipment
        for item in self.db.equipment:
            if item.get_equipper() != self:
                return 'character and item data conflict (%s)' % item.key
        return None

    # ----- Utilities -----
    def trace(self):
        """
        Returns all objects up the tree starting with this object and ending with a base object.
        """
        objects = [self]
        while True:
            location = objects[-1].location
            if not location:
                break
            if location in objects:
                raise Exception('Object loop detected!  ' + obj.dbref + ' contains itself!')
            objects.append(location)
        return objects

    def get_area(self):
        """
	Ascends the tree until it hits the first area, and returns it.
	"""
        for obj in self.trace():
            if utils.inherits_from(obj, 'game.gamesrc.latitude.objects.area.Area'):
                return obj
        return None

    def get_region(self):
        """
	Ascends the tree until it hits the first region, and returns it.
	"""
        for obj in self.trace():
            if utils.inherits_from(obj, 'game.gamesrc.latitude.objects.region.Region'):
                return obj
        return None

    def get_character(self):
        """
	Ascends the tree until it hits the first character, and returns it.
	"""
        for obj in self.trace():
            if isinstance(obj, EvenniaCharacter):
                return obj
        return None

    def get_room(self):
        """
	Ascends the tree until it hits the first room, and returns it.
	"""
        for obj in self.trace():
            if isinstance(obj, EvenniaRoom):
                return obj
        return None

    def is_inside(self, obj):
        """
	Ascends the tree to determine if this object is inside obj
	"""
        obj_seen = set([self])
        parent = self.location
        while parent:
            if parent in obj_seen:
                raise Exception('Object loop detected!  ' + parent.dbref + ' contains itself!')
            obj_seen.add(parent)
	    if parent == obj:
	        return True
            parent = parent.location
	return False

    def alias_highlight_name(self):
        """
        Returns the name of the object with its shortest matching alias
        highlighted, so viewers will know that they don't have to type the
        entire name.

        For example
        key='East', aliases=['east', 'e'] = '[E]ast'
        """
        key = self.key
        aliases = sorted(self.aliases, key=lambda alias: (len(alias), alias))
        # If there's no aliases, just return the name
        if not self.aliases:
            return key
        # Check for an alias that's inside the name
        for alias in aliases:
            if re.search(r'(^|(?<=\s))%s' % (re.escape(alias)), key, flags=re.IGNORECASE):
                return re.sub(r'(^|(?<=\s))%s' % (re.escape(alias)), lambda m: '[%s]' % (m.group(0)), key, count=1, flags=re.IGNORECASE)
        # Simply return the smallest alias
        return '[%s] %s' % (aliases[0], key)

    # ----- Descriptions -----
    def get_desc_styled_name(self, looker=None):
        """
        Returns the name of this object, styled (With colors, etc.) to help identify
        the type of the object.  This is used when displaying lists of objects, or
        examining the object data, or any other situation where it would be convenient
        to be able to identify the type of an object at a glance. (@who, @examine,
        inventory, the contents of rooms when doing a 'look', etc.)

        * This can also be used to create special glasses for administrators, where
        when you see the title of an object, it's accompanied by its database ID, or
        other technical details.

        * This can also be used to see at a glance whether a user is online or not.
        """
        # You shouldn't create any Objects directly.  This is meant to be a pure base class.
        # So, make an accordingly ominous looking name.
        return '{x<<' + self.key + '>>'

    def get_desc_styled_gender(self, looker=None):
        """
        Returns the gender of this object, styled (With colors, etc.).
        """
        gender = self.get_desc_gender()
        if not gender:
            gender = '%cn%cr-Unset-'
        elif self.is_male():
            gender = '%cn%ch%cb' + gender
        elif self.is_female():
            gender = '%cn%ch%cm' + gender
        elif self.is_herm():
            gender = '%cn%ch%cg' + gender
        else:
            gender = '%cn%ch%cw' + gender
        return gender

    def get_desc_appearance(self, looker=None):
        """
        Describes the appearance of this object.  Used by the "look" command.
	This method, by default, delegates its desc generation into several other calls on the object.
	   get_desc_appearance_name for the name of the object. (Which defaults to showing nothing)
	   get_desc_apperaance_desc to generate the main description of the room.
           get_desc_appearance_exits to generate a line that shows you which exits are available for you to take
	   get_desc_appearance_contents to generate the description of the contents of the object
	      (This, itself, calls get_desc_appearance_contents_header if there are any contents to get the 'Carrying:' line by default)
	"""
        # By default, construct the appearance by calling other methods on the object
	descs = [self.get_desc_appearance_name(looker), self.get_desc_appearance_desc(looker), self.get_desc_appearance_exits(looker), self.get_desc_appearance_contents(looker)]
	descs = [desc for desc in descs if desc != None]
	return '\n' + '\n'.join(descs)

    def get_desc_appearance_name(self, looker=None):
        """
	Return the name portion of the visual description.
	"""
        return self.get_desc_styled_name(looker=looker)

    def get_desc_appearance_desc(self, looker=None):
        """
	Return the main portion of the visual description.
	"""
        desc = self.db.desc_appearance
	if desc != None:
	    return '%cn' + self.objsub(desc)
	else:
	    return '%cnYou see nothing special.'

    def get_desc_appearance_exits(self, looker=None):
        """
	Return a line that describes the visible exits in the object.
	"""
        # get and identify all objects
        visible = (con for con in self.contents if con != looker)
        exits = []
        for con in visible:
            if isinstance(con, EvenniaExit):
                exits.append(con.alias_highlight_name())

        if exits:
            return '%ch%cx[Exits: ' + ', '.join(exits) + ']%cn'
	else:
	    return None

    def get_desc_appearance_contents(self, looker):
        """
	Return a descriptive list of the contents held by this object.
	"""
        visible = [con for con in self.contents if con != looker]
        exits, users, things = [], [], []
        for con in visible:
            if isinstance(con, EvenniaExit):
	        exits.append(con.key)
            elif con.player:
                users.append(con.get_desc_styled_name(looker))
            else:
                things.append(con.get_desc_styled_name(looker))
        if users or things:
            string = self.get_desc_appearance_contents_header(looker)
            if users:
                string += '\n%ch%cc' + '\n'.join(users) + '%cn'
            if things:
                string += '\n%cn%cc' + '\n'.join(things) + '%cn'
            return string
	else:
	    return None

    def get_desc_appearance_contents_header(self, looker=None):
        """
	Returns a header line to display just before outputting the contents of the object.
	"""
        return '%ch%cbContents:%cn'

    def get_desc_scent(self, looker=None):
        """
	Returns the scent description of the object.
	"""
        if self.db.desc_scent:
	    return self.objsub(self.db.desc_scent)
	else:
	    return self.objsub("&0C doesn't seem to have any descernable scent.")

    def get_desc_texture(self, looker=None):
        """
	Returns the scent description of the object.
	"""
        if self.db.desc_texture:
	    return self.objsub(self.db.desc_texture)
	else:
	    return self.objsub("&0C doesn't seem to have any descernable texture.")

    def get_desc_flavor(self, looker=None):
        """
	Returns the scent description of the object.
	"""
        if self.db.desc_flavor:
	    return self.objsub(self.db.desc_flavor)
	else:
	    return self.objsub("&0C doesn't seem to have any descernable flavor.")

    def get_desc_sound(self, looker=None):
        """
	Returns the scent description of the object.
	"""
        if self.db.desc_sound:
	    return self.objsub(self.db.desc_sound)
	else:
	    return self.objsub("&0C doesn't seem to have any descernable sound.")

    def get_desc_aura(self, looker=None):
        """
	Returns the scent description of the object.
	"""
        if self.db.desc_aura:
	    return self.objsub(self.db.desc_aura)
	else:
	    return self.objsub("&0C doesn't seem to have any descernable aura.")

    def get_desc_writing(self, looker=None):
        """
	Returns the scent description of the object.
	"""
        if self.db.desc_writing:
	    return self.objsub(self.db.desc_writing)
	else:
	    return self.objsub("&0C doesn't seem to have any descernable writing.")

    def get_desc_gender(self, looker=None):
        """
        Returns the gender description of the object.  (Typically one word)
        """
        if self.db.desc_gender:
            return self.db.desc_gender
        else:
            return 'thing'

    def get_desc_species(self, looker=None):
        """
        Returns the species description of the object.  (Typically less than 25 characters)
        """
        if self.db.desc_species:
            return self.db.desc_species
        else:
            return 'Object'

    # ----- Maps -----
    def get_desc_map(self, mark_friends_of=None):
        """
	Return an ascii image representing the location of the object for helping users to navigate.
	"""
	room = self.get_room()
	if hasattr(room, 'get_desc_map'):
	    return room.get_desc_map(mark_friends_of)
	return None

    # ----- Gender -----
    def is_male(self):
        return self.get_desc_gender().lower().strip() in ['male', 'man', 'boy', 'dude', 'him']

    def is_female(self):
        return self.get_desc_gender().lower().strip() in ['female', 'woman', 'girl', 'chick', 'lady', 'her']

    def is_herm(self):
        return self.get_desc_gender().lower().strip() in ['herm', 'hermy', 'both', 'shemale']

    def is_neuter(self):
        return self.get_desc_gender().lower().strip() in ['neuter', 'asexual', 'it', 'thing', 'object', 'machine', 'genderless', 'sexless']

    def is_androgynous(self):
        return not self.is_male() and not self.is_female() and not self.is_herm() and not self.is_neuter()

    # ----- Event Hooks -----
    def at_desc(self, looker):
        pass

    def at_desc_scent(self, looker):
        if not looker.location or (not looker.location == self.location and not looker.location == self):
            return()
        self.msg(self.objsub('&1N just smelled you!', looker))
        if looker.location:
            looker.location.msg_contents(self.objsub('&1N just smelled &0c.', looker), exclude=[self, looker])

    def at_desc_flavor(self, looker):
        if not looker.location or (not looker.location == self.location and not looker.location == self):
            return()
        self.msg(self.objsub('&1N just tasted you!', looker))
        if looker.location:
            looker.location.msg_contents(self.objsub('&1N just tasted &0c.', looker), exclude=[self, looker])

    def at_desc_texture(self, looker):
        if not looker.location or (not looker.location == self.location and not looker.location == self):
            return()
        self.msg(self.objsub('&1N just felt you!', looker))
        if looker.location:
            looker.location.msg_contents(self.objsub('&1N just felt &0c.', looker), exclude=[self, looker])

    def at_desc_sound(self, looker):
        pass

    def at_desc_aura(self, looker):
        pass

    def at_desc_writing(self, looker):
        pass

    def at_say(self, speaker, message):
        pass

    def at_whisper(self, speaker, message):
        pass

    # ----- Player Actions -----
    def action_use(self, user):
        """
        Called when a player attempts to use this object, without using it on something specific.
        This allows the object to decide its default target, if it's targetable.
        """
        user.msg("You can't use that.")

    def action_use_on(self, user, targets):
        """
        Called when a player attempts to use this object on another object.
        It also works on multiple objects, for example: use vacuum cleaner on dust bunny, crumbs
        """
        # If there's only one target, then the default is to try reversing it.
        if len(targets) == 1:
            targets[0].action_used_on_by(user, self)
        else:
            user.msg("That doesn't work.")

    def action_used_on_by(self, user, targets):
        """
        This is a secondary call, when the system is unable or unwilling to call 'use_on' for an object.
        It's called to indicate that a player wants to use an object on this object.
        It also works with multiple objects, for example: use candy wrapper, pop can on trash bin
        """
        user.msg("That doesn't work.")

    def action_lock(self, locker):
        """
        This action is called when a player attempts to 'lock' the object.
        The definition of locking is left up to the object creator.
        """
        locker.msg("You can't lock that!")

    def action_unlock(self, unlocker):
        """
        This action is called when a player attempts to 'lock' the object.
        The definition of locking is left up to the object creator.
        """
        unlocker.msg("You can't unlock that!")

    def action_stop(self, stopper):
        """
        This action is called when a player attempts to 'stop' the object.
        """
        stopper.msg("You can't stop that.")

    def action_start(self, starter):
        """
        This action is called when a player attempts to 'start' the object
        """
        starter.msg("You can't start that.")

    def action_equip(self, equipper):
        """
        This action is called when a player attempts to 'equip' the object
        """
        equipper.msg("You can't put that on.")

    def action_unequip(self, unequipper):
        """
        This action is called when a player attempts to 'doff' the object
        """
        unequipper.msg("That's not something you can take off.")

    # ----- Movement -----
    def redirectable_move_to(self, destination, quiet=False, emit_to_obj=None, use_destination=True, to_none=False):
        seen_destinations = set()
        while True:
            # Check for a destination redirect
            if not hasattr(destination, 'move_redirect'):
                break
            new_destination = destination.move_redirect(self)
            if not new_destination:
                break
            # Ensure we haven't already seen this destination (there's a loop)
            if new_destination in seen_destinations:
                raise Exception('move_redirect() loop detected!  ' + destination.dbref + ' lead to itself!')
            seen_destinations.add(new_destination)
            # Looks good.  Change the destination.
            destination = new_destination
        return super(Object, self).move_to(destination, quiet=quiet, emit_to_obj=emit_to_obj, use_destination=use_destination, to_none=to_none)

    # ----- Object based string substitution -----
    def objsub(self, template, *args):
        def repl(codeseq):
            # Determine which object we're asking for a substitution
            objnum = int(codeseq.group(1))
            if objnum == 0:
                subobj = self
            elif objnum <= len(args):
                subobj = args[objnum - 1]
            else:
                return(codeseq.group(0))
            # Determine whether we're capitalizing or not
            if codeseq.group(2).isupper():
                capitalize = True
                code = codeseq.group(2).lower()
            else:
                capitalize = False
                code = codeseq.group(2)
            # Check for an attribute override first
            if self.has_attribute('objsub_' + code):
                return(str(self.get_attribute('objsub_' + code)))
            # Otherwise, use a function on the class
            if hasattr(subobj, 'objsub_' + code):
                retval = getattr(subobj, 'objsub_' + code)()
            else:
                retval = subobj.objsub_other(code)
            # If the function returns 'None' then we want to ignore this substitution
            if retval == None:
                return codeseq.group(0)
            # Capitalize if necessary, and return the value.
            if capitalize:
                retval = retval[0].upper() + retval[1:]
            return retval
        return re.sub(r'&([0-9])([a-zA-Z])', repl, template)
    
    # A - Absolute Pronoun
    def objsub_a(self):
	if self.is_male():
	    return('his')
	if self.is_female():
	    return('hers')
        if self.is_herm():
	    return('hirs')
	if self.is_neuter():
	    return('its')
	return(self.key + "'s")

    # B - Casual Indefinite Name
    def objsub_b(self):
        """
        The casual name is used to order to casually or vaguely refer to the object, but expressed in an indefinite way (That is, not specific or unknown to the listener, such as with the idefinite article 'a')

        Examples:
            lamp post -> a lamp post
            Greywind Scaletooth -> an adventurer
            The Land Before Time -> a book
            a few pebbles -> pebbles
            [E]astern Gate -> a gate
            [E]xit Cave -> an exit
            The Courtyard -> a room

        In almost all cases, a character's name should be their casual name, but for objects it's often not.
        """
        return self.key

    # C - Casual Definite Name
    def objsub_c(self):
        """
        The casual name is used to order to casually or vaguely refer to the object, but expressed in a definite way (That is, specific or known to the listener, such as with the definite article 'the')

        Examples:
            lamp post -> the lamp post
            Greywind Scaletooth -> the adventurer
            The Land Before Time -> the book
            a few pebbles -> the pebbles
            [E]astern Gate -> the gate
            [E]xit Cave -> the exit
            The Courtyard -> the room

        In almost all cases, a character's name should be their casual name, but for objects it's often not.
        """
        return self.key

    # D - Specific Definite Name
    def objsub_d(self):
        """
        The name of the object when the object is specific or known to the listener.
        In other words, the name used in situations which typically call for the
        definite article.  ('the')

        Examples:
            lamp post -> the lamp post
            Greywind Scaletooth -> Greywind Scaletooth
            The Land Before Time -> The Land Before Time
            a few pebbles -> the pebbles
            [E]astern Gate -> the eastern gate
            [E]xit Cave -> the cave exit
            The Courtyard -> the courtyard
        """
        return 'the ' + self.key

    # I - Specific Indefinite Name
    def objsub_i(self):
        """
        The indefinite, (non-particular or unknown to the listenr) name of the object.
        In other words, the name used in situations which typically call for the
        indefinite article.  ('a')

        Examples:
            lamp post -> a lamp post
            Greywind Scaletooth -> Greywind Scaletooth
            The Land Before Time -> a copy of The Land Before Time
            a few pebbles -> a few pebbles
            [E]astern Gate -> an eastern gate
            [E]xit Cave -> a cave exit
            The Courtyard -> a courtyard

        Also, this doesn't mean 'vague'.  For example, you wouldn't want to change
        'King George' into 'a king'.  The user should still be able to identify what
        you're talking about, even though you're referring to it in an indefinite
        manner.  Although, for totally unique objects like 'King George' or 'The Holy
        Grail' there is no indefinite way to refer to them, in that case, just return
        their definite name.  (For 'vague', see 'B' - 'Casual Indefinite Name')
        """
        return 'a ' + self.key

    # N - Object Name
    def objsub_n(self):
        """
        This is the proper name of the object.
        Even though it's possible to override this, it would probably be bad, because it's used to identify the object to other players.
        It would allow a character to masquerade as another character, for example.  Not good.
        """
        return self.key

    # O - Objective Pronoun
    def objsub_o(self):
	if self.is_male():
	    return('him')
	if self.is_female():
	    return('her')
        if self.is_herm():
	    return('hir')
	if self.is_neuter():
	    return('it')
	return(self.key)

    # P - Posessive Pronoun
    def objsub_p(self):
	if self.is_male():
	    return('his')
	if self.is_female():
	    return('her')
        if self.is_herm():
	    return('hir')
	if self.is_neuter():
	    return('its')
	return(self.key + "'s")

    # R - Reflexive Pronoun
    def objsub_r(self):
	if self.is_male():
	    return('himself')
	if self.is_female():
	    return('herself')
        if self.is_herm():
	    return('hirself')
	if self.is_neuter():
	    return('itself')
	return(self.key)

    # S - Subjective Pronoun
    def objsub_s(self):
	if self.is_male():
	    return('he')
	if self.is_female():
	    return('she')
        if self.is_herm():
	    return('shi')
	if self.is_neuter():
	    return('it')
	return(self.key)

    # W - Within Name
    def objsub_w(self):
        """
        The within name describes the state of being within the object.

        Examples:
            Character/NPC: in Ted's pocket
            Room: at the southern doors
            Areas: in the Pleasantville Shopping Mall <-- Technically not an object, but also has within names
            Regions: on the moon <-- Technically not an object, but also has within names

        This can be used to generate a sentence (Combined with the casual name):
            That's a pencil, in Ted's pocket, at the southern doors, in the Pleasantville Shopping Mall, on the moon.
        """
        return 'in ' + self.key

    # Other
    def objsub_other(self, code):
        return None
