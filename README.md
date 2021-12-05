# Meta Noughts and Crosses

Meta Noughts and Crosses (aka [Ultimate Tic-Tac-Toe](wiki)) is a tactical twist on the classic game. Make no mistake - it is easy to learn but difficult to master! MNAC can be played via the terminal or UI.

It also has a Discord bot, which is currently based on a much older version of Python and is therefore not guaranteed to work:

![A screenshot of the Discord bot. A player types in '6', and the bot responds with an image of the game.](assets/screenshot_discord.png)

## Features

- A core game class and renderer,
- An ASCII terminal version
- A Tkinter version, playable by mouse or keyboard
- A Discord bot that works per-channel or via direct messages, as simple as `mnac/start` for each player, and with extensible support for different languages

## Installation and setup

First, grab the Python requirements - grab Python 3.6 or above and:

`pip install numpy Pillow`

Run `terminal.py` on the Terminal or just `tk.py` for a Tkinter-powered UI.

### Installing Discord bot

If you want to run a Discord bot, register it with [Discord's API] and grab:

`pip install discord.py toml`

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

# Update log
- 
- 1.0: Initial release.

[wiki]: https://en.wikipedia.org/wiki/Ultimate_tic-tac-toe
[API]: https://discordapp.com/developers/applications/me

# Legal

Copyright (c) Mia yun Ruse (yunru.se) 2018 – 2021.

This work is licensed under a Creative Commons Attribution 4.0 International
license. In non-legal terms: do whatever you like, but credit me.

The full license is available here:
https://creativecommons.org/licenses/by/4.0/

