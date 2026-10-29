import json as json
import os
import sys
from pathlib import Path


def player_save_path():
    if not getattr(sys, "frozen", False):
        return "./data/player.json"

    appdata = Path(os.environ.get("APPDATA", Path.home())) / "Starfall"
    beside_exe = Path(sys.executable).resolve().parent / "Starfall_Data"
    for folder in (appdata, beside_exe):
        try:
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / "player.json"
            # Check an existing save is writable too; a read-only stale save should
            # not prevent the game from starting with its local fallback.
            with path.open("a", encoding="utf-8"):
                pass
            return str(path)
        except OSError:
            continue
    return str(beside_exe / "player.json")

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
