```
     ________  **    ________
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
     |__/' |_|_| |_| |_|\_/ \__._|_|\__,_|_|
```

Vimvaldi is a program for efficient editing of musical scores in your terminal. The controls are keyboard-oriented and customized for Vim users. Features of the program include basic note sheet editing and LilyPond import/export. The program is written in Python with the use of the Curses library.

---

## Running Vimvaldi
To install Vimvaldi, run `pip install vimvaldi` (make sure to have Python 3 installed).
Then you can simply run `vimvaldi` from a terminal of your choice and you should be good to go!

Alternatively, run from source:
```console
xiaoxiae@thinkpad ~> git clone https://github.com/xiaoxiae/vimvaldi.git
xiaoxiae@thinkpad ~> cd vimvaldi/
xiaoxiae@thinkpad ~> pip install -r requirements.txt
xiaoxiae@thinkpad ~> python -m vimvaldi.__init__
```

**Warning:** the app will only properly work when ran in terminals with UTF-8 support and fonts that contain the [Musical Symbols Unicode block](https://en.wikipedia.org/wiki/Musical_Symbols_(Unicode_block)).

## Controls
After starting the app (and pressing enter), use the arrow keys (or j/k) and enter to open the `HELP` section of the menu.
