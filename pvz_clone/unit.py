import json


UNIT_INFOS = json.load(open("units.json"))
ATTACK_INFOS = json.load(open("attacks.json"))


class Unit():
    def __init__(self, unit_id, location, is_attack=False):
        self.id = unit_id
        self.location = location
        self.is_attack = is_attack
        self.has_moved = False

        unit_info = ATTACK_INFOS[unit_id] if is_attack else UNIT_INFOS[unit_id]
        for k in unit_info:
            setattr(self, k, unit_info[k])

        self.curr_move = 0
        self.curr_attack = 0


    def move(self):
        new_loc = [self.location[0] + self.moves[self.curr_move][0],
                   self.location[1] + self.moves[self.curr_move][1]]

        self.has_moved = True
        self.curr_move = (self.curr_move + 1) % len(self.moves)

        return new_loc


    def attack(self):
        atks = []
        if not hasattr(self, 'attacks'):
            return atks
        
        unit_atks = self.attacks[self.curr_attack]
        self.curr_attack = (self.curr_attack + 1) % len(self.attacks)

        for atk in unit_atks:
            atk_loc = []
            atk_loc.append(self.location[0] + atk[0])
            atk_loc.append(self.location[1] + atk[1])

            atks.append((atk[2], atk_loc))

        return atks
