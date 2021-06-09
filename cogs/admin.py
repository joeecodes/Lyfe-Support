import discord, platform, datetime, logging, asyncio
from discord.ext import commands
import platform, datetime
from pathlib import Path
cwd = Path(__file__).parents[1]
cwd = str(cwd)
import utils.json

class Admin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        data = utils.json.read_json("blacklist")
        for item in data["blacklistedUsers"]:
            self.bot.blacklisted_users.append(item)
        print("- Admin Cog loaded")

    @commands.command(aliases=['staffhelp', 'mhelp', 'shelp'])
    @commands.has_any_role("Developer", "Head Moderator", "Moderator", "Trial Moderator")
    async def modhelp(self, ctx):
        embed = discord.Embed(title=":herb: Staff Commands List", color=discord.Color.red())
        embed.add_field(name=f"{self.bot.prefix}purge (limit)", value="Group delete an amount of messages.", inline=False)
        embed.add_field(name=f"{self.bot.prefix}ban (user) [reason]", value="Ban a user from the server.", inline=False)
        embed.add_field(name=f"{self.bot.prefix}kick (user) [reason]", value="Kick a user from the server.", inline=False)
        embed.add_field(name=f"{self.bot.prefix}mute (user) [time] [reason]", value="Prevent a user from sending messages, reacting to messages or speaking in channels.", inline=False)
        embed.add_field(name=f"{self.bot.prefix}unmute (user)", value="Unmute a user.", inline=False)
        embed.add_field(name=f"{self.bot.prefix}blacklist (user)", value="Rarely used: Prevent someone from using bot commands.", inline=False)
        embed.add_field(name=f"{self.bot.prefix}unblacklist (user)", value="Rarely used: Allow someone to using bot commands again.", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_any_role("Developer", "Head Moderator", "Moderator", "Trial Moderator")
    async def purge(self, ctx, amount: int):
        if not amount:
            await ctx.message.delete()
            return await ctx.author.send(f"Usage: `{self.bot.prefix}purge (limit)`")
        elif amount <= 250:
            await ctx.channel.purge(limit=amount + 1)
            await ctx.send(f":wastebasket: Deleted {amount} messages.", delete_after=3)
        else:
            await ctx.message.delete()
            await ctx.author.send("Too much! The limit is 250.")

    @purge.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument):
            await ctx.message.delete()
            await ctx.author.send(f"Usage: `{self.bot.prefix}purge (limit)`")

    # --------------------------------------------------------------------------
    # ----- COMMAND: -----------------------------------------------------------
    # ----- BLACKLIST ----------------------------------------------------------
    # --------------------------------------------------------------------------

    @commands.command()
    @commands.has_any_role("Developer", "Head Moderator", "Moderator", "Trial Moderator")
    async def blacklist(self, ctx, member: discord.Member):
        if ctx.message.author.id == member.id:
            return await ctx.send("You can't blacklist yourself.")

        data = utils.json.read_json("blacklist")

        if member.id in data["blacklistedUsers"]:
            return await ctx.send("This user is already blacklisted.")

        data["blacklistedUsers"].append(member.id)
        self.bot.blacklisted_users.append(member.id)
        utils.json.write_json(data, "blacklist")
        await ctx.send(f"Blacklisted **{member.name}**.")
        print(f"{ctx.author.name} blacklisted {member.name}")

    # ----- ERROR HANDLER ------------------------------------------------------

    @blacklist.error
    async def blacklist_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            return await ctx.send("I couldn't find that user.")
        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f"Usage: `{self.bot.prefix}blacklist (user)`")

    # --------------------------------------------------------------------------
    # ----- COMMAND: -----------------------------------------------------------
    # ----- UNBLACKLIST --------------------------------------------------------
    # --------------------------------------------------------------------------

    @commands.command()
    @commands.has_any_role("Developer", "Head Moderator", "Moderator", "Trial Moderator")
    async def unblacklist(self, ctx, member: discord.Member):
        data = utils.json.read_json("blacklist")

        if member.id not in data["blacklistedUsers"]:
            return await ctx.send("That user isn't blacklisted.")

        data["blacklistedUsers"].remove(member.id)
        self.bot.blacklisted_users.remove(member.id)
        utils.json.write_json(data, "blacklist")
        await ctx.send(f"Unblacklisted **{member.name}**.")
        print(f"{ctx.author.name} unblacklisted {member.name}")

    # ----- ERROR HANDLER ------------------------------------------------------

    @unblacklist.error
    async def unblacklist_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            return await ctx.send("I couldn't find that user.")
        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send("Usage: `.unblacklist (user)`")

    # --------------------------------------------------------------------------
    # ----- COMMAND: -----------------------------------------------------------
    # ----- LOGOUT -------------------------------------------------------------
    # --------------------------------------------------------------------------

    @commands.command(aliases=['disconnect', 'stop', 's'])
    @commands.has_any_role("Developer")
    async def logout(self, ctx):
        if self.bot.maintenancemode:
            return
        await ctx.send("Stopping.")
        await self.bot.logout()

    # ----- BASIC SERVER MODERATION --------------------------------------------

    @commands.command()
    @commands.has_any_role("Developer", "Head Moderator", "Moderator", "Trial Moderator")
    async def ban(self, ctx, user: discord.Member, *, reason="none provided"):
        if not user:
            return await ctx.send("Please specify a user.")

        if user == ctx.author:
            return await ctx.send("You cannot punish yourself.")

        try:
            await user.ban(reason=f"Banned by {ctx.author} for {reason}")
            await ctx.send(f"**{user}** banned for {reason}.")

        except discord.Forbidden:
            return await ctx.send("I couldn't ban that user.")

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            return await ctx.send("I couldn't find that user.")
        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f"Usage: `{self.bot.prefix}ban (user) [reason]`")


    # ----- KICKING -----
    @commands.command()
    @commands.has_any_role("Developer", "Head Moderator", "Moderator", "Trial Moderator")
    async def kick(self, ctx, user: discord.Member, *, reason="none provided"):
        if not user:
            return await ctx.send("Please specify a user.")

        if user == ctx.author:
            return await ctx.send("You cannot punish yourself.")

        try:
            await user.kick(reason=f"Kicked by {ctx.author} for {reason}")
            await ctx.send(f"**{user}** was kicked.")

        except discord.Forbidden:
            return await ctx.send("I couldn't kick that user.")

    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            return await ctx.send("I couldn't find that user.")
        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f"Usage: `{self.bot.prefix}kick (user) [reason]`")

    # ----- MUTING -----

    @commands.command()
    @commands.has_any_role("Developer", "Head Moderator", "Moderator", "Trial Moderator")
    async def mute(self, ctx, user: discord.Member, duration=None, *, reason="none provided"):
        if not user:
            return await ctx.send("Please specify a user.")

        if user == ctx.author:
            return await ctx.send("You cannot punish yourself.")

        if user == self.bot.user:
            return await ctx.send("Very funny...")

        mutedrole = discord.utils.get(ctx.guild.roles, name='Muted')
        if mutedrole is None:
            return await ctx.send("Please set up a `Muted` role.")

        if mutedrole in user.roles:
            return await ctx.send("This user is already muted.")

        timeEndings = ('s', 'm', 'h', 'd')
        if duration != None and duration.endswith(timeEndings) and any(char.isdigit() for char in duration.strip("smhd")):
            try:
                await user.add_roles(mutedrole) # 60 secs in a minute 3600 in an hour 86400 in a day
            except discord.Forbidden:
                return await ctx.send("I couldn't mute that user.")

            if duration.endswith('s'): # SECONDS
                await ctx.send(f"**{user}** has been muted by {ctx.author} for {duration.strip('s')} second(s).")
                await asyncio.sleep(int(duration.strip('s')))
                await user.remove_roles(mutedrole)

            elif duration.endswith('m'): # MINUTES
                await ctx.send(f"**{user}** has been muted by {ctx.author} for {duration.strip('m')} minute(s).")
                await asyncio.sleep(int(duration.strip('m')) * 60)
                await user.remove_roles(mutedrole)

            elif duration.endswith('h'): # HOURS
                await ctx.send(f"**{user}** has been muted by {ctx.author} for {duration.strip('h')} hour(s).")
                await asyncio.sleep(int(duration.strip('h')) * 3600)
                await user.remove_roles(mutedrole)

            elif duration.endswith('d'): # DAYS
                await ctx.send(f"**{user}** has been muted by {ctx.author} for {duration.strip('d')} day(s).")
                await asyncio.sleep(int(duration.strip('d')) * 86400)
                await user.remove_roles(mutedrole)

            return

        try:
            await user.add_roles(mutedrole)
        except discord.Forbidden:
            return await ctx.send("I couldn't mute that user.")

        await ctx.send(f"**{user}** has been muted indefinitley.")

    @mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            return await ctx.send("I couldn't find that user.")
        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f"Usage: `{self.bot.prefix}mute (user) [reason]`")

    @commands.command()
    @commands.has_any_role("Developer", "Head Moderator", "Moderator", "Trial Moderator")
    async def unmute(self, ctx, user: discord.Member):
        if not user:
            return await ctx.send("Please specify a user.")

        mutedrole = discord.utils.get(ctx.guild.roles, name='Muted')

        if mutedrole not in user.roles:
            return await ctx.send("This user is not muted.")

        if mutedrole in user.roles:
            await user.remove_roles(mutedrole)
            await ctx.send(f"**{user}** has been unmuted.")

    @unmute.error
    async def unmute_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            return await ctx.send("I couldn't find that user.")
        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f"Usage: `{self.bot.prefix}unmute (user) [reason]`")

    @commands.command()  # adds people to the channel
    @commands.has_guild_permissions(manage_channels=True)
    @commands.has_any_role("Developer", "Head Moderator")
    async def add(self, ctx, member: discord.Member):
        if len(ctx.message.mentions) == 0:
            try:
                member = self.bot.get_user(int(member.id))
                if member is None:
                    return await ctx.send("I couldn't find that user.\n**Tip:** Mention them or use their id.")
            except ValueError:
                return await ctx.send("I couldn't find that user.\n**Tip:** Mention them or use their id.")
        else:
            member = ctx.message.mentions[0]

        if ctx.message.author.id == member.id:
            return await ctx.send("You can't add yourself to the channel!")

        channel = ctx.channel
        if member in channel.overwrites:
            return await channel.send("This user can already see this channel")
        else:
            overwrite = discord.PermissionOverwrite()
            overwrite.send_messages = True
            overwrite.read_messages = True
            await channel.set_permissions(member, overwrite=overwrite, reason="Added via command")
            return await channel.send("Done")

    @commands.command()  # adds people to the channel
    @commands.has_guild_permissions(manage_channels=True)
    @commands.has_any_role("Developer", "Head Moderator")
    async def remove(self, ctx, member: discord.Member):
        if len(ctx.message.mentions) == 0:
            try:
                member = self.bot.get_user(int(member.id))
                if member is None:
                    return await ctx.send("I couldn't find that user.\n**Tip:** Mention them or use their id.")
            except ValueError:
                return await ctx.send("I couldn't find that user.\n**Tip:** Mention them or use their id.")
        else:
            member = ctx.message.mentions[0]

        if ctx.message.author.id == member.id:
            return await ctx.send("You can't add removed yourself from the channel!")


        channel = ctx.channel
        if member not in channel.overwrites:
            return await channel.send("That user isn't in the channel's permissions")
        else:
            await channel.set_permissions(member, overwrite=None, reason="Removed via command")
            return await channel.send("Done")

    @commands.command()
    @commands.has_any_role("Developer", "Head Moderator")
    async def changelog(self, ctx, ping=False, version=None, *, changelog):
        channel = self.bot.get_channel(851222738198593546)
        if ping is False:
            embed = discord.Embed(title=":tada: **New Update**", description="The devs have updated Lyfe! Read the changelog here:", colour=discord.Colour.green())
            embed.add_field(name="New Version:", value="`"+version+"`\n", inline=False)
            embed.add_field(name="**Changelog**:", value=changelog, inline=False)
            await ctx.send("Sent the changelog!")
            return await channel.send(embed=embed)
        else:
            embed = discord.Embed(title=":tada: **New Update**",
                                  description="The devs have updated Lyfe! Read the changelog here:",
                                  colour=discord.Colour.green())
            embed.add_field(name="New Version:", value="`" + version + "`\n", inline=False)
            embed.add_field(name="**Changelog**:", value=changelog, inline=False)
            await ctx.send("Sent the changelog!")
            await channel.send("<@&851482269038542858>")
            return await channel.send(embed=embed)


    @changelog.error
    async def changelog_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(
                f"Missing args.\nUsage: `{self.bot.prefix}changelog (ping[True|False]) (version) (changelog)`")


    @commands.command()
    @commands.has_any_role("Developer", "Head Moderator")
    async def announce(self, ctx, ping=False, title=None, *, contents):
        channel = self.bot.get_channel(851222728039858197)
        if title is None:
            title = "**Announcement**"
        if ping is False:
            embed = discord.Embed(title=":mega: "+title, description=contents, colour=discord.Colour.blurple())
            await ctx.send("Sent the announcement!")
            return await channel.send(embed=embed)
        else:
            embed = discord.Embed(title=":tada: " + title, description=contents, colour=discord.Colour.blurple())
            await channel.send("<@&851482232883249192>")
            await ctx.send("Sent the announcement!")
        return await channel.send(embed=embed)


    @announce.error
    async def announce_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(
                f"Missing args.\nUsage: `{self.bot.prefix}announce (ping[True|False]) (title) (contents)`")
        
    @commands.command()
    @commands.has_any_role("Developer", "Head Moderator")
    async def giveaway(self, ctx):
        await ctx.send("Giveaway config started.")

        questionList = [
            ["What channel should it be in?", "Mention the channel"],
            ["How long should this giveaway last?", "`d|h|m|s`"],
            ["What are you giving away?", "I.E. Your soul hehe"]
        ]
        answers = {}

        for i, question in enumerate(questionList):
            answer = await GetMessage(self.bot, ctx, question[0], question[1])

            if not answer:
                await ctx.send("You failed to answer, please answer quicker next time.")
                return

            answers[i] = answer

        embed = discord.Embed(name="Giveaway content")
        for key, value in answers.items():
            embed.add_field(name=f"Question: `{questionList[key][0]}`", value=f"Answer: `{value}`", inline=False)

        m = await ctx.send("Are these all valid?", embed=embed)
        await m.add_reaction("✅")
        await m.add_reaction("🇽")

        try:
            reaction, member = await self.bot.wait_for(
                "reaction_add",
                timeout=60,
                check=lambda reaction, user: user == ctx.author
                                             and reaction.message.channel == ctx.channel
            )
        except asyncio.TimeoutError:
            await ctx.send("Confirmation Failure. Please try again.")
            return

        if str(reaction.emoji) not in ["✅", "🇽"] or str(reaction.emoji) == "🇽":
            await ctx.send("Cancelling giveaway!")
            return

        channelId = re.findall(r"[0-9]+", answers[0])[0]
        channel = self.bot.get_channel(int(channelId))

        time = convert(answers[1])
        newtime = str(datetime.timedelta(hours=time))
        giveawayEmbed = discord.Embed(
            title="🎉 __**Giveaway**__ 🎉",
            description=answers[2]
        )
        giveawayEmbed.set_footer(text=f"This giveaway ends {time} seconds from this message.")
        giveawayMessage = await channel.send(embed=giveawayEmbed)
        await giveawayMessage.add_reaction("🎉")

        await asyncio.sleep(time)

        message = await channel.fetch_message(giveawayMessage.id)
        users = await message.reactions[0].users().flatten()
        users.pop(users.index(ctx.guild.me))

        if len(users) == 0:
            await channel.send("No winner was decided")
            return

        winner = random.choice(users)

        return await channel.send(f"**Congrats {winner.mention}!**\nPlease contact {ctx.author.mention} about your prize.")

    @commands.command()
    @commands.has_any_role("Developer", "Head Moderator")
    async def nick(self, ctx, member: discord.Member, *, nick):
        await member.edit(reason="Updated nickname", nick=nick)
        return await ctx.send(f"Changed **{member}'s** nick to **{nick}**")

    @commands.command()
    @commands.has_any_role("Developer")
    async def listguilds(self, ctx):
        messages = []
        for guild in self.bot.guilds:
            messages.append(f"{guild.name}")
        await ctx.send("\n".join(messages))
        return

def setup(bot):
    bot.add_cog(Admin(bot))
