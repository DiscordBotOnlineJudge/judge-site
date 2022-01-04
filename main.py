import pywebio
from pywebio.input import input, FLOAT, file_upload, textarea, select
from pywebio.output import put_text, put_html, put_markdown, put_table, put_file, scroll_to, put_button, use_scope, clear
from pywebio.session import set_env
import pymongo
import os
import dns
import time
import judge
import sys
from google.cloud import storage
from functools import cmp_to_key
from pymongo import MongoClient

cluster = MongoClient("mongodb+srv://onlineuser:$" + os.getenv("PASSWORD") + "@discord-bot-online-judg.7gm4i.mongodb.net/database?retryWrites=true&w=majority")
db = cluster['database']
settings = db['settings']

def cmpProblem(a, b):
    if a[0] < b[0]:
        return -1
    elif a[0] > b[0]:
        return 1
    else:
        return a[1] - b[1]

def enterPassword():
    with use_scope("scope1"):
        getUserPswd = input("Please enter the administrator password:")
        if getUserPswd == settings.find_one({"type":"password"})['password']:
            return True
        put_markdown("Sorry, the password you entered was incorrect. Please reload the page to try again.")
        return False

def private_problems():
    global clicked
    if clicked:
        return
    clicked = True

    pswd = input("To view private problems, type in the administrator password:")
    if pswd == settings.find_one({"type":"password"})['password']:
        arr = sorted([(x['name'], x['points'], x['contest'], x['types'], x['authors']) for x in settings.find({"type":"problem", "published":False})], key = cmp_to_key(cmpProblem))
        data = [
            ['Problem Name', 'Points/Difficulty', 'Contest', 'Problem Types', 'Authors'],
        ]
        for x in arr:
            data.append([x[0], x[1], x[2], ", ".join(x[3]), ", ".join(x[4])])
        put_markdown("## All private problems:")
        put_table(data)
        scroll_to(position = "bottom")
    else:
        put_markdown("Sorry, the password you entered was incorrect.")
        scroll_to(position = "bottom")

def lang():
    with use_scope("scope1"):
        clear(scope = "scope1")
        data = [["Language", "Compilation", "Execution"]]
        g = settings.find({"type":"lang"})
        for x in g:
            lg = [x['name']]
            lg.append(x['compl'].format(x = 0, path="path") if len(x['compl']) > 0 else "not a compiled language")
            lg.append(x['run'].format(x = 0, t = 0, path="path"))
            data.append(lg)
        put_markdown("## Exact compilation and execution commands for all languages")
        put_table(data)

def info():
    with use_scope("scope1"):
        clear(scope = "scope1")
        put_markdown(open("problem_setting.md", "r").read())

def contest():
    with use_scope("scope1"):
        clear(scope = "scope1")

        put_markdown("## Setting up a contest")
        if not enterPassword():
            return

        name = input("Enter the contest name:")

        prev = settings.find_one({"type":"contest", "name":name})
        if not prev is None:
            put_text("An existing contest with the name \"" + name + "\" was found. If you would like to edit or delete this contest, please contact me.")
            return

        start = input("Enter the contest start time in the format YYYY MM DD HH MM SS (24-hour time):\n")
        end = input("Enter the contest end time in the format YYYY MM DD HH MM SS (24-hour time):\n")
        problems = int(input("Enter the number of problems in the contest:", type=FLOAT))
        ll = int(input("How long should the participant window be (in seconds): ", type=FLOAT))

        inst = textarea("Paste the contest instructions here (will be shown as a user starts a contest)")
        with open("instructions.txt", "w") as f:
            f.write(inst)
            f.flush()
            f.close()
        
        stc = storage.Client()
        bucket = stc.get_bucket("discord-bot-oj-file-storage")
        blob = bucket.blob("ContestInstructions/" + name + ".txt")
        blob.upload_from_filename("instructions.txt")

        settings.insert_one({"type":"contest", "name":name, "start":start, "end":end, "problems":problems, "len":ll})

        put_text("Successfully created contest `" + str(name) + "`! You may now close this page.")

def view_problems():
    with use_scope("scope1"):
        clear(scope = "scope1")
        arr = sorted([(x['name'], x['points'], x['types'], x['authors']) for x in settings.find({"type":"problem", "published":True})], key = cmp_to_key(cmpProblem))
        data = [
            ['Problem Name', 'Points/Difficulty', 'Problem Types', 'Authors'],
        ]
        for x in arr:
            data.append([x[0], x[1], ", ".join(x[2]), ", ".join(x[3])])
        put_markdown("## All published problems on the judge:")
        put_table(data)

        global clicked
        clicked = False

        put_button("View private problems", onclick = private_problems, outline = True)

def about():
    with use_scope("scope1"):
        clear(scope = "scope1")
        put_markdown(open("about.md", "r").read())

def view_problem():
    with use_scope("scope1"):
        if user is None:
            put_markdown("Please login to use this command")
            return

        clear(scope = "scope1")
        name = input("Enter the problem to open:")
        judge.problemInterface(settings, name, user['name'])

def login():
    with use_scope("scope1"):
        clear(scope = "scope1")
        pswd = input("Please enter your account password to login")
        global user
        user = settings.find_one({"type":"account", "pswd":pswd.strip()})
        if user is None:
            put_text("Could not find an account associated with the given password")
            return
        put_markdown("**Logged in as `" + user['name'] + "`**")

def join():
    with use_scope("scope1"):
        clear(scope = "scope1")

        if user is None:
            put_markdown("Please login to use this command")
            return

        put_markdown("Select the contest to join:")
        op = [x['name'] for x in settings.find({"type":"contest"})]
        name = select(options = op)

        if not judge.joinContest(settings, name, user['name']):
            return
        judge.instructions(name)

def rank():
    with use_scope("scope1"):
        clear(scope = "scope1")
        put_markdown("## View contest rankings:")
        put_markdown("Select the contest to view:")
        op = [x['name'] for x in settings.find({"type":"contest"})]
        contest = select(options = op)
        put_markdown(judge.getScoreboard(settings, contest))

def rem():
    with use_scope("scope1"):
        global user
        if user is None:
            put_markdown("Please login to use this command")
            return
        put_markdown("## Time remaining for joined contests:\n" + judge.remaining(settings, user['name']))

def register():
    set_env(title = "DBOJ Online Console")

    try:
        put_markdown("# Welcome to the Discord Bot Online Judge administrator console!")
        
        put_button("Problem/Contest setting documentation", onclick = info, outline = True)
        put_button("Language Info", onclick = lang, outline = True)
        put_button("View contest rankings", onclick = rank, outline = True)
        put_button("Set up a new contest", onclick = contest, outline = True)
        put_button("View all problems", onclick = view_problems, outline = True)
        put_button("About page", onclick = about, outline = True)

        put_markdown("### Web online judge")
        put_button("Open/submit to a problem", onclick = view_problem, outline = True)
        put_button("Join a contest", onclick = join, outline = True)
        put_button("See remaining time on contest window", onclick = rem, outline = True)

        login()

    except Exception as e:
        put_text("An error occurred. Please make sure your input is valid. Please reload to try again or contact me.")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)

if __name__ == '__main__':
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-service-key.json'
    pywebio.start_server(register, port=int(os.getenv("PORT")))