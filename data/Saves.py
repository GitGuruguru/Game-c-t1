import json as json 

def save_player(player,file_player):
   json_player = json.dumps(player)
   with open (file_player,'w') as player_file:
      player_file.write(json_player)
      
def load_player(file_player):
  
   try:
      with open (file_player,'r') as player_file:
         player = json.load(player_file)
   except Exception as ex:
         player = {
             "name" : "<A>",
             "money" : 0,
             "score" : 0,
             "level" : 1,
             "lives" : 3,
             "items" : {},
             "powers" : {}
         }
         save_player(player,"./data/player.json")

   return player