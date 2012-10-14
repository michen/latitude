from game.gamesrc.latitude.commands.muckcommand import MuckCommand
from game.gamesrc.latitude.utils.stringmanip import conj_join
from ev import Object
from ev import Character
from ev import search_object

class CmdLead(MuckCommand):
    """
    lead - Start leading a character or object.
    Usage:
      lead <character/object>
      lead #auto <character/object>
      lead #stop

      Use 'lead #auto <character/object>' to allow others to skip permission checks when they choose to follow you.
      Use 'lead #auto all' or 'lead #auto none' to permit everyone or nobody, respectively, to automatically follow you.
      Use 'lead #stop' to stop others from following you.
    """
    key = "lead"
    locks = "cmd:all()"
    help_category = "Actions"
    aliases = []

    def func(self):
        if 'stop' in self.switches:
            self.stop()
        elif 'auto' in self.switches:
            self.auto()
        else:
            self.lead()

    def stop(self):
        leader = self.caller
        followers = search_object(leader, attribute_name='follow_following')
        # Ensure we're ready to clear the follow
        if not followers:
            leader.msg("You're not currently leading anyone.")
            return
        # Clear the follow
        for follower in followers:
            del follower.db.follow_following
            leader.msg('You stop leading %s.' % (follower.key))
            follower.msg('%s stops leading you.' % (leader.key))

    def lead(self):
        leader = self.caller
        follower = leader.search(self.args)
        if not follower:
            return # Error message is handled by the search call
        if not isinstance(follower, Object):
            leader.msg("You can't follow that!")
            return
        already_following = search_object(leader, attribute_name='follow_following')
        if already_following:
            leader.msg("You're already leading %s.  [Use \"lead #stop\" to stop leading, first.]" % (conj_join([char.key for char in already_following], 'and')))
            return
        if follower.db.follow_following:
            leader.msg("%s is already following someone." % (follower.key))
            return
        # Start leading, if we have permissions.
        if not follower.access(leader, 'follow') and not (follower.db.follow_pending and follower.db.follow_pending == leader and not follower.db.follow_pending_tolead):
            # Looks like it's not going to happen.  If we're dealing with a character, give them a chance to give permission
            if isinstance(follower, Character):
                # TODO: ALREADY WAITING
                # Warn the user that existing requests are being cleared
                if leader.db.follow_pending and not leader.db.follow_pending_tolead:
                    leader.msg('You no longer want to follow %s' % (leader.db.follow_pending.key))
                    del leader.db.follow_pending
                    del leader.db.follow_pending_tolead
                # Set the new request, adding to the list if a lead request already exists
                leader.db.follow_pending_tolead = True
                if leader.db.follow_pending:
                    # For some reason I can't store sets.  So extract it as a list, and convert it to a set, then store it back in.
                    follow_pending_set = set(leader.db.follow_pending)
                    follow_pending_set.add(follower)
                    leader.db.follow_pending = follow_pending_set
                else:
                    leader.db.follow_pending = set([follower])
                # Alert both parties
                follower.msg('%s wants to lead you.  [Use "follow %s" to follow.]' % (leader.key, leader.key))
                leader.msg('You wait for %s to follow you.' % (follower.key))
                return
            # It's not a character.  Fail out.
            self.caller.msg("You can't follow that!")
            return
        # Start leading
        follower.db.follow_following = leader
        follower.msg('%s starts leading you.' % (leader.key))
        leader.msg('You start leading %s.' % (follower.key))
        # Clear existing follow/lead requests if needed.
        if leader.db.follow_pending:
            if leader.db.follow_pending_tolead:
                if follower in leader.db.follow_pending:
                    leader.db.follow_pending.remove(follower)
            else:
                follower.msg("It seems you're now too busy to follow %s." % (leader.db.follow_pending.key))
                del leader.db.follow_pending
                del leader.db.follow_pending_tolead
        if follower.db.follow_pending and not follower.db.follow_pending_tolead:
            del follower.db.follow_pending
            del follower.db.follow_pending_tolead
