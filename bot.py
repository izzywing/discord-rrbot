import discord
from discord.ext import commands
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Required for member-related events

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

DATA_FILE = 'data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # The file exists but is empty or invalid
            data = {'players': {}, 'matches': []}
            save_data(data)
            return data
    else:
        # File doesn't exist; initialize with default data
        data = {'players': {}, 'matches': []}
        save_data(data)
        return data

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Load data at startup
data = load_data()

@bot.command()
async def signup(ctx):
    user_id = str(ctx.author.id)
    if user_id in data['players']:
        await ctx.send(f"{ctx.author.mention}, you are already registered!")
    else:
        data['players'][user_id] = {'name': ctx.author.name, 'wins': 0, 'losses': 0}
        save_data(data)
        await ctx.send(f"{ctx.author.mention}, you have been registered!")

@bot.command()
async def report(ctx, opponent: discord.Member, result: str, score: str):
    reporter_id = str(ctx.author.id)
    opponent_id = str(opponent.id)
    result = result.upper()

    # Validate players
    if reporter_id not in data['players'] or opponent_id not in data['players']:
        await ctx.send("Both players must be registered. Use `!signup` to register.")
        return

    # Validate result
    if result not in ['W', 'L']:
        await ctx.send("Result must be 'W' for win or 'L' for loss.")
        return

    # Record match
    match = {
        'reporter': reporter_id,
        'opponent': opponent_id,
        'result': result,
        'score': score
    }
    data['matches'].append(match)

    # Update player stats
    if result == 'W':
        data['players'][reporter_id]['wins'] += 1
        data['players'][opponent_id]['losses'] += 1
    else:
        data['players'][reporter_id]['losses'] += 1
        data['players'][opponent_id]['wins'] += 1

    save_data(data)
    await ctx.send(f"Match reported: {ctx.author.mention} {'won' if result == 'W' else 'lost'} against {opponent.mention} with score {score}.")

@bot.command()
async def leaderboard(ctx):
    # Generate leaderboard
    leaderboard = sorted(data['players'].items(), key=lambda x: x[1]['wins'], reverse=True)
    embed = discord.Embed(title="Leaderboard", color=discord.Color.blue())

    for rank, (user_id, stats) in enumerate(leaderboard, start=1):
        embed.add_field(
            name=f"{rank}. {stats['name']}",
            value=f"Wins: {stats['wins']}, Losses: {stats['losses']}",
            inline=False
        )

    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def reset(ctx):
    data['players'] = {}
    data['matches'] = []
    save_data(data)
    await ctx.send("All player data has been reset for the new season.")

@signup.error
async def signup_error(ctx, error):
    await ctx.send(f"An error occurred: {str(error)}")

@report.error
async def report_error(ctx, error):
    await ctx.send(f"An error occurred: {str(error)}")

@leaderboard.error
async def leaderboard_error(ctx, error):
    await ctx.send(f"An error occurred: {str(error)}")

@reset.error
async def reset_error(ctx, error):
    await ctx.send(f"An error occurred: {str(error)}")

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Bot Commands", color=discord.Color.green())
    embed.add_field(name="!signup", value="Register as a player.", inline=False)
    embed.add_field(name="!report @opponent W/L score", value="Report a match result.", inline=False)
    embed.add_field(name="!leaderboard", value="View the leaderboard.", inline=False)
    embed.add_field(name="!reset", value="Reset all scores (admin only).", inline=False)
    await ctx.send(embed=embed)

# Run the bot
bot.run(TOKEN)
