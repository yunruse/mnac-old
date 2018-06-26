# Meta Noughts and Crosses

<a href="https://discordapp.com/oauth2/authorize?client_id=446046704039624715&scope=bot">
<img src="https://img.shields.io/badge/Add%20to%20your-Discord-9399ff.svg" alt="Invite to your Guild"></a>

Meta Noughts and Crosses (aka [Ultimate Tic-Tac-Toe](wiki)) is a tactical twist on the classic game. Make no mistake - it is easy to learn but difficult to master! MNAC can be played via the terminal, UI, or via a Discord bot.

![A screenshot of the Discord bot. A player types in '6', and the bot responds with an image of the game.](assets/screenshot_discord.png)

## Features

- A core game class and renderer, freely available per [license] to reuse in your own project
- An ASCII terminal version, if you enjoy playing games in Vim or something
- A Discord bot that works per-channel or via direct messages, as simple as `mnac/start` for each player, and with extensible support for different languages

## Installation

First, [download] and extract.

If you just want the UI, grab the dependencies required:

`pip install numpy Pillow`

Then run `terminal.py` or `tk.py` for the terminal or UI versions of the game.

If you want the Discord bot, grab the dependencies:

`pip install numpy Pillow discord.py toml`

Then, simply:

1. [Create a Discord bot](API), and place the token inside of `config/tokens.txt`.
2. Rename `config_sample.toml` to `config.toml`, and modify settings as you please.
3. To save time and processing power, the bot caches the URL of each render of the game. Create a private channel, disable notifications on it, and run `mnac/cache here` - this is where all images will be sent.

# Update log
- 1.0: Initial release.

[wiki]: https://en.wikipedia.org/wiki/Ultimate_tic-tac-toe
[license]: license.txt
[download]: https://github.com/yunruse/MNAC/archive/master.zip
[API]: https://discordapp.com/developers/applications/me