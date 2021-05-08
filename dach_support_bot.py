#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat 24.01.2020
This is version 0.8 of the new and improved Dach-Bot
last update: 08.05.2021

"""
import datetime
import locale
import discord
import configparser
from forecastpy import Weather, Unit
from discord.ext.commands import CommandNotFound
from discord.ext.commands import Bot, has_role
from discord.ext import commands, tasks
from discord.utils import get

import crypto_connection as crypto
import hive_connection as hive
import db_connection as db

# setting locales and intents for discord
intents = discord.Intents.default()
intents.members = True
locale.setlocale(locale.LC_ALL, '')

# read the config file and set the correct parameters
config = configparser.ConfigParser()
config.read('dach_support_bot.ini')
admin_id = config["General"]["admin_id"]
guild_id = int(config["General"]["guild_id"])
discord_role_name = config["General"]["role_to_distribute"]
block_number_starting = int(config["Hive"]["starting_block_number"])
BOT_PREFIX = config["General"]["bot_prefix"]
TOKEN = config["General"]["token"]
HIVE_PW = config["Hive"]["password"]

client = Bot(command_prefix=BOT_PREFIX, intents=intents)

# waiting until the bot is ready and starting the automated checking of registries
@client.event
async def on_ready():
    print("Bot is online and connected to Discord")
    print("with the ID: %s running on %s" % (client.user.id, client.user.name))
    
    automated_checkreg.start()

# print kudos and version of the bot
@client.command(description="Informationen über den Versionierungsstand des Bots",
                brief="Info über Version des Bots",
                aliases=["ver", "Ver","v"])
async def version(ctx, *arg):
    await ctx.send("D-A-CH Bot Version 0.9, brought to you by jedigeiss\n**Thanks to:** louis88, rivalzzz, felixxx and Bennybär")

# Get weather info from Openweathermap.org and displaying this in Discord
@client.command(description="Anzeige des Wetters und der Vorhersage für die nächsten Tage, Daten von Openweathermap.org",
                brief="Wettervorhersage",
                aliases=["wetter"])
async def Wetter(ctx, *arg):
    weather = Weather('ff7689fdb6cd24b12a313362d4815920')
    place = arg[0]
    data = weather.get_current_weather(place, unit=Unit.METRIC)
    temperature = data["forecast"]["temperature"]
    location = data["name"]
    condition = data["forecast"]["main"]
      
    embed = discord.Embed(title="Wetter Übersicht für : %s "% (location), color=0x00ff00)
    embed.add_field(name="Wetterlage Heute", value="%s bei %s Grad Celsius" % (condition,temperature))
    embed.timestamp=datetime.datetime.utcnow()
    embed.set_footer(text="fresh from the DACH-BOT and Openweathermap.org")
    await ctx.send(embed=embed)

#  Get basic info about a Hive user account 
@client.command(description="Informationen über den einen Hivian",
                brief="Info über Hivians",
                aliases=["Info"])
async def info(ctx, account_name):
    level = "short"
    data = hive.basic_info(account_name, level)
    if data["error"] == 1:
        await ctx.send("Der Account %s existiert nicht" % account_name)
    # building the embed to broadcast via discord
    else:
        embed = discord.Embed(title="Konto Information", description="[%s](%s)"% (account_name.title(), data["hivelink"]), color=0x00ff00)
        embed.add_field(name="Effektive HP", value="%s HP" % data["sp"])
        embed.add_field(name="Votingpower", value="%s Prozent" % data["vp"])
        embed.add_field(name="Reputation", value = data["rep"])
        embed.add_field(name="Angemeldet seit", value="%s, %s Tage" % (datetime.datetime.strftime( data["created"],"%d.%m.%Y"), data["since"]))
        embed.add_field(name="Letzte Aktion auf Hive", value=datetime.datetime.strftime( data["latestactivity"], "%d.%m.%Y %H:%M"))
        embed.add_field(name="Wert in Euro", value="%s Euro" % data["worth"])
        embed.add_field(name="Hive Kurs", value="%s EUR/Hive" % round(data["hive_price"],3))
        
        embed.set_thumbnail(url=data["pic_url"])
        embed.timestamp=datetime.datetime.utcnow()
        embed.set_footer(text="frisch von der Blockchain & Coingecko")
        await ctx.send(embed=embed) # send the built message

# Get detailed information about a Hive user account 
@client.command(description="Viele Informationen über den einen Hivian",
                brief="LongInfo über Hivians",
                aliases=["Longinfo", "long", "Long"])
async def longinfo(ctx, account_name):
    level = "long"
    data = hive.basic_info(account_name, level)
    
    if data["error"] == 1:
        await ctx.send("Der Account %s existiert nicht" % account_name)
    # building the embed to broadcast via discord
    else:
        embed = discord.Embed(title="Ausführliche Konto Information", description="[%s](%s)"% (account_name.title(), data["hivelink"]), color=0x00ff00)
        embed.add_field(name="Effektive HP", value="%s HP" % data["sp"])
        embed.add_field(name="Votingpower", value="%s Prozent" % data["vp"])
        embed.add_field(name="Eigene HP", value = data["own_sp"])
        embed.add_field(name="Delegierte HP", value = data["delegated_sp"])
        embed.add_field(name="Erhaltene HP", value = data["received_sp"])
        embed.add_field(name="Reputation", value = data["rep"])
        embed.add_field(name="Angemeldet seit", value="%s, %s Tage" % (datetime.datetime.strftime( data["created"],"%d.%m.%Y"), data["since"]))
        embed.add_field(name="Letzte Aktion auf Hive", value=datetime.datetime.strftime( data["latestactivity"], "%d.%m.%Y %H:%M"))
        embed.add_field(name="Aufgeladen auf 100% VP", value=datetime.datetime.strftime( data["recharge_vp"], "%d.%m.%Y %H:%M" ))
        embed.add_field(name="Wert in Euro", value="%s Euro" % data["worth"])    
        embed.add_field(name="Hive Kurs", value="%s EUR/Hive" % round(data["hive_price"],3))

        embed.set_thumbnail(url=data["pic_url"])
        embed.timestamp=datetime.datetime.utcnow()
        embed.set_footer(text="frisch von der Blockchain & Coingecko")
        await ctx.send(embed=embed) # send the built message


# check and display the status of the bot
@client.command(description="Informationen über den Status des Bots",
                brief="Info über den Bot",
                aliases=["Status"])
async def status(ctx):
    level = "short"
    account_name = "dach-support"
    data = hive.basic_info(account_name, level)
    if data["error"] == 1:
        await ctx.send("Der Account %s existiert nicht" % account_name)
    # building the embed to broadcast via discord
    else:
        embed = discord.Embed(title="Bot Status Information", description="[%s](%s)"% (account_name.title(), data["hivelink"]), color=0x00ff00)
        embed.add_field(name="Hive Power", value="%s SP" % data["sp"])
        embed.add_field(name="Votingpower", value="%s Prozent" % data["vp"])
        embed.add_field(name="Aufgeladen auf 100% VP", value=datetime.datetime.strftime( data["recharge_vp"], "%d.%m.%Y %H:%M" ))
        embed.add_field(name="Letzte Aktion auf Hive", value=datetime.datetime.strftime( data["latestactivity"], "%d.%m.%Y %H:%M"))
        
        embed.set_thumbnail(url=data["pic_url"])
        embed.timestamp=datetime.datetime.utcnow()
        embed.set_footer(text="frisch von der Blockchain")
        await ctx.send(embed=embed) # send the built message

@client.command(description="Kursinformationen über Kryptowährungen",
                brief="Kursinfo Kryptos",
                aliases=["Kurs"])
async def kurs(ctx, coin):
    default = "Bitcoin"
    if coin is None:
        coin = default
    #elif coin.upper() == "SBD":
    #    coin = "steem-dollars"

    data = crypto.coin_info(coin)
    if data["error"] == -1:
        await ctx.send("Fehler - %s wurde nicht gefunden" % coin)
    else:
            
        embed = discord.Embed(title="Preis Übersicht :", description=coin, color=0x00ff00)
        embed.add_field(name="Preis USD", value=locale.format_string("%g $",data["priceusd"], grouping=True, monetary=True))
        #embed.add_field(name="Preis EUR", value="%.3f" % float(data["priceeur"]))
        #embed.add_field(name="Preis BTC", value="%s" % data["pricebtc"])
        #embed.add_field(name="Change 1h", value="%s %%" % data["change1h"])
        embed.add_field(name="Change 24h", value="%s %%" % data["usd_24h_change"])
        #embed.add_field(name="Change 7d", value="%s %%" % data["change7d"])
        embed.add_field(name="Volume 24h", value=locale.format_string("%d $", data["usd_24h_vol"], grouping=True, monetary=True))
        
        #embed.add_field(name="Datum", value="%s" % datetime.datetime.strftime(r[3],"%d.%m.%Y"), inline=True)
        #embed.add_field(name="Tage bis zum Meetup", value="%s" % daystomeetup, inline=True)
        #embed.set_thumbnail(url=picurl)
        embed.timestamp=datetime.datetime.utcnow()
        embed.set_footer(text="fresh from the DACH-BOT and CoinGecko")
        await ctx.send(embed=embed)


@client.command(description="Super Gags von und mit Chuck Norris",
                brief="Chuck Gags",
                aliases=["Chuck"])
async def chuck(ctx):

    gag = db.get_chuck()

    await ctx.send("%s" % gag)

# Register a new user with the bot
@client.command(description="Registrierung eines Hive Users beim Bot",
                brief="Registrierung",
                aliases=["Register", "reg"])
async def register(ctx, hive_user):
    discord_ID = ctx.message.author.id
    discord_name = ctx.message.author.name
    print(discord_ID, discord_name)
    user = await client.fetch_user(discord_ID)
    print(user)
    result = db.db_register(discord_ID, discord_name, hive_user)

    if result["error"] == 0:
        await user.send("**Hallo %s!**\n"
                        "Die Registrierung der **Discord ID <@%s>** mit der **Hive ID @%s** wurde eingeleitet!\nDein persönlicher Registrierungs-Token " 
                        "wurde generiert!\nBitte schicke **0.001 HBD** oder **0.001** Hive an die Adresse **@dach-support** mit "
                        "untenstehender Memo um die Registrierung abzuschliessen!\nMemo: `%s`" % (discord_name, discord_ID, hive_user,result["token"]))
    else: 
        await user.send("Sorry der **Discordname** oder der **Hiveaccount** werden bereits in einer "
                        "Registrierung verwendet.\nBitte nimm Kontakt mit <@jedigeiss> auf um die Situation zu klären.")

# Show the user data that is stored in the database of the bot
@client.command(description="Anzeige der Userdaten die beim Bot hinterlegt sind",
                brief="Anzeige der Userdaten",
                aliases=["Showuser", "show"])
async def showuser(ctx, username):

    data = db.get_users(username)
    if data == []:
        await ctx.send("Der Username %s konnte nicht gefunden werden." % username)
    elif len(data) == 1:
        embed = discord.Embed(title="Übersicht User :", description=data[0][1], color=0x00ff00)
        embed.add_field(name="DiscordID", value="%s" % data[0][0])
        embed.add_field(name="Discordname", value="%s" % str(data[0][1]))
        embed.add_field(name="Hivename", value="[%s](%s)" % (str(data[0][2]),"https://peakd.com/@"+str(data[0][2])))
        embed.add_field(name="Status", value="%s" % data[0][4])
        embed.add_field(name="Angemeldet seit", value="%s" % (datetime.datetime.strftime( data[0][5],"%d.%m.%Y")))
        embed.add_field(name="Votes übrig?", value="%s" % (3-int(data[0][6])))
        await ctx.send(embed=embed)
    else:
        user_gesamt = int(data[0]) + int(data[1])
        embed = discord.Embed(title="Userstatistik für den Bot", description="", color=0xff0000)
        embed.add_field(name="Gesamte User", value="%s" % user_gesamt)
        embed.add_field(name="Registriert", value="%s" % data[0])
        embed.add_field(name="Warten auf Hive", value="%s" % data[1])
        await ctx.send(embed=embed)

""" @client.command(description="Manuelles Verifizieren der Registrierungen",
                brief="Manueller Regchecker",
                aliases=["Checkreg"])
async def checkreg(ctx):
    result= ""
    users_to_check = db.get_users_reg()
    guild = client.get_guild(guild_id)

    print(guild)
    if users_to_check == -1:
        await ctx.send("Es sind keine offenen Registrierungen vorhanden")
    else:
        result = hive.check_hive_reg(users_to_check)
        #print(result)
        for user in result:
            print(user)
            if user[2] == "validated":
                await ctx.send("Token Match!\n**DiscordUser: %s** ist jetzt mit **Hiveaccount: %s** registriert" %(user[0], user[1]))
                print(user[0])
                discorduser = guild.get_member_named(str(user[0]))
                print(discorduser)
                # discorduser = await client.fetch_user(user[3])
                await discorduser.send("Deine Registrierung mit dem **D-A-CH Support Bot** ist abgeschlossen!\nDu bist jetzt mit **Hiveaccount: %s registriert**\n"
                                       "Die Rolle *Hive Community Member* wurde dir zugeteilt" % user[1])
                role = get(discorduser.guild.roles, name="registered")
                print(role)
                await discorduser.add_roles(role)
            else:
                await ctx.send("Kein Token Match!\nDiscordUser: %s konnte nicht mit Hiveaccount: %s verifiziert werden" %(user[0], user[1]))
 """

# Function to let a post be upvoted via the bot, the bot will check if the post is eligible and add it to a list or discards it
@client.command(description="Vorschlag eines Artikels zum Voten für den Bot",
                brief="Artikel vorschlagen",
                aliases=["uv", "Upvote"])
@has_role(discord_role_name)
async def upvote(ctx, post_url):
    voter = ctx.message.author.id
    max_comment_age = datetime.timedelta(days=3)
    max_votes = 3
    comment_category = ["hive-121566", "deutsch"]
    comment_tag = "deutsch"
    
    #check how many votes the user already has done
    num_votes = db.get_voter_info(voter)

    pos1 = post_url.find("@")
    if num_votes["votes"] == max_votes:
        await ctx.send("Fehler - Du hast die *maximale Anzahl von %s Votes* verbraucht, **Reset um Mitternacht**" % max_votes)
        
    elif pos1 <= 0:
        await ctx.send("Fehler - Bitte den *kompletten Link* hinter ?upvote einfügen, beginnend mit https://...")
        
    else: 
        
        pos2 = post_url.find("/",pos1)
        hive_name = (post_url[pos1+1:pos2])
        length = len(post_url)
        discord_id = ctx.message.author.id
        discord_name = ctx.message.author.name
        post_url = post_url[pos1:length]
        check_result = hive.check_post(post_url)
        check_db = db.get_article(post_url)
        if check_result["error"] < 0:
            await ctx.send("Fehler - Der Post kann nicht gefunden werden")
        elif check_db["voted"] != "No":
            await ctx.send("Zu spät - Der Artikel wurde schon mit %s Prozent gevoted" % check_db["voted"])
        elif check_result["age"] > max_comment_age:
            await ctx.send("Fehler - Der Post ist *älter als 3 Tage* und kann daher nicht gevoted werden")
        elif check_result["category"] not in comment_category and comment_tag not in check_result["tags"]:
            await ctx.send("Fehler - Der Post wurde nicht in der *D-A-CH Community* gepostet,"
                           " hat ebenfalls kein Tag Deutsch -- kann daher nicht gevoted werden")    
        elif check_result["main_post"] != True:
            await ctx.send("Fehler - *Kommentare* können nicht gevoted werden")
        else:
            if check_db["code"] == 0:
                result = db.insert_article_db(discord_name, post_url, check_result["title"], check_result["author"])
                await ctx.send("**Erfolg!**\n- Post ist vor *weniger als 3 Tagen* geschrieben worden..... **check**\n"
                            "- *D-A-CH Community* oder *Tag Deutsch*..... **check**\n"
                            "- Post ist *kein Kommentar*..... **check**\n"
                            "**Der Post wurde dem Bot zum Voten übergeben**")
                db.increase_votes(discord_name)
                            
            else:
                basepct = 50 + (check_db["votes"] -1) *10
                db.increase_article_votes(post_url)
                await ctx.send("**Erfolg!**\n- Der Post wurde schon eingereicht\n"
                            "- Erhöhe die Anzahl der Votes um 1..... **check**\n"
                            "- Basis-Voting-Prozent werden um *10 Prozent erhöht*, ist jetzt **%s Prozent**..... **check**\n"% (basepct +10))
                db.increase_votes(discord_name)

# Shows the next post that is going to be voted by the bot and the timeline  
@client.command(description="Anzeige des nächsten zu votenden Artikels",
                brief="Nächster Vote des Bots",
                aliases=["Nextvote", "nv"])
async def nextvote(ctx):

    data = db.get_next_vote()
    recharge = hive.get_recharge_time()
    basepct = 50 + (data["votes"] -1) *10
    
    recharge_hours = recharge.seconds // 3600
    recharge_minutes = (recharge.seconds % 3600) // 60

    if data == []:
        await ctx.send("Keine Artikel zum Voten gefunden")
    else:
        embed = discord.Embed(title="Nächster Vote", description="", color=0x228B22)
        embed.add_field(name="Autor", value="[%s](%s)" % (str(data["author"]),"https://peakd.com/@"+str(data["author"])), inline=True)
        embed.add_field(name="Artikel", value="[%s](%s)" % (str(data["title"]),"https://peakd.com/"+str(data["permlink"])), inline=True)
        embed.add_field(name="Votes", value="%s" % int(data["votes"]),inline=True)
        embed.add_field(name="BasisProzentVote", value="%s Prozent" % basepct, inline=True)
        if recharge_hours > 0:
            embed.add_field(name="Vote kommt in :" , value="%s Stunde %s Minuten" % (recharge_hours, recharge_minutes))
        else:
            embed.add_field(name="Vote kommt in :" , value="%s Minuten" % recharge_minutes)
        await ctx.send(embed=embed)

# Shows all posts that are on the list to be voted
@client.command(description="Anzeige aller noch zu votenden Artikel",
                brief="Alle offenen Artikel",
                aliases=["Showarticles", "showart"])
async def showarticles(ctx):
    data = db.get_all_articles()
    
    embed = discord.Embed(title="Liste aller offenen Artikel", description="", color=0x228B22)
    if data[0] == -1:
        embed.add_field(name="Artikel:", value= "%s" % "derzeit keine Artikel zum Voten in der Datenbank")
    else:
        for article in data:
            basepct = 50 + (article[2] -1) *10
            embed.add_field(name="Artikel:", value= "[%s](%s)" % (str(article[4]),"https://peakd.com/"+str(article[1])))
            embed.add_field(name="Autor", value="[%s](%s) " % (str(article[5]),"https://peakd.com/@"+str(article[5])), inline=True)
            #embed.add_field(name="Kurator", value="%s" % r[0], inline=True)
            #embed.add_field(name="Votes", value="%s" % int(article[2]), inline=True)
            embed.add_field(name="BasisProzentVote", value="%s Prozent" % basepct, inline=True)
    embed.timestamp=datetime.datetime.utcnow()
    embed.set_footer(text="frisch vom D-A-CH Bot")
        
    await ctx.send(embed=embed)

# Claim Rewards every 2 hours
@tasks.loop(seconds=7200.0)
async def claim():
    reward = claimreward("dach-support", HIVE_PW)
    print(reward)
    
    
# The function that runs in a loop every 2nd minute and checks for new registrations to the bot
@tasks.loop(seconds=120.0)
async def automated_checkreg():
    result = ""
    users_to_check = db.get_users_reg()
    guild = client.get_guild(guild_id)
    admin = await client.fetch_user(admin_id)
    if users_to_check == -1:
        await admin.send("Es sind keine offenen Registrierungen vorhanden")
    else:
        result = hive.check_hive_reg(users_to_check, block_number_starting)
        for user in result:
            if user[2] == "validated":
                await admin.send("Token Match!\n**DiscordUser: %s** ist jetzt mit **Hiveaccount: %s** registriert" %(user[0], user[1]))
                discorduser = await guild.fetch_member(user[3])
                # discorduser = await client.fetch_user(user[3])
                await discorduser.send("Deine Registrierung mit dem **D-A-CH Support Bot** ist abgeschlossen!\nDu bist jetzt mit **Hiveaccount: %s registriert**\n"
                                       "Die Rolle *%s* wurde dir zugeteilt" % (user[1], "Hive Community Member"))
                role = get(discorduser.guild.roles, name="Hive Community Member")
                await discorduser.add_roles(role)
            else:
                await admin.send("Kein Token Match!\nDiscordUser: %s konnte nicht mit Hiveaccount: %s verifiziert werden" %(user[0], user[1]))

# Shows the last 5 voted posts
@client.command(description="Anzeige der letzten 5 gevoteten Artikel",
                brief="letzte 10 gevotete Artikel",
                aliases=["prevvotes", "previousvotes", "pv"])
async def lastvotes(ctx):
    data = db.get_voted_articles()
    print(data)
    embed = discord.Embed(title="Liste der 5 zuletzt gevoteten Artikel", description="", color=0x228B22)
    if data[0] == -1:
        embed.add_field(name="Artikel:", value= "%s" % "derzeit keine gevoteten Artikel in der Datenbank")
    else:
        for article in data:
            embed.add_field(name="Artikel:", value= "[%s](%s)" % (str(article[4]),"https://peakd.com/"+str(article[1])))
            embed.add_field(name="Autor", value="[%s](%s) " % (str(article[5]),"https://peakd.com/@"+str(article[5])), inline=True)
            #embed.add_field(name="Kurator", value="%s" % r[0], inline=True)
            #embed.add_field(name="Votes", value="%s" % int(article[2]), inline=True)
            embed.add_field(name="Prozent des Votes", value="%s Prozent" % article[3], inline=True)
    embed.timestamp=datetime.datetime.utcnow()
    embed.set_footer(text="frisch vom D-A-CH Bot")
        
    await ctx.send(embed=embed)

# Shows the delegations to the bot 
@client.command(description="Anzeige der Delegationen für den Bot",
                brief="Anzeige der Delegationen",
                aliases=["Delegations", "dl", "DL"])
async def delegations(ctx):
    data = hive.get_delegations()
    embed = discord.Embed(title="Liste aller Delegationen an den Bot", description="", color=0x228B22)
    if data[0] == -1:
        embed.add_field(name="Name & Delegation:", value= "%s" % "derzeit keine aktiven Delegationen gefunden")
    else:
        for row in data:
            #date = datetime.datetime.strptime(row["date"], "%Y-%m-%dT%H:%M:%S")

            embed.add_field(name="Name & Delegation:", value= "[%s](%s) - *%s HP*" % (str(row["delegator"]),"https://peakd.com/@"+str(row["delegator"]),str(row["vests"])),inline=False)
            #embed.add_field(name="Prozent des Votes", value="%s Prozent" % article[3], inline=True)
    embed.timestamp=datetime.datetime.utcnow()
    embed.set_footer(text="frisch vom D-A-CH Bot & der Hive Blockchain")
        
    await ctx.send(embed=embed)

@upvote.error
async def upvote_error(ctx, error):
    if isinstance(error, commands.errors.MissingRole):
        await ctx.send("**Upvote nicht möglich** - Du bist *nicht beim D-A-CH Bot registriert*")
    else:
        raise error

#@register.error
#async def register_error(ctx, error):
#    if isinstance(error, )

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        await ctx.send(error)
        return
    raise error

client.run(TOKEN)
