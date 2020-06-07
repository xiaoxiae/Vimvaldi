"""A file containing various text strings that are used throughout the project.  It
doesn't contain all of them, just the big ones that are either ASCII art or larger
chunks of text."""

vimvaldi_logo = r"""     ________  **    ________               
    /        \****  /        \              
    \        /******\        /              
     |      |********/      /'              
     |      |******/      /'                
    *|      |****/      /'                  
  ***|      |**/      /'****                
*****|      |/      /'********              
  ***|            /'*********               
    *|      _   /'*********       _     _ _ 
     |     (_)/'__ _____   ____ _| | __| (_)
     |     | | '_ V _ \ \ / / _` | |/ _` | |
     |    /| | | | | | \ V / (_| | | (_| | |
     |__/' |_|_| |_| |_|\_/ \__._|_|\__,_|_|"""


menu_logo = r""" __  __                  
|  \/  | ___ _ __  _   _ 
| |\/| |/ _ \ '_ \| | | |
| |  | |  __/ | | | |_| |
|_|  |_|\___|_| |_|\__,_|"""


editor_logo = r""" _____    _   _            
| ____|__| |_| |_ ___  _ _ 
|  _| / _` (_) __/ _ \| '_|
| |__| (_| | | || (_) | |  
|_____\__,_|_|\__\___/|_|  """


info_text = r"""# Info
The following page contains relevant information about the app (and it's creator and maintainer).

## Context
This project was created as a semester project for the AP Programming Course at the Charles University (_http:\/\/mj.ucw.cz\/vyuka\/1920\/p1x\/_) by Tomáš Sláma (_http:\/\/slama.dev\/_).

## Source Code
The code is licensed under MIT and freely available at _https:\/\/github.com\/xiaoxiae\/Vimvaldi\/_, so feel free do whatever you want with it :-). Feel free to create an issue or submit a pull request if there's something you'd like to see changed or implemented!

## Disclaimer
This is a toy project. Please, for the love of god, do not use this anywhere near production."""


help_text = r"""# Help
The following page contains instructions on using the app.

## Controls

### General
_k_ or _↑_          | move up
_j_ or _↓_          | move down
_h_ or _←_          | move left
_l_ or _→_          | move right
_CTRL-D_ \/ _CTRL-U_ | move up\/down faster
_enter_           | confirm

### Help\/Info
_q_ | exit

### Editor
_hl_ or _←→_ | move left\/right
_i_        | insert item
_x_        | delete a single item
_._        | repeat the last insert command

## Commands
Commands can be issued from nearly anywhere within the app by pressing _:_ and typing the respective command.

### General
_:help_ | display this page
_:info_ | display the info page

### Editor
_:q[!]_ or _:quit[!]_                | quit [without saving]
_:w[!] [path]_ or _:write[!] [path]_ | [forcibly] save [to the specified path]
_:o[!] path_ or _:open[!] path_      | open file [discarding current]
_:wq[!] [path]_                    | _:w_ and _:q[!]_ combined

_:set opt val_ or _:set opt=val_     | set an option to a given value
                                 | example: 'set clef bass'"""

