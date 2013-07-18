import random

def pick_reward(rewards, character):
    """
    Pick a reward at random weighted based on its chance() values.
    """
    # Extract the chance values in advance (They may change, who knows)
    chances = [reward.chance(character) for reward in rewards]
    # Calculate the total chance pool
    total_chance = 0
    for reward_index in range(len(rewards)):
        if chances[reward_index] < 0:
            raise Exception('negative chance value')
        total_chance += chances[reward_index]
    # If there's nothing to pick, then return
    if total_chance < 1:
        return None
    # Pick a point in the chance pool at random
    roll = random.randint(1, total_chance)
    character.msg(roll)
    # Iterate through the items until we land on our rolled number
    current_chance = 0
    for reward_index in range(len(rewards)):
        current_chance += chances[reward_index]
        if roll <= current_chance:
            return rewards[reward_index]
    return None

class Reward(object):
    """
    This class is used to give things to characters, and to define how likely it
    is that the user will receive it (Compared to other competing rewards which
    could be offered at the same time)
    """
    def chance(self, character):
        """
        Returns an integer representing the chance this object should
        be randomly selected opposed to a competing object.  The value
        is analagous to the number of 'lottery tickets' desired.
        """
        return 1

    def apply(self, character):
        """
        Generate the actual reward
        """
        character.msg("Who's awesome?  You're awesome!")

class RewardItem(Reward):
    """
    This reward class generates an item.  Which object to create, and how, are
    stored as attributes.
    """
    item_chance = 1
    item_key = None
    item_typeclass = 'prop.Prop'
    item_quantity = 1
    item_attributes = None
    item_give_msg = 'You recieve &0i.'
    item_give_msg_others = None

    def chance(self, character):
        return self.item_chance

    def apply(self, character):
        new_obj = character.give(self.item_typeclass, quantity=self.item_quantity, key=self.item_key, attributes=self.item_attributes)[0]
        # Alert the character
        if self.item_give_msg:
            character.msg(new_obj.objsub(self.item_give_msg, character))
        # Alert others at the character's location
        if self.item_give_msg_others and character.location:
            character.location.msg_contents(new_obj.objsub(self.item_give_msg_others, character), exclude=character)

