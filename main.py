import pywebio
from pywebio.input import input, FLOAT, file_upload, textarea, select
from pywebio.output import put_text, put_html, put_markdown, put_table, put_file, scroll_to, put_button, use_scope, clear, toast, popup
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
    if get("pp"):
        return
    set("busy", True)
    set("pp", True)

    with use_scope("scope1"):
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
            toast("Sorry, the password you entered was incorrect", color = "error")
    set("busy", False)
    set("pp", False)

def lang():
    if isBusy():
        toast("Please complete the current operation before starting another")
        return
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
    if isBusy():
        toast("Please complete the current operation before starting another")
        return
    with use_scope("scope1"):
        clear(scope = "scope1")
        put_markdown(open("problem_setting.md", "r").read())

def contest():
    if isBusy():
        toast("Please complete the current operation before starting another")
        return
    set("busy", True)
    with use_scope("scope1"):
        clear(scope = "scope1")

        put_markdown("## Setting up a contest")
        if not enterPassword():
            set("busy", False)
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
    set("busy", False)

def view_problems():
    if isBusy():
        toast("Please complete the current operation before starting another")
        return
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

        put_button("View private problems", onclick = private_problems, outline = True)

def about():
    if isBusy():
        toast("Please complete the current operation before starting another")
        return
    with use_scope("scope1"):
        clear(scope = "scope1")
        put_markdown(open("about.md", "r").read())

def view_problem():
    if isBusy():
        toast("Please complete the current operation before starting another")
        return

    
    if len(get("username")) == 0: # Test logged in
        toast("Please login to use this command", color = "error")
        set("busy", False)
        clear(scope = "scope1")
        return

    set("busy", True)
    with use_scope("scope1"):
        clear(scope = "scope1")
        name = input("Enter the problem to open:")
        problemInterface(settings, name, get("username"))
        
    set("busy", False)

def problemInterface(settings, problem, user):
    try:
        sc = storage.Client()
        bucket = sc.get_bucket("discord-bot-oj-file-storage")
        file = bucket.blob("ProblemStatements/" + problem + ".txt")

        found = settings.find_one({"type":"problem", "name":problem})
        if found is None:
            toast("Error: Problem not found", color = "error")
            return
        if judge.perms(settings, found, user):
            toast("Error: Problem not found", color = "error")
            return
        
        try:
            file.download_to_filename("problem.txt")
            put_markdown("### Problem statement for problem `" + problem + "`")
            put_markdown(open("problem.txt").read())
        except:
            put_markdown("Sorry, this problem does not yet have a problem statement.")

        set("problem", problem)
        put_button("Submit solution", onclick = run_submit, outline = True)

    except Exception as e:
        toast("An error occurred. Please make sure your input is valid. Please reload to try again or contact me.", color = "error")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)

def run_submit():
    if get("submit"):
        return
    set("submit", True)

    problem = get("problem")
    set("busy", True)
    
    op = [x['name'] for x in settings.find({"type":"lang"})]
    lang = select(options = op, label = "Select a language to submit in:")

    res = textarea('Paste your code into the editor below:', code=True)
    judge.judgeSubmission(settings, get("username"), problem, lang, res)

    set("busy", False)
    set("submit", False)

def login():
    with use_scope("scope2"):
        clear(scope = "scope1")
        put_markdown("**Not logged in**")
        done = False
        while not done:
            pswd = input("Please enter your account password to login")
            user = settings.find_one({"type":"account", "pswd":pswd.strip()})
            if user is None:
                toast("Could not find an account associated with the given password", color = "error")
            else:
                set("username", user['name'])
                clear(scope = "scope2")
                put_markdown("**Logged in as `" + get("username") + "`**")
                done = True  

def join():
    if isBusy():
        toast("Please complete the current operation before starting another")
        return

    if len(get("username")) == 0: # Test logged in
        toast("Please login to use this command", color = "error")
        set("busy", False)
        clear(scope = "scope1")
        return

    set("busy", True)
    with use_scope("scope1"):
        clear(scope = "scope1")

        put_markdown("## Joining a contest")
        op = [x['name'] for x in settings.find({"type":"contest"})]
        name = select(options = op, label = "Select a contest to join:")

        try:
            if not judge.joinContest(settings, name, get("username")):
                set("busy", False)
                return
            judge.instructions(name)
        except:
            toast("Please login to use this command", color = "error")
            set("busy", False)
            clear(scope = "scope1")
    set("busy", False)

def rank():
    if isBusy():
        toast("Please complete the current operation before starting another")
        return
    set("busy", True)
    try:
        with use_scope("scope1"):
            clear(scope = "scope1")
            put_markdown("## View contest rankings:")
            op = [x['name'] for x in settings.find({"type":"contest"})]
            contest = select(options = op, label = "Select a contest to view:")
            put_markdown(judge.getScoreboard(settings, contest))
    except:
        print("Error reading scoreboard")
    set("busy", False)

def rem():
    if isBusy():
        toast("Please complete the current operation before starting another")
        return
    with use_scope("scope1"):
        clear(scope = "scope1")
        if len(get("username")) > 0:
            put_markdown("## Time remaining for joined contests:\n" + judge.remaining(settings, get("username")))
        else:
            toast("Please login to use this command", color = "error")
            clear(scope = "scope1")

def getSession() -> int:
    return int(os.environ['session'])

def isBusy():
    return settings.find_one({"type":"session", "idx":getSession()})['busy']

def set(key, val):
    settings.update_one({"type":"session", "idx":getSession()}, {"$set":{key:val}})

def get(key):
    return settings.find_one({"type":"session", "idx":getSession()})[key]

def account():
    if isBusy():
        toast("Please complete the current operation before starting another")
        return
    with use_scope("scope1"):
        clear(scope = "scope1")
        put_markdown(open("web_oj_documentation.md", "r").read())

def register():
    set_env(title = "Discord Bot Online Judge")

    try:
        put_markdown("# Welcome to the Discord Bot Online Judge web interface!")

        if not "session" in os.environ:
            os.environ['session'] = '1'
        os.environ['session'] = str(int(os.environ['session']) + 1)
        settings.insert_one({"type":"session", "idx":getSession(), "busy":False, "pp":False, "submit":False, "username":""})

        print("Starting session", getSession())

        put_button("Problem/Contest setting documentation", onclick = info, outline = True)
        put_button("Language Info", onclick = lang, outline = True)
        put_button("View contest rankings", onclick = rank, outline = True)
        put_button("Set up a new contest", onclick = contest, outline = True)
        put_button("View all problems", onclick = view_problems, outline = True)
        put_button("About page", onclick = about, outline = True)

        put_markdown("### Web online judge")
        put_button("Creating an account", onclick = account, outline = True)
        put_button("Open/submit to a problem", onclick = view_problem, outline = True)
        put_button("Join a contest", onclick = join, outline = True)
        put_button("See remaining time on contest window", onclick = rem, outline = True)

        login()

    except Exception as e:
        toast("An error occurred. Please make sure your input is valid. Please reload to try again or contact me.", color = "error")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)

if __name__ == '__main__':
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-service-key.json'
    settings.delete_many({"type":"session"})
    pywebio.start_server(register, port=int(os.getenv("PORT")))