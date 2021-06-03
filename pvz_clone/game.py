import asyncio
import discord
import json
import math
import random
import re

from discord.ext import commands
from unit import Unit, UNIT_INFOS


class Player():
    def __init__(self, user):
        self.money = 5
        self.user = user
        self.action = []
        self.error = ''

        self.name = user.nick if user.nick else user.name
        if len(self.name) > 25:
            self.name = self.name[:25]


class Game(commands.Cog):

    start_state = ['<:blank:842642757368545300>​🇦​🇧​🇨​🇩​🇪​🇫​🇬​🇭​🇮​🇯​🇰​🇱​🇲​🇳​🇴',
                   '0️⃣🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢⛔⛔⛔',
                   '1️⃣🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢⛔⛔⛔',
                   '2️⃣🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢⛔⛔⛔',
                   '3️⃣🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢⛔⛔⛔',
                   '4️⃣🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢⛔⛔⛔',
                   '5️⃣🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢⛔⛔⛔',
                   '6️⃣🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢⛔⛔⛔',
                   '7️⃣🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢⛔⛔⛔',
                   '8️⃣🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢⛔⛔⛔',
                   '9️⃣🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢⛔⛔⛔',
                   '<:blank:842642757368545300>​🇦​🇧​🇨​🇩​🇪​🇫​🇬​🇭​🇮​🇯​🇰​🇱​🇲​🇳​🇴']

    col_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O']

    enemy_spawns = [[], [], [], [], [], [('101', 4)],
                    [], [], [], [('101', 4)], [('101', 4)],
                    [], [], [], [('101', 4), ('102', 2)],
                    [], [], [], [], [('101', 6)],
                    [], [], [('101', 3), ('103', 2)],
                    [], [], [], [('102', 2), ('103', 4)],
                    [], [], [], [('103', 6)],
                    [], [], [], [('101', 2), ('102', 2), ('103', 2)],
                    [], [], [], [], [('102', 6)],
                    [], [], [('104', 2)],
                    [], [], [], [], [('104', 6)],
                    [], [], [], [('102', 6)], [('104', 4), ('105', 1)],
                    [], [], [], [('104', 3)], [('104', 6)], [('105', 4)],
                    [], [], [], [('102', 6)], [('102', 6)],
                    [], [], [('104', 6)], [('106', 1)],
                    [], [], [], [('104', 6)], [('105', 2)], [('106', 2)],
                    [], [], [('102', 6)], [('102', 6)], [('102', 6)], [('105', 6)], [('106', 6)],
                    [], [], [], [('103', 6)], [('104', 5)], [('105', 5)],
                    [], [], [], [('103', 6)], [('106', 3)],
                    [], [], [], [('105', 4)], [('107', 1)],
                    [], [], [('102', 4), ('105', 2)], [('107', 3)],
                    [], [], [], [], [('107', 6)]]

    def __init__(self, bot):
        self.bot = bot
        self.game_state = self.start_state
        self.discord_players = []
        self.game_players = {}
        self.state = 0      # 0 for idle; 1 for signups; 2 for in progress; 3 for wrapping up.

        self.info_msg = None
        self.board_msgs = []
        self.game_ch = None
        self.signups = None

        self.units = {(i, j): [] for i in range(15) for j in range(10)}
        self.stage = 0
        self.base_hp = 0


    def get_emoji(self, location):
        emoji = '🟢'
        if not self.units[location]:
            if location[0] > 11:
                emoji = '⛔'
            return emoji

        for unit in self.units[location]:
            emoji = unit.emoji
            if not unit.is_attack:
                break
        
        return emoji


    async def display_stats(self, ctx):
        new_info_msg = [f'```TOTAL HEALTH: {self.base_hp}',
                        'Player                    | Money | Action       | Error',
                        '-' * 64]
        for pid in self.game_players:
            player = self.game_players[pid]

            action = ''
            if player.action:
                tile = (f'{self.col_names[player.action[0][0]]}'
                        f'{player.action[0][1]}')
                unit = UNIT_INFOS[str(player.action[1])]['name']
                action = f'{unit} on {tile}'

            new_line = (f'{player.name.ljust(26)}| '
                        f'{str(player.money).ljust(6)}| '
                        f'{action.ljust(13)}| '
                        f'{player.error}')
            new_info_msg.append(new_line)

        new_info_msg.append('```')

        if not self.info_msg:
            self.info_msg = await ctx.send('\n'.join(new_info_msg))
        else:
            await self.info_msg.edit(content='\n'.join(new_info_msg))


    async def display_state(self, ctx):
        # Info display
        await self.display_stats(ctx)

        # Board display
        for row in range(10):
            new_row = self.start_state[row+1][0:3]
            for col in range(15):
                new_row += self.get_emoji((col, row))

            self.game_state[row+1] = new_row

        formatted = ['\n'.join(self.game_state[i:i+4]) for i in range(0, len(self.game_state), 4)]
        for i, line in enumerate(formatted):
            if len(self.board_msgs) > i:
                await self.board_msgs[i].edit(content=line)
            else:
                msg = await ctx.send(line)
                self.board_msgs.append(msg)


    async def edit_signups(self):
        if self.signups:
            player_names = [p.nick if p.nick else p.name for p in self.discord_players]
            player_list = ', '.join(player_names)
            await self.signups.edit(content=f'Currently signed up: {player_list}')


    # Management

    @commands.command(brief='Starts signups for a game.')
    @commands.has_any_role('test', 'The Chesire Cat', 'Teapot', 'Queen of Hearts')
    @commands.guild_only()
    async def start_signups(self, ctx):
        if self.state != 0:
            await ctx.send('Game already in progress.')
            return
        self.state = 1
        self.game_ch = ctx
        await ctx.send('React with ✋ to join!')
        self.signups = await ctx.send('Currently signed up:')
        await self.signups.add_reaction('✋')


    @commands.Cog.listener('on_reaction_add')
    async def add_player(self, reaction, user):
        if (reaction.message.id == self.signups.id and
                reaction.emoji == '✋' and
                self.state == 1):
            if user == self.bot.user:
                return
            
            self.discord_players.append(user)
            await self.edit_signups()


    @commands.Cog.listener('on_raw_reaction_remove')
    async def remove_player(self, payload):
        if (payload.message_id == self.signups.id and
                str(payload.emoji) == '✋' and
                self.state == 1):
            for player in self.discord_players:
                if payload.user_id == player.id:
                    self.discord_players.remove(player)
                    await self.edit_signups()


    @commands.command(brief='Begins the game.')
    async def start_game(self, ctx):
        if self.state == 0 or not self.discord_players:
            await ctx.send('No valid signups.')
            return
        if self.state >= 2:
            await ctx.send('Game already in progress.')
            return
        self.state = 2

        self.base_hp = 150

        for p in self.discord_players:
            self.game_players[p.id] = Player(p)

        unit_help = []
        for uid in UNIT_INFOS:
            u = UNIT_INFOS[uid]
            if u['friendly']:
                u_name = u['name']
                u_emoji = u['emoji']
                u_hp = u['hp']
                u_price = u['price']
                u_desc = u['description']
                unit_help.append({'name': f'{u_emoji} {u_name}',
                                  'value': (f'{u_desc}\n'
                                            f'❤️: {u_hp} | 🪙: {u_price}')})

        game_help = {'title': 'HOW TO PLAY',
                     'description': ('!place UNITNAME TILE (ex: !place sentry a0)\n'
                                     '!cancel to cancel !place'),
                     'fields': unit_help}
        await self.game_ch.send(embed=discord.Embed.from_dict(game_help))

        asyncio.create_task(self.cycle(), name='game-runner')


    @commands.command(brief='Cancels/ends a game.')
    @commands.has_any_role('test')
    async def end_game(self, ctx):
        if self.state == 0:
            await ctx.send('No game in progress.')
            return

        for task in asyncio.all_tasks():
            if task.get_name() == 'game-runner':
                task.cancel()
                break

        win = False
        if self.state >= 3:
            win = True

        self.discord_players = []
        self.game_players = {}
        self.game_state = self.start_state
        self.state = 0

        self.info_msg = None
        self.board_msgs = []
        self.game_ch = None
        self.signups = None

        self.units = {(i, j): [] for i in range(15) for j in range(10)}
        self.stage = 0

        if win:
            await ctx.send('Congration you winned')
        else:
            await ctx.send('Game ended.')


    # Gameplay

    def apply_attack(self, unit, attack):
        unit.hp -= attack.damage


    async def cycle(self):
        while self.state >= 2:

            if self.state >= 3:
                should_end = True
                for t in self.units:
                    for u in self.units[t]:
                        if not u.is_attack and not u.friendly:
                            should_end = False
                            break
                    if not should_end:
                        break
                
                if should_end:
                    await self.end_game(self.game_ch)
                    break

            self.stage += 1
            if self.stage >= len(self.enemy_spawns):
                self.state = 3

            # Handle collisions while spawning enemies
            if self.state < 3:
                rows_left = list(range(10))
                '''
                # Uncomment if you don't want enemies to be able to stack on spawn squares
                for r in rows_left:
                    for u in self.units[(14, r)]:
                        if not u.is_attack:
                            rows_left.remove(r)
                            break
                '''
                for (uid, num_units) in self.enemy_spawns[self.stage]:
                    spawn_rows = random.sample(rows_left, math.ceil(len(self.game_players) / 6 * num_units))
                    rows_left = [r for r in rows_left if r not in spawn_rows]
                    
                    for s_row in spawn_rows:
                        s_tile = (14, s_row)
                        new_enemy = Unit(uid, s_tile)
                        for i, c_unit in enumerate(self.units[s_tile]):
                            if c_unit.is_attack and c_unit.friendly != new_enemy.friendly:
                                self.apply_attack(new_enemy, c_unit)
                                del self.units[s_tile][i]
                                if new_enemy.hp <= 0:
                                    break
                        
                        if new_enemy.hp > 0:
                            self.units[s_tile].append(new_enemy)

            # Remove all leftover dead units
            for location in self.units:
                for i, unit in enumerate(self.units[location]):
                    if unit.hp <= 0:
                        del self.units[location][i]

            for pid in self.game_players:
                player = self.game_players[pid]
                player.money += 1

                # Handle collisions while spawning units
                if player.action:
                    player.money -= UNIT_INFOS[player.action[1]]['price']
                    new_unit = Unit(player.action[1], player.action[0])

                    for i, c_unit in enumerate(self.units[player.action[0]]):
                        if c_unit.is_attack and c_unit.friendly != new_unit.friendly:
                            self.apply_attack(new_unit, c_unit)
                            del self.units[player.action[0]][i]
                            if new_unit.hp <= 0:
                                break

                    if new_unit.hp > 0:
                        self.units[player.action[0]].append(new_unit)
                    player.action = []
                    player.error = ''

            await self.display_state(self.game_ch)
            await asyncio.sleep(0.1)

            # Handle collisions while moving.
            for location in self.units:
                for i, unit in reversed(list(enumerate(self.units[location]))):
                    if unit.has_moved:
                        continue
                    new_loc = tuple(unit.move())
                    update = True

                    # Handle units going offscreen.
                    if new_loc not in self.units:
                        update = False
                        new_loc = (0, 0)

                        if not unit.friendly:
                            base_dmg = unit.damage if hasattr(unit, 'damage') else unit.hp
                            self.base_hp -= base_dmg
                            if self.base_hp < 0:
                                self.base_hp += 1 << 32

                        del self.units[location][i]

                    else:
                        for c_unit in self.units[new_loc]:
                            if not unit.is_attack and not c_unit.is_attack:
                                new_loc = location
                                update = False
                                break

                        for j, c_unit in reversed(list(enumerate(self.units[new_loc]))):
                            if (unit.is_attack != c_unit.is_attack and
                                    unit.friendly != c_unit.friendly):
                                if unit.is_attack:
                                    self.apply_attack(c_unit, unit)
                                    update = False
                                    if i > j:
                                        del self.units[location][i]
                                        if c_unit.hp <= 0:
                                            del self.units[new_loc][j]
                                            break
                                    else:
                                        if c_unit.hp <= 0:
                                            del self.units[new_loc][j]
                                            break
                                        del self.units[location][i]
                                else:
                                    self.apply_attack(unit, c_unit)
                                    if i > j:
                                        if unit.hp <= 0:
                                            del self.units[location][i]
                                            update = False
                                        del self.units[new_loc][j]
                                        if unit.hp <= 0:
                                            break
                                    else:
                                        del self.units[new_loc][j]
                                        if unit.hp <= 0:
                                            del self.units[location][i]
                                            update = False
                                            break

                    if update:
                        unit.location = list(new_loc)
                        self.units[new_loc].append(unit)
                        del self.units[location][i]

            for t in self.units:
                for u in self.units[t]:
                    u.has_moved = False

            await self.display_state(self.game_ch)
            await asyncio.sleep(1)

            # Handle collisions while spawning attacks.
            for location in self.units:
                for unit in self.units[location]:
                    new_atks = unit.attack()

                    for new_atk in new_atks:
                        new_loc = tuple(new_atk[1])
                        if new_loc not in self.units:
                            break
                        atk = Unit(new_atk[0], new_atk[1], is_attack=True)
                        update = True

                        for j, c_unit in enumerate(self.units[new_loc]):
                            if not c_unit.is_attack and atk.friendly != c_unit.friendly:
                                self.apply_attack(c_unit, atk)
                                if c_unit.hp <= 0:
                                    del self.units[new_loc][j]
                                update = False
                                break
                        
                        if update:
                            self.units[new_loc].append(atk)

            await self.display_state(self.game_ch)
            await asyncio.sleep(0.1)


    @commands.command(brief='Buy a unit.')
    async def place(self, ctx, unit_name, tile):
        sender = ctx.message.author
        if self.state < 2:
            await ctx.send('No game in progress.')
            return
        uid = ''
        for u in UNIT_INFOS:
            if UNIT_INFOS[u]['name'].lower() == unit_name.lower():
                uid = u
                break
        if sender.id not in self.game_players:
            await sender.send(f'You are not in an active game!')
            return
        if not uid:
            self.game_players[sender.id].error = f'Invalid unit ({unit_name} at {tile})'
            await self.display_state(self.game_ch)
            return
        if not UNIT_INFOS[uid]['friendly']:
            self.game_players[sender.id].error = f'Invalid unit ({unit_name} at {tile})'
            await self.display_state(self.game_ch)
            return
        if self.game_players[sender.id].money < UNIT_INFOS[uid]['price']:
            self.game_players[sender.id].error = f'Not enough money ({unit_name} at {tile})'
            await self.display_state(self.game_ch)
            return

        loc = re.match('(?P<col>[A-Za-z])(?P<row>\d)', tile)
        try:
            col = ord(loc.group('col').lower()) - 97
            row = int(loc.group('row'))
            location = (col, row)

            if col > 11:
                self.game_players[sender.id].error = f'Invalid tile ({tile})'
                await self.display_state(self.game_ch)
                return
            for u in self.units[location]:
                if not u.is_attack:
                    self.game_players[sender.id].error = f'Unit already on {tile}!'
                    await self.display_state(self.game_ch)
                    return
            for p in self.game_players:
                if not self.game_players[p].action or p == sender.id:
                    continue
                if self.game_players[p].action[0] == location:
                    self.game_players[sender.id].error = f'Unit already on {tile}!'
                    await self.display_state(self.game_ch)
                    return

            self.game_players[sender.id].action = [location, uid]
            self.game_players[sender.id].error = ''
            await self.display_stats(self.game_ch)
        except AttributeError:
            self.game_players[sender.id].error = f'Invalid tile: ({tile})'
            await self.display_state(self.game_ch)


    @commands.command(brief='Cancels placement action')
    async def cancel(self, ctx):
        sender = ctx.message.author.id
        if self.state >= 2 and sender in self.game_players:
            self.game_players[sender].error = ''
            if self.game_players[sender].action:
                self.game_players[sender].action = []
                await self.display_stats(self.game_ch)


    @commands.Cog.listener()
    async def on_message(self, msg):
        if self.state >= 2:
            if msg.channel == self.game_ch.channel and msg.author != self.bot.user:
                await msg.delete()
