import os
import discord
from discord.ext import commands
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from xbox import XboxApiClient
import youtube_dl
import requests
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
XBOX_API_KEY = os.getenv('XBOX_API_KEY')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)
spotify = Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))
xbox_client = XboxApiClient(XBOX_API_KEY)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("You need to be in a voice channel to use this command.")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.guild.voice_client.disconnect()
    else:
        await ctx.send("I'm not connected to a voice channel.")

@bot.command()
async def play(ctx, url):
    if not ctx.voice_client:
        await ctx.send("I'm not connected to a voice channel.")
        return

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['formats'][0]['url']

    source = await discord.FFmpegOpusAudio.from_probe(url2)
    ctx.voice_client.play(source)

@bot.command()
async def spotify(ctx, *, query):
    results = spotify.search(q=query, limit=1, type='track')
    if results['tracks']['items']:
        track = results['tracks']['items'][0]
        track_url = track['external_urls']['spotify']
        await ctx.send(f"Playing {track['name']} by {track['artists'][0]['name']}\n{track_url}")
    else:
        await ctx.send("No results found for that query.")

@bot.command()
async def xbox(ctx, gamer_tag, *, message):
    xbox_client.send_message(gamer_tag, message)
    await ctx.send(f"Sent message to {gamer_tag} via Xbox.")

@bot.command()
async def search(ctx, *, query):
    # Search on Spotify
    spotify_results = spotify.search(q=query, limit=1, type='track')
    spotify_message = "Spotify Results:\n"
    if spotify_results['tracks']['items']:
        track = spotify_results['tracks']['items'][0]
        track_url = track['external_urls']['spotify']
        spotify_message += f" - {track['name']} by {track['artists'][0]['name']}\n{track_url}\n"
    else:
        spotify_message += " - No results found\n"

    # Search on YouTube
    ydl_opts = {'default_search': 'auto', 'format': 'bestaudio/best'}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        youtube_info = ydl.extract_info(f"ytsearch:{query}", download=False)
        youtube_message = "YouTube Results:\n"
        if 'entries' in youtube_info and youtube_info['entries']:
            entry = youtube_info['entries'][0]
            youtube_message += f" - {entry['title']}\n{entry['webpage_url']}\n"
        else:
            youtube_message += " - No results found\n"

    await ctx.send(spotify_message + "\n" + youtube_message)

def get_oauth2_token(auth_code):
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post('https://login.live.com/oauth20_token.srf', data=data, headers=headers)
    return response.json()

bot.run(DISCORD_TOKEN)
