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

## Commands
Here is a list of commands that can be issued from pretty much anywhere within the app, simply by typing them.

### General
_:help_ | display this page
_:info_ | display the info page

### I\/O
_:q[!]_ or _:quit[!]_                | terminate the app [without saving]
_:w[!] [path]_ or _:write[!] [path]_ | [forcibly] save [to the specified path]
_:o[!] path_ or _:open[!] path_      | open file [discarding current]
_:wq[!] [path]_                    | _:w_ and _:q[!]_ combined"""
