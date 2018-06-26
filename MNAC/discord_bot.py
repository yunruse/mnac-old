import copy
import datetime
import json
import random
import time
import os

import discord
import toml

from mnac import MNAC, MoveError, getIndex
import render

# Print log messages to console output
LOG_TO_STDOUT = True
# Path to log file or `None`
PATH_LOG = '../config/log.txt'
PATH_TOKEN = '../config/token.txt'

# These can be .json or .toml
PATH_LANGUAGES ='../config/languages.toml'
PATH_SERVERS = '../config/servers.toml'
PATH_CONFIG = '../config/config.toml'
PATH_CACHE = '../config/image_cache.toml'

#                   __
# |\   /|\  |  /\  /    
# | \ / | \ | /__\/ 
# |  v  |  \|/    \
# |     |   V      \__
# M E T A   N O U G H T S   A N D   C R O S S E S
#
# Thar be dragons below.

bot = discord.Client()

def printf(message, *args, **kwargs):
    msg = '{:%Y-%m-%d %H:%M:%S}  '.format(datetime.datetime.now()) + message.format(*args, **kwargs)
    if LOG_TO_STDOUT:
        print(msg)
    if PATH_LOG and os.path.isfile(PATH_LOG):
        with open(PATH_LOG, 'a', encoding='utf8') as f:
            f.write(msg + '\n')

def _data_load(path, required=False):
    if path:
        try:
            with open(path, encoding='utf8') as f:
                if path.endswith('.json'):
                    return json.load(f)
                elif path.endswith('.toml'):
                    return toml.load(f)
        except FileNotFoundError:
            if required:
                raise
    
    return dict()

def _data_save(path, data):
    with open(path, 'w', encoding='utf8') as f:
        if path.endswith('.json'):
            json.dump(data, f)
        elif path.endswith('.toml'):
            toml.dump(data, f)

printf('Loading configuration...')

LANGUAGES = _data_load(PATH_LANGUAGES, required=True)
# {lang_code(s): {response_id(s): translation}}

CONFIG = _data_load(PATH_CONFIG)
CACHE_CHANNEL = None

SERVERS = _data_load(PATH_SERVERS)
# channel_id(s): {'language': lang_code, 'state': state}
# where state is null or either:
  # {'kind': 'lobby', 'noughts': str, 'time_started': int, otherconfig...}
  # {'kind': 'game', ...}

# deserialise lobbies
# (actual games are deserialised when needed)
for chan in SERVERS:
    state = SERVERS[chan].get('state')
    if state is None:
        SERVERS[chan]['state'] = None
    elif state['kind'] == 'lobby':
        SERVERS[chan]['state']['noughts'] = bot.get_user_info(state['noughts'])

CACHE = _data_load(PATH_CACHE)
# {gameMapping(s): image_url}

CONF_DEFAULT = {'language': CONFIG['default_language'], 'state': None}
def config(chan):
    conf = SERVERS.get(chan.id)
    if not conf:
        SERVERS[chan.id] = conf = dict(CONF_DEFAULT)
        # don't save - the server hasn't interacted yet
    return LANGUAGES[conf['language']], conf['state']




#
# %% Bot i/o shenanigans
#




mention = lambda user: "<@{}>".format(user.id)

@bot.event
async def on_ready():
    global CACHE_CHANNEL
    if CACHE_CHANNEL is None:
        CACHE_CHANNEL = bot.get_channel(str(CONFIG.get('cache_channel')))
    
    printf('Welcome,        {0.user} ({0.user.id})', bot)
    printf('Server invite:  https://discordapp.com/oauth2/authorize?client_id={}&scope=bot',
        bot.user.id)
    printf('Chat prefix:    {}', CONFIG['prefix'])
    printf('-'*20)

async def respond(msg, chan, user, **kwargs):
    lang, game = config(chan)

    if msg in lang:
        msg = lang[msg].format(**kwargs)
    
    # Determine user identifiers
    m_user = mention(user)
    m_oppo = ''

    if isinstance(game, DiscordMNAC):
        if game.is_solo:
            prefix = ''
            m_user, m_oppo = game._namePlayers()
        else:
            m_oppo = mention(game.opponent)            
    
    for a, b in (
        ('>user<', m_user),
        ('>opponent<', m_oppo),
        ('[>', '`' + CONFIG['prefix']),
        ('<]', '`')):
        msg = msg.replace(a, b)
    
    await bot.send_message(chan, msg)

RENDER_PATH = '%smnac_{}.%s' % (
    os.path.expandvars('%temp%/' if os.name == 'nt' else '$tmpdir/'),
    CONFIG['render_file_format'])

class DiscordMNAC(MNAC):
    '''Handles serialisation, user confusing and message sending'''
    
    def __init__(self, channel, noughts, crosses, noMiddleStart=False):
        self.timeStarted = time.time()
        self.channel = channel
        self.noughts = noughts
        self.crosses = crosses
        self.render = render.ImageRender(self, CONFIG['render_file_size'])
        MNAC.__init__(self, noMiddleStart=noMiddleStart)

    def __repr__(self):
        return '<Discord MNAC ({}, {})>'.format(self.noughts, self.crosses)

    current_user = property(lambda s: s.noughts if s.player == 1 else s.crosses)
    opponent = property(lambda s: s.noughts if s.player == 2 else s.crosses)
    users = property(lambda s: (s.noughts, s.crosses))
    is_solo = property(lambda s: s.noughts == s.crosses)

    @property
    def has_expired(self):
        return time.time() - self.timeStarted > CONFIG['max_game_time']

    def _namePlayers(self):
        '''Return 'noughts' or 'crosses' in order (currentPlayer, otherPlayer)'''
        lang, _ = config(self.channel)
        users = lang['noughts'], lang['crosses']
        return users[::-1] if self.player == 2 else users
    
    async def show(self):
        await bot.send_typing(self.channel)
        if self.winner:
            code = "result_" + ('draw' if self.winner == 3 else 'win')
            return await respond(code, self.channel, self.current_user)
        else:
            # Todo: globals? really? use OOP
            # An admin must specify a private channel for the bot
            # to chuck all images into. This ensures the status
            # is always returned as an embed, not an image,
            # and means users can't just delete images.

            if CACHE_CHANNEL is None:
                return await respond('cache_not_found', self.channel, self.current_user)
            
            embed = discord.Embed()
            player, other = self._namePlayers()
            lang, _ = config(self.channel)
            status = lang[self.state].format(player=player, other=other)
            icon_url = CONFIG.get(['noughts_icon', 'crosses_icon'][self.player == 2])
            embed.set_footer(text=status, icon_url=icon_url)

            # equal hash(game) <-> equal render
            game_hash = str(hash(self))
            
            # messageID, imageID
            imageIDs = CACHE.get(game_hash)
            
            if imageIDs:
                link = 'https://cdn.discordapp.com/attachments/{}/{}/mnac_{}.png'.format(
                    CACHE_CHANNEL.id, imageIDs[1], game_hash)
            else:
                # render game and send to the cache channel
                file_path = RENDER_PATH.format(game_hash)
                self.render.draw().save(file_path)
                
                message = await bot.send_file(CACHE_CHANNEL, file_path)
                link = message.attachments[0]['url']
                CACHE[game_hash] = [int(message.id), int(link.split('/')[-2])]
                os.remove(file_path)

            
            embed.set_image(url=link)
            return await bot.send_message(self.channel, embed=embed)
    
    # Serialisation to dict (Discord items store as IDs)
    
    _NoneSerial = 'lastPlacedGrid lastPlacedCell'.split()
    _directSerial = 'noMiddleStart player grid grids state'.split()
    _idSerial = 'noughts crosses'.split()
    
    @classmethod
    async def fromSerial(cls, channel, config):
        game = cls(channel,
            noughts=await bot.get_user_info(config.pop('noughts')),
            crosses=await bot.get_user_info(config.pop('crosses')),
        )
        for i in cls._NoneSerial:
            setattr(game, i, config.get(i, None))
        for i in cls._directSerial:
            setattr(game, i, config.get(i, None))
        game.check()
        return game
        
    def toSerial(self):
        serial = {'kind': 'game'}
        for i in self._NoneSerial:
            serial[i] = getattr(self, i, None)
        for i in self._directSerial:
            serial[i] = getattr(self, i)
        for i in self._idSerial:
            serial[i] = getattr(self, i).id
        return serial



#
# %% Message handling
#



COMMANDS = 'help tutorial status start stop play random lang cache'.split()

@bot.event
async def on_message(message):
    # Message variables
    user = message.author
    if user == bot.user:
        return
    chan = message.channel
    now = time.time()
    content = message.content.lower()

    async def r(m, **k):
        await respond(m, chan, user, **k)
    
    # Game variables
    game = config(chan)[1]
    mode = 'chat'

    def set_game(new=None):
        if new != SERVERS[chan.id]['state']:
            SERVERS[chan.id]['state'] = new
        return new

    # deserialise game entries
    if isinstance(game, dict) and game['kind'] == 'game':
        game = await DiscordMNAC.fromSerial(chan, game)
        SERVERS[chan.id]['state'] = game
    
    if isinstance(game, DiscordMNAC):
        mode = 'game'
        if game.has_expired:
            game = set_game(None)
            mode = 'chat'
        
    elif isinstance(game, dict):
        # Lobby - purge if reached limit
        mode = 'lobby'
        lobby_seconds_left = CONFIG['max_lobby_time'] - (now - game['time_started'])
        if lobby_seconds_left < 0:
            game = set_game(None)
            mode = 'chat'
    
    if mode == 'game' and user in game.users and isinstance(getIndex(content), int):
        # players can skip the whole '/play' malarkey
        args = content.split()
        command = 'play'
    
    elif content.startswith(CONFIG['prefix']):
        # standard prefixed response
        args = content[len(CONFIG['prefix']):].split()
        if not args:
            return
        command = args.pop(0)
        
    elif chan.is_private:
        # private games can go prefixless
        args = content.split()
        if not args:
            return
        command = args.pop(0)
    else:
        return

    if args:
        subcommand = args[0]
    else:
        subcommand = None

    if command in COMMANDS:
        printf('{:<20} {:<5} {:<10} : {}({})', chan.id, mode, user.name, command, ', '.join(args))
    else:
        return await r('command_unknown', command=command)

    if command == 'help':
        # list off commands
        doc = 'help'
        
        for sub in 'start play'.split():
            if subcommand == sub:
                doc += '_' + sub
        
        await r(doc)

    elif command == 'status':
        # give status of game / re-print game
        if mode == 'game':
            await game.show()
        else:
            await r('status_{}'.format(
                'solo' if chan.is_private else 'lobby' if mode == 'lobby' else 'empty'))

    elif command == 'lang':
        if subcommand in LANGUAGES:
            SERVERS[chan.id]['language'] = subcommand
            return await r('language_changed')

        # print list of languages
        await r('language_help')
        langs = '\n'.join('{:<10} {}'.format(s, LANGUAGES[s]['Language']) for s in LANGUAGES)
        return await r(langs)
    
    elif command == 'start':
        # Lobbies can be held but also skipped, so we get arguments and THEN apply them
        noughts = None
        noMiddleStart = 'allowMiddle' not in args
        
        isSolo = chan.is_private or ('practice' in args or 'solo' in args)
        if game is None and isSolo:
            noughts = user
        elif mode == 'lobby':
            noughts = game.get('noughts')
            noMiddleStart = game.get('noMiddleStart', True)
        
        if noughts:
            game = DiscordMNAC(message.channel, noughts, user, noMiddleStart=noMiddleStart)
            set_game(game)
            await game.show()

        if mode == 'game' and user not in game.users:
            await r('lobby_game_already_started')
        
        if game is None:
            # start lobby
            lobby = {'kind': 'lobby', 'noughts': user,
                     'time_started': now, 'noMiddleStart': noMiddleStart}
            set_game(lobby)
            await r('lobby_open', time_left=CONFIG['max_lobby_time'])

    elif command in 'stop play random'.split() and mode == 'game' and user in game.users:

        async def play(direction):
            game.play(direction)
            await game.show()
            if game.winner:
                set_game(None)

        if command == 'stop':
            set_game(None)
            await r('stop_success_{}'.format('solo' if game.is_solo else 'multi_'))

        elif command == 'play':
            if args:
                direction = getIndex(args.pop(0))
                if isinstance(direction, int):
                    await play(direction + 1)
                else:
                    await r('play_unknown_direction', direction=direction)
            else:
                await r('play_no_args')

        elif command == 'random':
            moves = [0, 1, 2, 3, 4, 5, 6, 7, 8]
            random.shuffle(moves)
            for i in moves:
                try:
                    await play(i)
                    break
                except MoveError:
                    continue
            else:
                await r('play_unknown_error')
        
    elif command == 'cache':
        global CACHE_CHANNEL
        global CACHE
        if 'admin' not in CONFIG:
            CONFIG['admin'] = int(user.id)
       
        if int(user.id) != CONFIG.get('admin'):
            return

        if subcommand == 'here':
            CACHE_CHANNEL = chan
            CONFIG['cache_channel'] = int(chan.id)
            await r('cache_here')
        
        elif subcommand == 'purge':
            for h in CACHE:
                messageID, imageID = CACHE[h]
                message = await bot.get_message(CACHE_CHANNEL, str(messageID))
                if message:
                    bot.delete_message(message)
            with open(PATH_CACHE, 'w') as f:
                pass # clears cache file
            await r('cache_purged')
        
        else:
            _data_save(PATH_CACHE, CACHE)
            await r('cache_saved')

        printf('Saving config and cache to file...')

        servers_serial = {}
        for chan in SERVERS:
            state = SERVERS[chan]['state']
            if isinstance(state, DiscordMNAC):
                state = state.toSerial()
            else:
                state = copy.deepcopy(state)
                if isinstance(state, dict) and state['kind'] == 'lobby':
                    state['noughts'] = state['noughts'].id
            
            servers_serial[chan] = {'language': SERVERS[chan]['language'], 'state': state}
    
        _data_save(PATH_SERVERS, servers_serial)
        _data_save(PATH_CONFIG, CONFIG)

with open(PATH_TOKEN, encoding='utf8') as f:
    TOKEN = f.read(-1)

# https://discordpy.readthedocs.io/en/latest/api.html#message
try:
    printf('Bot spinning up...')
    bot.run(TOKEN)
except Exception as e:
    printf('{}: {}', type(e).__name__, ' '.join(map(str,e.args)))
    printf('Bot turning off...')
    input()
