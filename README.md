# Meta Noughts and Crosses

Meta Noughts and Crosses (aka [Ultimate Tic-Tac-Toe](wiki)) is a tactical twist on the classic game. Make no mistake - it is easy to learn but difficult to master! MNAC can be played via the terminal or UI.

It also has a Discord bot, which is currently based on a much older version of Python and is therefore not guaranteed to work:

![A screenshot of the Discord bot. A player types in '6', and the bot responds with an image of the game.](assets/screenshot_discord.png)
## Installation and setup

Requires Python 3.5 or above.

You can run `terminal.py` straight away. If you want the GUI version, install:

`pip install numpy Pillow`

Then run `tk.py` for a Tkinter-powered UI.

### Installing Discord bot

If you want to run a Discord bot, register it with [Discord's API] and install:

`pip install numpy Pillow discord.py toml`

If you have Linux, just:
```bash
git clone https://github.com/yunruse/mnac
cd mnac
echo "MY_DISCORD_TOKEN" > config/token.txt
cp config/config_sample.toml config/config.toml
nano config/config.toml
```

Then run `discord_bot.py`. If Linux gives you numpy errors, the following may help:

```bash
pip uninstall numpy
apt install python3-numpy
```

#### Configuring the bot before use

To save time and processing power, the bot caches the URL of each render of the game, and stores them in a channel to avoid users deleting the cache. Create a private channel in a server you control, disable notifications on it, invite the bot with the link it shows you on startup, and register yourself as admin and that channel as cache channel by running `mnac/cache here`. From then on only you will be able to run `mnac/cache`. Delete the relevant lines in `config.toml` to undo that.

The bot will save data every few minutes. Run `mnac/cache purge` to clear cache or `mnac/help` for all non-admin commands.

[wiki]: https://en.wikipedia.org/wiki/Ultimate_tic-tac-toe
[API]: https://discordapp.com/developers/applications/me

# Legal

Copyright (c) Mia yun Ruse (yunru.se) 2018 – 2021.

This work is licensed under a Creative Commons Attribution 4.0 International
license. In non-legal terms: do whatever you like, but credit me.

The full license is available here:
https://creativecommons.org/licenses/by/4.0/

