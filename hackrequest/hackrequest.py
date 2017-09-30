import os
import discord
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from cogs.utils import checks


class hackrequest:
    """Custom Cog for applications"""
    def __init__(self, bot):
        self.bot = bot
        self.settings = dataIO.load_json('data/hackrequest/settings.json')
        for s in self.settings:
            self.settings[s]['usercache'] = []
    def save_json(self):
        dataIO.save_json("data/hackrequest/settings.json", self.settings)

    @commands.group(name="hset", pass_context=True, no_pm=True)
    async def appset(self, ctx):
        """configuration settings"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)
    def initial_config(self, server_id):
        """makes an entry for the server, defaults to turned off"""
        if server_id not in self.settings:
            self.settings[server_id] = {'inactive': True,
                                        'output': [],
                                        'cleanup': False,
                                        'usercache': [],
                                        'multiout': False
                                        }
            self.save_json()

    @checks.admin_or_permissions(Manage_server=True)
    @appset.command(name="reset", pass_context=True, no_pm=True)
    async def fix_cache(self, ctx):
        """Reset cache for applications"""
        server = ctx.message.server
        self.initial_config(ctx.message.server.id)
        self.settings[server.id]['usercache'] = []
        self.save_json()
        await self.bot.say("Cache has been reset")

    @checks.admin_or_permissions(Manage_server=True)
    @appset.command(name="roles", pass_context=True, no_pm=True)
    async def rolecreation(self, ctx):
        server = ctx.message.server
        author = ctx.message.author
        aprole = discord.utils.get(server.roles, name="Hack Requester")
        if aprole not in server.roles:
            await self.bot.create_role(server, name="Hack Requester")
            await self.bot.say("All done!")
        else:
            await self.bot.say("Roles already present")

    @checks.admin_or_permissions(Manage_server=True)
    @appset.command(name="channel", pass_context=True, no_pm=True)
    async def setoutput(self, ctx, chan=None):
        """sets the place to output application embed to when finished."""
        server = ctx.message.server
        if server.id not in self.settings:
            self.initial_config(server.id)
        if chan in self.settings[server.id]['output']:
            return await self.bot.say("Channel already set as output")
        for channel in server.channels:
            if str(chan) == str(channel.id):
                if self.settings[server.id]['multiout']:
                    self.settings[server.id]['output'].append(chan)
                    self.save_json()
                    return await self.bot.say("Channel added to output list")
                else:
                    self.settings[server.id]['output'] = [chan]
                    self.save_json()
                    return await self.bot.say("Channel set as output")
        await self.bot.say("I could not find a channel with that id")

    @checks.admin_or_permissions(Manage_server=True)
    @appset.command(name="toggle", pass_context=True, no_pm=True)
    async def reg_toggle(self, ctx):
        """Toggles applications for the server"""
        server = ctx.message.server
        if server.id not in self.settings:
            self.initial_config(server.id)
        self.settings[server.id]['inactive'] = \
            not self.settings[server.id]['inactive']
        self.save_json()
        if self.settings[server.id]['inactive']:
            await self.bot.say("Request disabled.")
        else:
            await self.bot.say("Request enabled.")

    @commands.command(name="request", pass_context=True)
    async def application(self, ctx):
        """"make an application by following the prompts"""
        author = ctx.message.author
        server = ctx.message.server
        aprole = discord.utils.get(server.roles, name="Hack Requester")
        if server.id not in self.settings:
            return await self.bot.say("Applications are not setup on this server!")
        if self.settings[server.id]['inactive']:
            return await self.bot.say("We are not currently accepting applications, Try again later")
        if aprole in author.roles:
            await self.bot.say("{}You have already applied to this server!".format(author.mention))
        else:
            await self.bot.say("{}Ok lets start the application".format(author.mention))
            while True:
                avatar = author.avatar_url if author.avatar \
                    else author.default_avatar_url
                em = discord.Embed(timestamp=ctx.message.timestamp, title="ID: {}".format(author.id), color=discord.Color.blue())
                em.set_author(name='Hack application for {}'.format(author.name), icon_url=avatar)
                gamemsg = await self.bot.send_message(author, "What game you want to be hacked?")
                while True:
                    game = await self.bot.wait_for_message(channel=gamemsg.channel, author=author, timeout=30)
                    if game is None:
                        await self.bot.send_message(author, "Sorry you took to long, please try again later!")
                        break
                    else:
                        em.add_field(name="Game: ", value=game.content, inline=True)
                        break
                if game is None:
                    break
                haxmsg = await self.bot.send_message(author, "Info:")
                while True:
                    hax1 = await self.bot.wait_for_message(channel=haxmsg.channel, author=author, timeout=30)
                    if hax1 is None:
                        await self.bot.send_message(author, "Timed out, Please run command again.")
                        break
                    else:
                        em.add_field(name="Features:", value=hax1.content, inline=True)
                        break
                if hax1 is None:
                    break
                whymsg = await self.bot.send_message(author, "What are the features you want on the hack?")
                while True:
                    why = await self.bot.wait_for_message(channel=whymsg.channel, author=author, timeout=60)
                    if why is None:
                        await self.bot.send_message(author, "Timed out, Please Re-Run command and try again!")
                        break
                    else:
                        em.add_field(name="Why do you want Chase to hack this game", value=why.content, inline=False)
                        aprole = discord.utils.get(server.roles, name="Hack Requester")
                        await self.bot.add_roles(author, aprole)
                        await self.bot.send_message(author, "You have finished the application, Thank you. You can submit another game "
                                                            "every 24 hours. You can't submit same game, last you submit or you will be"
                                                            " blacklisted for using the bot, hack request or might get banned!")
                        break
                if why is None:
                    break
                for output in self.settings[server.id]['output']:
                    where = server.get_channel(output)
                    if where is not None:
                        await self.bot.send_message(where, embed=em)
                        break
                    break
                return

def check_folder():
    f = 'data/hackrequest'
    if not os.path.exists(f):
        os.makedirs(f)


def check_file():
    f = 'data/hackrequest/settings.json'
    if dataIO.is_valid_json(f) is False:
        dataIO.save_json(f, {})


def setup(bot):
    check_folder()
    check_file()
    n = hackrequest(bot)
    bot.add_cog(n)
