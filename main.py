import pywebio
from pywebio.input import input, FLOAT, file_upload, textarea, select, input_group, NUMBER, PASSWORD
from pywebio.output import put_text, put_html, put_markdown, put_table, put_file, scroll_to, put_button, put_buttons, use_scope, clear, toast, put_loading, put_scope
from pywebio.session import set_env
from pywebio.session import info as session_info
from pywebio import session as s
import pymongo
import os
import dns
import time
import judge
import sys
import functools
import uuid
import hashlib
import problem_uploading
import contests
from google.cloud import storage
from functools import cmp_to_key
from pymongo import MongoClient

from flask import Flask
app = Flask(__name__)

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

def hashCode(password):
    salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt

def check_equal(hashed_password, user_password):
    password, salt = hashed_password.split(':')
    return password == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()

def enterPassword():
    with use_scope("scope1"):
        getUserPswd = input("Please enter the administrator password:")
        if check_equal(settings.find_one({"type":"password"})['password'], getUserPswd):
            return True
        toast("The password you entered was incorrect. Please try again.", color = "error")
        return False

def isAdmin(session):
    user = get(session, "username")
    if len(user) == 0:
        return False
    return not settings.find_one({"type":"access", "mode":"admin", "name":user}) is None

def private_problems(session):
    if len(get(session, "username")) == 0:
        toast("Please login to view private problems")
        return
    if get(session, "pp"):
        return
    set(session, "pp", True)
    with use_scope("scope1"):
        with put_loading(shape = 'border', color = 'primary'):
            arr = []
            for x in settings.find({"type":"problem", "published":False}):
                if not judge.perms(settings, x, get(session, "username")):
                    arr.append((x['name'], x['points'], x['contest'], x['types'], x['authors']))
            arr = sorted(arr, key = cmp_to_key(cmpProblem))
            data = [
                ['Problem Name', 'Points/Difficulty', 'Contest', 'Problem Types', 'Authors'],
            ]
            for x in arr:
                data.append([put_button(x[0], outline = True, link_style = True, onclick = functools.partial(problemInterface, session, settings, x[0], get(session, "username"))), x[1], x[2], ", ".join(x[3]), ", ".join(x[4])])
        put_markdown("## Private problems visible to you:")
        put_table(data)
        scroll_to(position = "bottom")

def lang(session):
    if isBusy(session):
        toast("Please complete the current operation before starting another", duration = 5)
        return
    set_env(title = "DBOJ language info")
    with use_scope("scope1"):
        scroll_to(scope = "scope1")
        clear(scope = "scope1")
        clear(scope = "scope1-1")
        data = [["Language", "Compilation", "Execution"]]
        g = settings.find({"type":"lang"})
        for x in g:
            lg = [x['name'], put_markdown(("```" + x['compl'].format(x = 0, path="path") + "```") if len(x['compl']) > 0 else "not a compiled language"), put_markdown("```" + x['run'].format(x = 0, t = 0, mem = 0, path="path") + "```")]
            data.append(lg)
        put_markdown("## Exact compilation and execution commands for all languages")
        put_table(data)

def info(session):
    if isBusy(session):
        toast("Please complete the current operation before starting another", duration = 5)
        return
    set_env(title = "DBOJ Documentation")
    with use_scope("scope1"):
        scroll_to(scope = "scope1")
        clear(scope = "scope1")
        clear(scope = "scope1-1")
        put_markdown(open("problem_setting.md", "r").read())

def check(data):
    for key in data:
        if len(str(data[key])) == 0:
            return (key, "This field cannot be blank")
    
    try:
        name = data['name']
        prev = settings.find_one({"type":"contest", "name":name})
        if not prev is None:
            return ("name", "An existing contest with the name \"" + name + "\" was found. If you would like to edit or delete this contest, please contact me.")
    except:
        pass

def contest(session):
    if isBusy(session):
        toast("Please complete the current operation before starting another", duration = 5)
        return
    set(session, "busy", True)
    set_env(title = "Setting up new contest")
    with use_scope("scope1"):
        scroll_to(scope = "scope1")
        clear(scope = "scope1")
        clear(scope = "scope1-1")

        put_markdown("## Setting up a contest")
        if not isAdmin(session):
            toast("Please login with an admin account")
            set(session, "busy", False)
            login(session)
            if len(get(session, "username")) == 0:
                return
            set(session, "busy", True)

        data = input_group("New Contest Info", [
            input('Enter the contest name:', name='name'),
            input('Enter the contest start time in the format YYYY MM DD HH MM SS (24-hour time):', name='start'),
            input("Enter the contest end time in the format YYYY MM DD HH MM SS (24-hour time):", name="end"),
            input("Enter the number of problems in the contest:", name="problems", type=NUMBER),
            input("How long should the participant window be (in seconds): ", name="len", type=NUMBER),
            select(options = ["Submission penalty", "Time bonus"], label = "What type of tie-breaker should the contest have?", name="breaker"),
            textarea("Paste the contest instructions here (will be shown as a user starts a contest)", name="instructions")
        ], validate = check, cancelable = True)

        if data is None:
            set(session, "busy", False)
            return

        inst = data['instructions']
        with open("instructions.txt", "w") as f:
            f.write(inst)
            f.flush()
            f.close()

        name = data['name']
        
        stc = storage.Client()
        bucket = stc.get_bucket("discord-bot-oj-file-storage")
        blob = bucket.blob("ContestInstructions/" + name + ".txt")
        blob.upload_from_filename("instructions.txt")

        settings.insert_one({"type":"contest", "name":data['name'], "start":data['start'], "end":data['end'], "problems":data['problems'], "len":data['len'], "has-penalty":data['breaker']=='Submission penalty', "has-time-bonus":data['breaker']=='Time bonus'})

        put_markdown("Successfully created contest `" + str(name) + "`! You may now close this page.")
        toast("Success!", color = "success")
    set(session, "busy", False)

def contestProblems(session):
    user = get(session, "username")
    
    for contest in settings.find({"type":"access", "name":user}):
        if contest['mode'] == 'admin' or contest['mode'] == 'owner': continue
        arr = []
        for problem in settings.find({"type":"problem", "contest":contest['mode']}):
            if not judge.perms(settings, problem, get(session, "username")):
                arr.append(problem['name'])
        arr.sort()
        data = [
            ['Problem Name']
        ]
        for x in arr:
            data.append([put_button(x, outline = True, link_style=True, onclick = functools.partial(problemInterface, session, settings, x, get(session, "username")))])
        put_markdown("## Contest problems for `" + contest['mode'] + "`")
        put_table(data)

def view_problems(session):
    if isBusy(session):
        toast("Please complete the current operation before starting another", duration = 5)
        return
    set(session, "busy", True)
    set_env(title = "View all problems")
    set(session, "pp", False)
    with use_scope("scope1"):
        scroll_to(scope = "scope1")
        clear(scope = "scope1")
        clear(scope = "scope1-1")
        contestProblems(session)
        arr = sorted([(x['name'], x['points'], x['types'], x['authors']) for x in settings.find({"type":"problem", "published":True})], key = cmp_to_key(cmpProblem))
        data = [
            ['Problem Name', 'Points/Difficulty', 'Problem Types', 'Authors'],
        ]
        for x in arr:
            data.append([put_button(x[0], outline = True, link_style=True, onclick = functools.partial(problemInterface, session, settings, x[0], get(session, "username"))), x[1], ", ".join(x[2]), ", ".join(x[3])])
        put_markdown("## All published problems on the judge:")
        put_table(data)
        put_button("View private problems", onclick = functools.partial(private_problems, session), outline = True)
    set(session, "busy", False)

def about(session):
    if isBusy(session):
        toast("Please complete the current operation before starting another", duration = 5)
        return
    set_env(title = "About DBOJ")
    with use_scope("scope1"):
        scroll_to(scope = "scope1")
        clear(scope = "scope1")
        clear(scope = "scope1-1")
        put_markdown(open("about.md", "r").read())

def view_problem(session):
    if isBusy(session):
        toast("Please complete the current operation before starting another", duration = 5)
        return
    
    if len(get(session, "username")) == 0: # Test logged in
        toast("Please login to use this command", color = "error", onclick = functools.partial(login, session))
        set(session, "busy", False)
        return
    set_env(title = "View problem")
    set(session, "busy", True)
    
    with use_scope("scope1"):
        scroll_to(scope = "scope1")
        clear(scope = "scope1")
        clear(scope = "scope1-1")
        data = input_group("Enter the problem to open:", [input(name = "problemName")], cancelable = True, validate = lambda d: ('problemName', 'Please enter a problem name') if not d['problemName'] else None)
        if data is None:
            set(session, "busy", False)
            return
        name = data['problemName']
        problemInterface(session, settings, name, get(session, "username"))
        
    set(session, "busy", False)

def problemInterface(session, settings, problem, user):
    if isBusy(session):
        toast("One sec, we're still compiling problems")
        return
    try:
        with use_scope("scope1"):
            clear(scope = "scope1")

            set_env(title = ("View problem " + problem))
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
            put_button("Submit solution", onclick = functools.partial(run_submit, session), outline = True)
            set(session, "problem", problem)

    except Exception as e:
        toast("An error occurred. Please make sure your input is valid. Please reload to try again or contact me.", color = "error")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)

def run_submit(session):
    if len(get(session, "username")) == 0: # Test logged in
        toast("Please login to submit solutions", onclick = functools.partial(login, session))
        set(session, "busy", False)
        return

    if get(session, "submit"):
        return
    set(session, "submit", True)

    problem = get(session, "problem")
    set(session, "busy", True)
    
    op = [x['name'] for x in settings.find({"type":"lang"})]
    data = input_group("Submit to " + problem, [
        select(options = op, label = "Select a language to submit in:", name = "lang"),
        textarea('Paste your code into the editor below:', code=True, rows = 12, name = "code")
    ], cancelable = True, validate = check)

    if data is None:
        set(session, "submit", False)
        set(session, "busy", False)
        return

    lang = data['lang']
    res = data['code']

    with use_scope("scope1-1"):
        scroll_to(scope = "scope1-1")
        put_markdown("**Preparing for grading...**")
        put_loading(shape = "border", color = "primary")
    judge.judgeSubmission(settings, get(session, "username"), problem, lang, res)

    set(session, "busy", False)
    set(session, "submit", False)

def login(session):
    if isBusy(session):
        toast("Please complete the current operation before starting another", duration = 5)
        return
    set(session, "busy", True)
    set_env(title = "Log In")
    with use_scope("scope2"):
        clear(scope = "scope1")
        clear(scope = "scope1-1")
        data = input_group("Please enter your account password to login", [input(type=PASSWORD, name = "pswd")], cancelable = True, validate = lambda d: ('pswd', 'Please enter a password') if not d['pswd'] else None)
        if data is None:
            set(session, "busy", False)
            return
        pswd = data['pswd']
        user = None
        for x in settings.find({"type":"account"}):
            if check_equal(x['pswd'], pswd):
                user = x
                break
        if user is None:
            toast("Could not find an account associated with the given password. Click \"Log In\" to try again.", color = "error", onclick = functools.partial(login, session))
        else:
            set(session, "username", user['name'])
            clear(scope = "scope2")
            put_markdown("**Logged in as `" + get(session, "username") + "`**")
            judge.put_timer(settings, get(session, "username"))
    set(session, "busy", False)

def join(session):
    if isBusy(session):
        toast("Please complete the current operation before starting another", duration = 5)
        return
    set_env(title = "Contests")
    with use_scope("scope1"):
        clear(scope = "scope1")
        clear(scope = "scope1-1")
        scroll_to(scope = "scope1")
        put_markdown("## Joining a contest")
        t = [["Contest name", "Start date", "End date", ""]]
        for x in settings.find({"type":"contest"}):
            t.append([x['name'], x['start'], x['end'], put_buttons(['Rankings', 'Contest Page'], onclick = [functools.partial(rank, x['name']), functools.partial(viewContest, session, x['name'])])])
        put_table(t)

def viewContest(session, name):
    with use_scope("scope1"):
        clear(scope = "scope1")
        clear(scope = "scope1-1")
        put_markdown("## Joining contest `" + name + "`")
        judge.instructions(name)
        put_button("Join contest and start my window countdown!", onclick = functools.partial(joinContest, session, name), outline = True)

def joinContest(session, name):
    if len(get(session, "username")) == 0: # Test logged in
        toast("Please login to join contests", onclick = functools.partial(login, session))
        login(session)
        return
    judge.joinContest(settings, name, get(session, "username"))

def rank(contest):
    try:
        with use_scope("scope1"):
            scroll_to(scope = "scope1")
            clear(scope = "scope1")
            clear(scope = "scope1-1")
            set_env(title = ("Contest rankings for " + contest))
            put_markdown(judge.getScoreboard(settings, contest))
            put_button("Refresh", onclick = functools.partial(rank_specific, contest), outline = True)
    except:
        toast("Internal error with reading scoreboard (might be an archived contest)", duration = 5)

def rank_specific(contest):
    try:
        with use_scope("scope1"):
            scroll_to(scope = "scope1")
            clear(scope = "scope1")
            clear(scope = "scope1-1")
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
    with use_scope("scope1"):
        clear(scope = "scope1")
        clear(scope = "scope1-1")
        scroll_to(scope = "scope1")
        if len(get(session, "username")) > 0:
            put_markdown("## Time remaining for joined contests:\n" + judge.remaining(settings, get(session, "username")))
            put_button("Refresh", onclick = functools.partial(rem, session), outline = True)
        else:
            toast("Please login to use this command", color = "error", onclick = functools.partial(login, session))
            clear(scope = "scope1")
            clear(scope = "scope1-1")

def export(session):
    if isBusy(session):
        toast("Please complete the current operation before starting another", duration = 5)
        return
    set(session, "busy", True)
    set_env(title = "Export/Upload problem data")
    with use_scope("scope1"):
        scroll_to(scope = "scope1")
        clear(scope = "scope1")
        clear(scope = "scope1-1")
        put_markdown("## Export problem data")

        with use_scope("scope1-1"):
            if not isAdmin(session):
                toast("Please login with an admin account")
                set(session, "busy", False)
                login(session)
                if len(get(session, "username")) == 0:
                    return
                set(session, "busy", True)
            
            if len(get(session, "username")) > 0:
                if settings.find_one({"type":"access", "mode":"admin", "name":"jiminycricket#2701"}) is None:
                    toast("Sorry, you do not have sufficient permissions to use this command. Please contact jiminycricket#2701 for problem setting permissions.")
                    set(session, "busy", False)
                    return

                try:
                    f = file_upload("Please upload the zip file with all the problem data. Refer to the documentation for formatting", help_text = "If the progress bar gets stuck at 100%, please reload the page and try again. It should work the second time.", accept=".zip", max_size='128M', cancelable = True)
                    os.system("rm data.zip && rm -r problemdata")
                    open('data.zip', 'wb').write(f['content'])
                except:
                    put_markdown("Error occurred while uploading data file")
                    set(session, "busy", False)
                    return

                put_markdown("Status: **Uploading problem data**")
                with put_loading(shape = 'border', color = 'primary'):
                    try:
                        problem_uploading.uploadProblem(settings, storage.Client(), get(session, "username"))
                    except Exception as e:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                        print(exc_type, fname, exc_tb.tb_lineno)
                        print(e)
                        clear(scope = "scope1-1")
                        put_markdown("Status: **Error occurred**")
                        put_markdown("Error occurred while uploading problem data:\n```\n" + str(e) + "\n```")
            else:
                toast("Please login to use this command", color = "error", onclick = functools.partial(login, session))
                clear(scope = "scope1-1")
    set(session, "busy", False)
    os.system("rm data.zip && rm -r problemdata")
        
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
        scroll_to(scope = "scope1")
        clear(scope = "scope1")
        clear(scope = "scope1-1")
        put_markdown(open("web_oj_documentation.md", "r").read())

@app.route("/home")
def register():
    set_env(title = "Discord Bot Online Judge")
    s.run_js("""$('footer').remove()""")
    with use_scope("top-bar"):
        put_html(open("nav-bar.html").read())
        put_markdown("# Welcome to the Discord Bot Online Judge web interface!")
    try:
        if not "session" in os.environ:
            os.environ['session'] = '1'
        os.environ['session'] = str(int(os.environ['session']) + 1)
        settings.insert_one({"type":"session", "idx":getSession(), "busy":False, "pp":False, "submit":False, "username":""})
        session = getSession()

        print("Starting session", getSession())
        put_markdown("### Problem/contest setting")
        put_buttons(["Upload problem data", "Set up a new contest"], onclick = [functools.partial(export, session), functools.partial(contest, session)], outline = False)
        put_button("Problem/Contest setting documentation", onclick = functools.partial(info, session), link_style = True)
        
        put_markdown("### General info")
        info_names = ["Language Info", "About page"]
        info_fns = [functools.partial(lang, session), functools.partial(about, session)]
        put_buttons(info_names, onclick = info_fns, outline = True)

        put_markdown("### Web online judge")
        login_names = ["Log In", "Creating an account"]
        login_fns = [functools.partial(login, session), functools.partial(account, session)]
        put_buttons(login_names, onclick = login_fns, outline = True)

        oj_names = ["Problems", "Contests"]
        oj_fns = [functools.partial(view_problems, session), functools.partial(join, session)]
        put_buttons(oj_names, onclick = oj_fns, outline = False)

        with use_scope("scope2"):
            clear(scope = "scope1")
            clear(scope = "scope1-1")
            put_markdown("**Not logged in**")
        put_scope("timer")
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
    #pywebio.platform.flask.start_server(register, port=int(os.getenv("PORT")))