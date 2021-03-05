import logging
from typing import Dict, Type

from discord.ext import commands

from miyu_bot.bot import models
from miyu_bot.bot.bot import D4DJBot
from miyu_bot.bot.models import PreferenceScope


class Preferences(commands.Cog):
    bot: D4DJBot

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.command(name='setpref',
                      description='',
                      help='')
    async def setpref(self, ctx: commands.Context, scope: str, name: str, value: str):
        scope = preference_scope_aliases.get(scope)
        if not scope:
            await ctx.send(f'Invalid scope "{scope.scope_name}".')
            return
        if scope != models.User and not (await ctx.bot.is_owner(ctx.author) or
                                         ctx.author.guild_permissions.manage_channels):
            await ctx.send(f'Altering preferences for scope "{scope.scope_name}" requires administrator permissions.')
            return
        if name not in scope.preferences:
            await ctx.send(f'Invalid preference "{name}" for scope "{scope.scope_name}".')
            return
        preference = scope.preferences[name]
        if validation_error_message := preference.validate(value):
            await ctx.send(f'Invalid value "{value}" for preference "{name}": {validation_error_message}')
        entry = await scope.get_from_context(ctx)
        if not entry:
            await ctx.send(f'Scope "{scope.scope_name}" not available in current channel.')
            return
        original = entry.get_preference(name)
        entry.set_preference(name, value)
        await entry.save()
        await ctx.send(f'Successfully changed preference "{name}" '
                       f'for scope "{scope.scope_name}" from "{original}" to "{value}".')

    @commands.command(name='getpref',
                      description='',
                      help='')
    async def getpref(self, ctx: commands.Context, scope: str, name: str = ''):
        scope = preference_scope_aliases.get(scope)
        if not scope:
            await ctx.send(f'Invalid scope "{scope}".')
            return
        entry = await scope.get_from_context(ctx)
        if not entry:
            await ctx.send(f'Scope "{scope.scope_name}" not available in current channel.')
            return
        if name:
            if name not in scope.preferences:
                await ctx.send(f'Invalid preference "{name}" for scope "{scope.scope_name}".')
                return
            await ctx.send(str(getattr(entry, scope.preferences[name].attribute_name) or None))
        else:
            await ctx.send(
                '\n'.join(f'{name}: {getattr(entry, pref.attribute_name)}' for name, pref in scope.preferences.items()))

    @commands.command(name='clearpref',
                      description='',
                      help='')
    async def clearpref(self, ctx: commands.Context, scope: str, name: str = ''):
        scope = preference_scope_aliases.get(scope)
        if not scope:
            await ctx.send(f'Invalid scope "{scope}".')
            return
        if name not in scope.preferences:
            await ctx.send(f'Invalid preference "{name}" for scope "{scope.scope_name}".')
            return
        entry = await scope.get_from_context(ctx)
        if not entry:
            await ctx.send(f'Scope "{scope.scope_name}" not available in current channel.')
            return
        entry.clear_preference(name)
        await entry.save()
        await ctx.send(f'Successfully cleared preference "{name}" for scope "{scope.scope_name}".')


preference_scope_aliases: Dict[str, Type[PreferenceScope]] = {
    'user': models.User,
    'self': models.User,
    'channel': models.Channel,
    'server': models.Guild,
    'guild': models.Guild,
}


async def get_preferences(ctx: commands.Context, toggle_user_prefs: bool):
    sources = []
    if user_prefs := await models.User.get_or_none(id=ctx.author.id):
        if not toggle_user_prefs:
            sources.append(user_prefs)
    if channel_prefs := await models.Channel.get_or_none(id=ctx.channel.id):
        sources.append(channel_prefs)
    if guild_prefs := ctx.guild and await models.Guild.get_or_none(id=ctx.guild.id):
        sources.append(guild_prefs)

    preferences = {}
    preference_types = {}
    for source in sources:
        for k, v in source.preferences.items():
            if v.name not in preferences:
                preferences[v.name] = source.get_preference(k)
                preference_types[v.name] = v
    return preferences, preference_types


def setup(bot):
    bot.add_cog(Preferences(bot))
