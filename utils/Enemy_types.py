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
        self.extraxp = xp_gain // 2


class cluster_capitan(boss_tier_enemy):
    def __init__(self, hp, xp_gain, dmg, speed, ability, phases , height , width ):
        super().__init__(hp, xp_gain, dmg, speed, ability, phases)

    def misle_barrage():
        pass
    def icbm():
        pass
    def active_rapair():
        pass




class ghost_leviathan(boss_tier_enemy):
    def __init__(self, hp, xp_gain, dmg, speed, ability, phases,height,width):
        super().__init__(hp, xp_gain, dmg, speed, ability, phases)
    
    def slide():
        pass
    def fade():
        pass
    def destroy():
        pass

