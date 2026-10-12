from utils import scene 
import io 
import re
class Entity():
    def __init__(self,hp,dmg,xp):
        self.hp = hp
        self.dmg = dmg
        self.xp = xp 

    def take_dmg(self, dmg):
        return self.hp - dmg
    def attack(self,hp):
        return self.dmg - hp
    def deathTriger(self):
        if(self.hp == 0):
            return 0

class Bullet():
    def __init__(self,dmg,):
        self.dmg = dmg
        self.speed = 10
    def colision():
        scene.colisionCheck()
        
class Enemy(Entity):

    def __init__(self, hp, dmg, xp):
        super().__init__(hp, dmg, xp)
        self.hp = 10
        self.dmg = 10 
        self.xp = 0 
        self.xp_gain = 5

    def spawner(self,bullet,scene):
        try:
            bullets = io.open("./utils/bulletTypes.txt")
            bullets.match("\w")
            
        except( FileExistsError ):
            print("Error plik bulletTypes.txt nie istnieje lub jest pusty")

        
        
        scene.add(bullet)
