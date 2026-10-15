abilities = ["addhitbox", "rewind", "reload","ice age","volcano","fieryaura"]



class Enemy():
    def __init__(self,hp,xp_gain,dmg,speed):
        self.hp = hp
        self.xp = xp_gain
        self.dmg = dmg
        self.speed = speed
class s_tier_enemy(Enemy):
    def __init__(self, hp, xp_gain, dmg, speed, ability):
        super().__init__(hp, xp_gain, dmg, speed)
        self.ability = ability
        self.maxdmg = dmg * 2
class boss_tier_enemy(s_tier_enemy):
    def __init__(self, hp, xp_gain, dmg, speed, ability , phases,):
        super().__init__(hp, xp_gain, dmg, speed, ability)
        self.phases = phases
        

    
        
