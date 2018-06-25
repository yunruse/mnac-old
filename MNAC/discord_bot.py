import copy
import datetime
import json
import random
import time
import os

import discord

from mnac import MNAC, MoveError, getIndex
import render

# Print log messages to console output
LOG_TO_STDOUT = True
# Path to log file or `None`
PATH_TOKEN = '../config/token.txt'
PATH_LANGUAGES ='../config/languages.json'
PATH_LOG = '../config/log.txt'
PATH_CONFIG = '../config/servers.json'
PATH_CACHE = '../config/image_cache.json'


# Chat prefix required in public channels
PREFIX = 'mnac/'

# Maximum time in seconds
MAX_LOBBY_TIME = 10
MAX_GAME_TIME = 60 * 30

# Width (= height) of image to render
RENDER_FILE_SIZE = 450
# f(game, game_hash) to determine path and file type.
def RENDER_FILE_PATH(game, game_hash):
    return '{}mnac_{}.png'.format(
        os.path.expandvars('%temp%/' if os.name == 'nt' else '$tmpdir/'),
        game_hash)

DEFAULT_LANGUAGE = 'en'

#                   __
# |\   /|\  |  /\  /         
# | \ / | \ | /__\/    \/ /\ \/ /\ |
# |  v  |  \|/    \    /\ \/ /\ \/ .
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



#
# %% Bot i/o shenanigans
#




mention = lambda user: "<@{}>".format(user.id)

@bot.event
async def on_ready():
    printf('Welcome,        {0.user} ({0.user.id})', bot)
    printf('Server invite:  https://discordapp.com/oauth2/authorize?client_id={}&scope=bot',
        bot.user.id)
    printf('Chat prefix:    {}', PREFIX)
    printf('-'*20)

async def respond(msg, chan, user, **kwargs):
    lang, game = config(chan)

    if msg in lang:
        msg = lang[msg].format(**kwargs)
    
    # Determine user identifiers
    m_user = mention(user)
    m_oppo = ''
    prefix = PREFIX

    if isinstance(game, DiscordMNAC):
        if game.is_solo:
            prefix = ''
            users = lang['noughts'], lang['crosses']
            m_user = users[game.player-1]
            m_oppo = users[2 - game.player]
        else:
            m_oppo = mention(game.opponent)            
    
    for a, b in (
        ('>user<', m_user),
        ('>opponent<', m_oppo),
        ('[>', '`' + prefix),
        ('<]', '`')):
        msg = msg.replace(a, b)
    
    await bot.send_message(chan, msg)

class DiscordMNAC(MNAC):
    # Serialisation to dict (Discord items store as IDs)
    _directSerial = 'noMiddleStart player grid grids state lastPlaced'.split()
    _idSerial = 'channel noughts crosses'.split()

    def toSerial(self):
        serial = {'kind': 'game'}
        for i in self._directSerial:
            serial[i] = getattr(self, i)
        for i in self._idSerial:
            serial[i] = getattr(self, i).id
        return serial
    
    @classmethod
    async def fromSerial(cls, config):
        config.pop('kind')
        game = cls(
            channel=bot.get_channel(config.pop('channel')),
            noughts=await bot.get_user_info(config.pop('noughts')),
            crosses=await bot.get_user_info(config.pop('crosses')),
        )
        for i in cls._directSerial:
            setattr(game, i, config[i])
        game.check()
        return game
    
    def __init__(self, channel, noughts, crosses, noMiddleStart=False):
        self.timeStarted = time.time()
        self.channel = channel
        self.noughts = noughts
        self.crosses = crosses
        self.render = render.ImageRender(self, RENDER_FILE_SIZE)
        MNAC.__init__(self, noMiddleStart=noMiddleStart)

    @property
    def has_expired(self):
        return time.time() - self.timeStarted > MAX_GAME_TIME
    
    async def show(self):
        await bot.send_typing(self.channel)
        if self.winner:
            return await respond(
                "result_" + ('draw' if self.winner == 3 else 'win'),
                self.channel, self.noughts)
        else:
            game_hash = hash(self)
            link = CACHE.get(game_hash)

            # equal hash(game) <-> equal render
            # Discord attachment links are cached, so we don't have
            # to re-render and upload each game. Delete cache if
            # you change the rendering engine, though.
            if False:
                await bot.send_message(self.channel, embed={'link': link})
            else:
                # render game
                file_path = RENDER_FILE_PATH(self, game_hash)
                self.render.draw().save(file_path)
                image_sent = await bot.send_file(self.channel, file_path)

                # remove local file, and save link to cache for future reference
                os.remove(file_path)
                link = image_sent.attachments[0]['url']
                CACHE[game_hash] = link
                save_cache()

            return await respond(self.state, self.channel, self.current_user)

    current_user = property(lambda s: s.noughts if s.player == 1 else s.crosses)
    opponent = property(lambda s: s.noughts if s.player == 2 else s.crosses)
    users = property(lambda s: (s.noughts, s.crosses))
    is_solo = property(lambda s: s.noughts == s.crosses)

    def __repr__(self):
        return '<Discord MNAC ({}, {})>'.format(self.noughts, self.crosses)



#
# %% Data
#



def _dL(path):
    if not path:
        return {}
    with open(path, encoding='utf8') as f:
        return json.load(f)

printf('Loading configuration...')

LANGUAGES = _dL(PATH_LANGUAGES)
# {lang_code(s): {response_id(s): translation}}

CONFIG = _dL(PATH_CONFIG)
# channel_id(s): {'language': lang_code, 'state': state}
# where state is null or either:
  # {'kind': 'lobby', 'noughts': str, 'time_started': int)
  # {'kind': 'game', ...}



# deserialise lobbies
# (games must be deserialised when the bot is loaded)
for chan in CONFIG:
    state = CONFIG[chan]['state']
    if isinstance(state, dict) and state['kind'] == 'lobby':
        CONFIG[chan]['state']['noughts'] = bot.get_user_info(state['noughts'])

CACHE = _dL(PATH_CACHE)
# {gameMapping(s): image_url}

# getters and setters
def save_server():
    printf('Saving server config...')
    serial = {}
    # serialise config
    for chan in CONFIG:
        state = CONFIG[chan]['state']
        if isinstance(state, DiscordMNAC):
            state = state.toSerial()
        else:
            state = copy.deepcopy(state)
            if isinstance(state, dict) and state['kind'] == 'lobby':
                state['noughts'] = state['noughts'].id
        
        serial[chan] = {'language': CONFIG[chan]['language'], 'state': state}
            
    
    with open(PATH_CONFIG, 'w', encoding='utf8') as f:
        json.dump(serial, f)

def save_cache():
    printf('Saving render cache...')
    with open(PATH_CACHE, 'w', encoding='utf8') as f:
        json.dump(CACHE, f)

CONF_DEFAULT = {'language': DEFAULT_LANGUAGE, 'state': None}
def config(chan):
    conf = CONFIG.get(chan.id)
    if not conf:
        CONFIG[chan.id] = conf = dict(CONF_DEFAULT)
        # don't save - the server hasn't interacted yet
    return LANGUAGES[conf['language']], conf['state']



#
# %% Message handling
#



COMMANDS = 'help tutorial status start stop play random lang'.split()
MEMES = (
    ('donger', 'ᕦ(ຈل͜ຈ)ᕤ'),
    )

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
        if new != CONFIG[chan.id]['state']:
            CONFIG[chan.id]['state'] = new
            save_server()
        return new

    # deserialise game entries
    if isinstance(game, dict) and game['kind'] == 'game':
        game = await DiscordMNAC.fromSerial(game)
        CONFIG[chan.id]['state'] = game
    
    if isinstance(game, DiscordMNAC):
        mode = 'game'
        if game.has_expired:
            game = set_game(None)
            mode = 'chat'
        
    elif isinstance(game, dict):
        # Lobby - purge if reached limit
        mode = 'lobby'
        lobby_seconds_left = MAX_LOBBY_TIME - (now - game['time_started'])
        if lobby_seconds_left < 0:
            game = set_game(None)
            mode = 'chat'
    
    if mode == 'game' and user in game.users and isinstance(getIndex(content), int):
        # players can skip the whole '/play' malarkey
        args = content.split()
        command = 'play'
    
    elif content.startswith(PREFIX):
        # standard prefixed response
        args = content[len(PREFIX):].split()
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
        for find, response in MEMES:
            if find in content:
                return await r(response)
        return

    if command in COMMANDS:
        printf('{:<20} {:<5} {:<10} : {}({})', chan.id, mode, user.name, command, ', '.join(args))
    else:
        return await r('command_unknown', command=command)

    if command == 'help':
        # list off commands
        await r('help' + '_start'*('start' in args))

    elif command == 'status':
        # give status of game / re-print game
        if mode == 'game':
            await game.show()
        else:
            await r('status_{}'.format(
                'solo' if chan.is_private else 'lobby' if mode == 'lobby' else 'empty'))

    elif command == 'lang':
        if args:
            lang = args.pop(0)
            if lang in LANGUAGES:
                CONFIG[chan.id]['language'] = lang
                save_server()
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
            await r('lobby_open', time_left=MAX_LOBBY_TIME)
        
        

    elif mode == 'game' and user in game.users:

        async def play(direction):
            game.play(direction)
            await game.show()
            if game.winner:
                set_game(None)
            else:
                save_server()

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
