import json as json 

def save_player(player,file_player):
   json_player = json.dumps(player)
   with open (file_player,'w') as player_file:
      player_file.write(json_player)

def load_player(file_player):
   player = json.decoder(file_player) 
   return player
