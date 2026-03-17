from flask import Flask, render_template, request, redirect, url_for, flash
import os
import json
import subprocess
import sys
import threading

app = Flask(__name__)
app.secret_key = "arabmaker_secret"
SETTINGS_FILE = "arab_maker_settings.json"
BOTS_FOLDER = "bots"

if not os.path.exists(BOTS_FOLDER):
    os.mkdir(BOTS_FOLDER)

if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        bot_settings = json.load(f)
else:
    bot_settings = []

running_processes = []

BOT_TYPES = {
    "ترحيب": "1",
    "تذكير": "2",
    "إدارة": "3",
    "تكتات": "4",
    "متاجر": "5",
    "ألعاب": "6"
}

def save_settings():
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(bot_settings, f, ensure_ascii=False, indent=4)

def generate_bot_code(settings):
    bot_name = settings["name"]
    bot_type = settings["type"]
    token = settings["token"]
    code = ""

    if bot_type == "1":
        code = f'''
import discord
from discord.ext import commands
import sys
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
@bot.event
async def on_ready():
    print("بوت {bot_name} جاهز ✅", flush=True)
@bot.event
async def on_member_join(member):
    channel = bot.get_channel({settings["channel_id"]})
    if channel:
        await channel.send("{settings["welcome_msg"]}")
        print("رسالة ترحيب أرسلت ✅", flush=True)
bot.run("{token}")
'''
    elif bot_type == "2":
        code = f'''
import discord
from discord.ext import commands, tasks
import sys
bot = commands.Bot(command_prefix="!")
@bot.event
async def on_ready():
    print("بوت {bot_name} جاهز ✅", flush=True)
    reminder.start()
@tasks.loop(seconds={settings["time"]})
async def reminder():
    channel = bot.get_channel({settings["channel_id"]})
    if channel:
        await channel.send("{settings["reminder_msg"]}")
        print("تم إرسال التذكير ✅", flush=True)
bot.run("{token}")
'''
    elif bot_type == "3":
        code = f'''
import discord
from discord.ext import commands
import sys
bot = commands.Bot(command_prefix="!")
@bot.event
async def on_ready():
    print("بوت {bot_name} جاهز ✅", flush=True)
@bot.command()
async def admin(ctx):
    await ctx.send("{settings["admin_msg"]}")
    print("أرسل رسالة الإدارة ✅", flush=True)
bot.run("{token}")
'''
    elif bot_type == "4":
        code = f'''
import discord
from discord.ext import commands
import sys
bot = commands.Bot(command_prefix="!")
@bot.event
async def on_ready():
    print("بوت {bot_name} جاهز ✅", flush=True)
@bot.command()
async def فتح(ctx):
    guild = ctx.guild
    overwrites = {{guild.default_role: discord.PermissionOverwrite(read_messages=False),
                  ctx.author: discord.PermissionOverwrite(read_messages=True)}}
    channel = await guild.create_text_channel(f'ticket-{{ctx.author.name}}', overwrites=overwrites)
    await channel.send("تم فتح التكت! دعمنا معك قريباً.")
    print("تم فتح التكت ✅", flush=True)
bot.run("{token}")
'''
    elif bot_type == "5":
        code = f'''
import discord
from discord.ext import commands
import sys
bot = commands.Bot(command_prefix="!")
@bot.event
async def on_ready():
    print("بوت {bot_name} جاهز ✅", flush=True)
@bot.command()
async def متجر(ctx):
    await ctx.send("🎉 مرحباً بك في متجرنا! المتجر يعمل بنظام العرض والشراء البسيط.")
    print("تم فتح المتجر ✅", flush=True)
bot.run("{token}")
'''
    elif bot_type == "6":
        code = f'''
import discord
from discord.ext import commands
import random, sys
bot = commands.Bot(command_prefix="!")
@bot.event
async def on_ready():
    print("بوت {bot_name} جاهز ✅", flush=True)
@bot.command()
async def رمي_نرد(ctx):
    num = random.randint(1,6)
    await ctx.send(f"🎲 لقد رميت النرد: {{num}}")
    print(f"تم رمي النرد: {{num}} ✅", flush=True)
bot.run("{token}")
'''
    return code

def run_bot(settings):
    filename = os.path.join(BOTS_FOLDER, f"{settings['name']}.py")
    proc = subprocess.Popen([sys.executable, filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    running_processes.append(proc)
    for line in proc.stdout:
        print(f"[{settings['name']}] {line}", flush=True)

@app.route("/")
def index():
    return render_template("index.html", bots=bot_settings, bot_types=BOT_TYPES)

@app.route("/add_bot", methods=["POST"])
def add_bot_route():
    data = request.form
    settings = {"name": data["name"], "type": data["type"], "token": data["token"]}
    if data["type"] == "1":
        settings["welcome_msg"] = data["welcome_msg"]
        settings["channel_id"] = data["channel_id"]
    elif data["type"] == "2":
        settings["reminder_msg"] = data["reminder_msg"]
        settings["channel_id"] = data["channel_id"]
        settings["time"] = int(data["time"])
    elif data["type"] == "3":
        settings["admin_msg"] = data["admin_msg"]
    elif data["type"] == "4":
        settings["channel_id"] = data["channel_id"]
    bot_settings.append(settings)
    save_settings()
    # توليد ملف البوت
    filename = os.path.join(BOTS_FOLDER, f"{settings['name']}.py")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(generate_bot_code(settings))
    flash(f"تم إضافة البوت {settings['name']} بنجاح!", "success")
    return redirect(url_for("index"))

@app.route("/run_bot/<bot_name>")
def run_bot_route(bot_name):
    bot = next((b for b in bot_settings if b["name"] == bot_name), None)
    if bot:
        threading.Thread(target=run_bot, args=(bot,), daemon=True).start()
        flash(f"تشغيل البوت {bot_name} ✅", "success")
    return redirect(url_for("index"))

@app.route("/run_all")
def run_all_route():
    for bot in bot_settings:
        threading.Thread(target=run_bot, args=(bot,), daemon=True).start()
    flash("تم تشغيل كل البوتات ✅", "success")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
