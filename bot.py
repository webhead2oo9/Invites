import discord
from discord.ext import commands
from discord.commands import slash_command
import sqlite3
from datetime import datetime, timedelta
import os

conn = sqlite3.connect('invites.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS invite_log
             (user_id INTEGER, timestamp DATETIME)''')
conn.commit()

# Add Intents if we need them later, unsure if this will work as is.
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

async def can_generate_invite(user_id):
    c.execute('SELECT timestamp FROM invite_log WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    
    if result:
        last_invite_time = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
        if datetime.now() - last_invite_time < timedelta(hours=12):
            return False, last_invite_time + timedelta(hours=12)
    
    return True, None

@bot.slash_command(name="invite", description="Generate an invite link")
async def invite(ctx: discord.ApplicationContext):
    print(f"Invite requested by {ctx.author} (ID: {ctx.author.id}) at {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    can_generate, next_invite_time = await can_generate_invite(ctx.author.id)
    if not can_generate:
        await ctx.respond(f"You can generate your next invite at {next_invite_time.strftime('%Y-%m-%d at %H:%M')}", ephemeral=True)
        return    
    invite_link = await ctx.channel.create_invite(max_age=43200, # 12 hours in seconds
                                                  max_uses=5,    # Maximum uses
                                                  unique=True)   # Generate a new link every time
    
    #so we can handle reboots
    c.execute('INSERT INTO invite_log (user_id, timestamp) VALUES (?, ?)', (ctx.author.id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    await ctx.respond(f"Here's your invite link: {invite_link}", ephemeral=True)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN_INVITE')
bot.run(DISCORD_TOKEN)
