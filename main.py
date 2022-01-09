import pywebio
from pywebio.input import input, FLOAT, file_upload, textarea, select, input_group, NUMBER
from pywebio.output import put_text, put_html, put_markdown, put_table, put_file, scroll_to, put_button, use_scope, clear, toast, popup
from pywebio.session import set_env
import pymongo
import os
import dns
import time
import judge
import sys
import functools
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
        toast("The password you entered was incorrect. Please try again.", color = "error")
        return False

def isAdmin(session):
    user = get(session, "username")
    if len(user) == 0:
        return False
    return not settings.find_one({"type":"access", "mode":"admin", "name":user}) is None

def private_problems(session):
    if get(session, "pp"):
        return
    set(session, "pp", True)
    with use_scope("scope1"):
        put_markdown("Compiling private problems...")
        arr = []
        for x in settings.find({"type":"problem", "published":False}):
            if not judge.perms(settings, x, get(session, "username")):
                arr.append((x['name'], x['points'], x['contest'], x['types'], x['authors']))
        arr = sorted(arr, key = cmp_to_key(cmpProblem))
        data = [
            ['Problem Name', 'Points/Difficulty', 'Contest', 'Problem Types', 'Authors'],
        ]
        for x in arr:
            data.append([x[0], x[1], x[2], ", ".join(x[3]), ", ".join(x[4])])
        put_markdown("## Private problems visible to you:")
        put_table(data)
        scroll_to(position = "bottom")

def lang(session):
    if isBusy(session):
        toast("Please complete the current operation before starting another", duration = 5)
        return
    set_env(title = "DBOJ language info")
    scroll_to(scope = "scope1")
    with use_scope("scope1"):
        clear(scope = "scope1")
        data = [["Language", "Compilation", "Execution"]]
        g = settings.find({"type":"lang"})
        for x in g:
            lg = [x['name'], put_markdown(("```" + x['compl'].format(x = 0, path="path") + "```") if len(x['compl']) > 0 else "not a compiled language"), put_markdown("```" + x['run'].format(x = 0, t = 0, path="path") + "```")]
            data.append(lg)
        put_markdown("## Exact compilation and execution commands for all languages")
        put_table(data)

def info(session):
    if isBusy(session):
        toast("Please complete the current operation before starting another", duration = 5)
        return
    set_env(title = "DBOJ Documentation")
    scroll_to(scope = "scope1")
    with use_scope("scope1"):
        clear(scope = "scope1")
        put_markdown(open("problem_setting.md", "r").read())

def checkDate(date):
    pass

def check(data):
    for key in data:
        if len(data[key]) == 0:
            return (key, "This field cannot be blank")
    
    name = data['name']
    prev = settings.find_one({"type":"contest", "name":name})
    if not prev is None:
        return ("name", "An existing contest with the name \"" + name + "\" was found. If you would like to edit or delete this contest, please contact me.")

def contest(session):
    if isBusy(session):
        toast("Please complete the current operation before starting another", duration = 5)
        return
    set(session, "busy", True)
    set_env(title = "Setting up new contest")
    scroll_to(scope = "scope1")
    with use_scope("scope1"):
        clear(scope = "scope1")

        put_markdown("## Setting up a contest")
        if not isAdmin(session):
            toast("Please log in with an admin account to set up contests", duration = 5, onclick = functools.partial(login, session))
            set(session, "busy", False)
            return

        data = input_group("New Contest Info", [
            input('Enter the contest name:', name='name'),
            input('Enter the contest start time in the format YYYY MM DD HH MM SS (24-hour time):', name='start'),
            input("Enter the contest end time in the format YYYY MM DD HH MM SS (24-hour time):", name="end"),
            input("Enter the number of problems in the contest:", name="problems", type=NUMBER),
            input("How long should the participant window be (in seconds): ", name="len", type=NUMBER),
            textarea("Paste the contest instructions here (will be shown as a user starts a contest)", name="instructions")
        ], validate = check)

        inst = data['instructions']
        with open("instructions.txt", "w") as f:
            f.write(inst)
            f.flush()
            f.close()

        data['type'] = 'contest'
        name = data['name']
        
        stc = storage.Client()
        bucket = stc.get_bucket("discord-bot-oj-file-storage")
        blob = bucket.blob("ContestInstructions/" + name + ".txt")
        blob.upload_from_filename("instructions.txt")

        settings.insert_one(data)

        put_markdown("Successfully created contest `" + str(name) + "`! You may now close this page.")
        toast("Success!", color = "success")
    set(session, "busy", False)

def view_problems(session):
    if isBusy(session):
        toast("Please complete the current operation before starting another", duration = 5)
        return
    set_env(title = "View all problems")
    scroll_to(scope = "scope1")
    set(session, "pp", False)
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

        put_button("View private problems", onclick = functools.partial(private_problems, session), outline = True)

def about(session):
    if isBusy(session):
        toast("Please complete the current operation before starting another", duration = 5)
        return
    set_env(title = "About DBOJ")
    scroll_to(scope = "scope1")
    with use_scope("scope1"):
        clear(scope = "scope1")
        put_markdown(open("about.md", "r").read())

def view_problem(session):
    if isBusy(session):
        toast("Please complete the current operation before starting another", duration = 5)
        return
    
    if len(get(session, "username")) == 0: # Test logged in
        toast("Please login to use this command", color = "error", onclick = functools.partial(login, session))
        set(session, "busy", False)
        clear(scope = "scope1")
        return
    set_env(title = "View problem")
    scroll_to(scope = "scope1")
    set(session, "busy", True)
    with use_scope("scope1"):
        clear(scope = "scope1")
        name = input("Enter the problem to open:")
        set_env(title = ("View problem " + name))
        problemInterface(session, settings, name, get(session, "username"))
        
    set(session, "busy", False)

def problemInterface(session, settings, problem, user):
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
        
        put_markdown("### Problem statement for problem `" + problem + "`")
        put_button("Submit solution", onclick = functools.partial(run_submit, session), outline = True)
        try:
            file.download_to_filename("problem.txt")
            put_markdown(open("problem.txt").read())
        except:
            put_markdown("Sorry, this problem does not yet have a problem statement.")

        set(session, "problem", problem)

    except Exception as e:
        toast("An error occurred. Please make sure your input is valid. Please reload to try again or contact me.", color = "error")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)

def run_submit(session):
    if get(session, "submit"):
        return
    set(session, "submit", True)

    problem = get(session, "problem")
    set(session, "busy", True)
    
    op = [x['name'] for x in settings.find({"type":"lang"})]
    lang = select(options = op, label = "Select a language to submit in:")

    res = textarea('Paste your code into the editor below:', code=True)
    judge.judgeSubmission(settings, get(session, "username"), problem, lang, res)

    set(session, "busy", False)
    set(session, "submit", False)

def login(session):
    if isBusy(session):
        toast("Please complete the current operation before starting another", duration = 5)
        return
    set(session, "busy", True)
    set_env(title = "Log In")
    scroll_to(scope = "scope1")
    with use_scope("scope2"):
        clear(scope = "scope1")
        pswd = input("Please enter your account password to login")
        user = settings.find_one({"type":"account", "pswd":pswd.strip()})
        if user is None:
            toast("Could not find an account associated with the given password. Click \"Log In\" to try again.", color = "error", onclick = functools.partial(login, session))
        else:
            set(session, "username", user['name'])
            clear(scope = "scope2")
            put_markdown("**Logged in as `" + get(session, "username") + "`**")
    set(session, "busy", False)

def join(session):
    if isBusy(session):
        toast("Please complete the current operation before starting another", duration = 5)
        return

    if len(get(session, "username")) == 0: # Test logged in
        toast("Please login to use this command", color = "error", onclick = functools.partial(login, session))
        set(session, "busy", False)
        clear(scope = "scope1")
        return
    set_env(title = "Joining a contest")
    set(session, "busy", True)
    scroll_to(scope = "scope1")
    with use_scope("scope1"):
        clear(scope = "scope1")

        put_markdown("## Joining a contest")
        op = [x['name'] for x in settings.find({"type":"contest"})]
        name = select(options = op, label = "Select a contest to join:")

        if len(name) == 0:
            toast("No contest was selected")
            return

        if not judge.joinContest(settings, name, get(session, "username")):
            set(session, "busy", False)
            return
    set(session, "busy", False)

def rank(session):
    if isBusy(session):
        toast("Please complete the current operation before starting another", duration = 5)
        return
    set_env(title = "Contest rankings")
    set(session, "busy", True)
    scroll_to(scope = "scope1")
    try:
        with use_scope("scope1"):
            clear(scope = "scope1")
            put_markdown("## View contest rankings:")
            op = [x['name'] for x in settings.find({"type":"contest"})]
            contest = select(options = op, label = "Select a contest to view:")
            set_env(title = ("Contest rankings for " + contest))
            put_markdown(judge.getScoreboard(settings, contest))
            put_button("Refresh", onclick = functools.partial(rank_specific, contest), outline = True)
    except:
        toast("Internal error with reading scoreboard (might be an archived contest)", duration = 5)
    set(session, "busy", False)

def rank_specific(contest):
    with use_scope("scope1"):
        scroll_to(scope = "scope1")
        clear(scope = "scope1")
        try:
            with use_scope("scope1"):
                clear(scope = "scope1")
                put_markdown("## View contest rankings:")
                set_env(title = ("Contest rankings for " + contest))
                put_markdown(judge.getScoreboard(settings, contest))
                put_button("Refresh", onclick = functools.partial(rank_specific, contest), outline = True)
        except:
            toast("Internal error with reading scoreboard (might be an archived contest)", duration = 5)

def rem(session):
    if isBusy(session):
        toast("Please complete the current operation before starting another", duration = 5)
        return
    set_env(title = "Remaining contest window time")
    scroll_to(scope = "scope1")
    with use_scope("scope1"):
        clear(scope = "scope1")
        if len(get(session, "username")) > 0:
            put_markdown("## Time remaining for joined contests:\n" + judge.remaining(settings, get(session, "username")))
            put_button("Refresh", onclick = functools.partial(rem, session), outline = True)
        else:
            toast("Please login to use this command", color = "error", onclick = functools.partial(login, session))
            clear(scope = "scope1")
        
def getSession() -> int:
    return int(os.environ['session'])

def isBusy(session):
    return settings.find_one({"type":"session", "idx":session})['busy']

def set(session, key, val):
    settings.update_one({"type":"session", "idx":session}, {"$set":{key:val}})

def get(session, key):
    return settings.find_one({"type":"session", "idx":session})[key]

def account(session):
    if isBusy(session):
        toast("Please complete the current operation before starting another", duration = 5)
        return
    set_env(title = "Creating an account")
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
        session = getSession()

        print("Starting session", getSession())

        put_button("Problem/Contest setting documentation", onclick = functools.partial(info, session), outline = True)
        put_button("Language Info", onclick = functools.partial(lang, session), outline = True)
        put_button("View contest rankings", onclick = functools.partial(rank, session), outline = True)
        put_button("Set up a new contest", onclick = functools.partial(contest, session), outline = True)
        put_button("View all problems", onclick = functools.partial(view_problems, session), outline = True)
        put_button("About page", onclick = functools.partial(about, session), outline = True)

        put_markdown("### Web online judge")
        put_button("Creating an account", onclick = functools.partial(account, session), outline = True)
        put_button("Log In", onclick = functools.partial(login, session), outline = True)
        put_button("Open/submit to a problem", onclick = functools.partial(view_problem, session), outline = True)
        put_button("Join a contest", onclick = functools.partial(join, session), outline = True)
        put_button("See remaining time on contest window", onclick = functools.partial(rem, session), outline = True)

        with use_scope("scope2"):
            clear(scope = "scope1")
            put_markdown("**Not logged in**")

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