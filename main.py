import pywebio
from pywebio.input import input, FLOAT, file_upload
from pywebio.output import put_text, put_html, put_markdown, put_table, put_file, scroll_to
import pymongo
import os
import dns
import time
import judge
import sys
from functools import cmp_to_key
from pymongo import MongoClient

cluster = MongoClient("mongodb+srv://onlineuser:$" + os.getenv("PASSWORD") + "@discord-bot-online-judg.7gm4i.mongodb.net/database?retryWrites=true&w=majority")
db = cluster['database']
settings = db['settings']

def cmpProblem(a, b):
    return a[0] - b[0]

def enterPassword():
    getUserPswd = input("Please enter the administrator password:")
    if getUserPswd == settings.find_one({"type":"password"})['password']:
        return True
    put_markdown("Sorry, the password you entered was incorrect. Please reload the page to try again.")
    return False

def register():
    try:
        put_markdown("# Welcome to the Discord Bot Online Judge administrator console!")
        put_table([
            ['Command', 'Function'],
            ['info', 'Problem and contest setting instructions and template'],
            ['lang', 'View exact executions for all languages'],
            ['rank', 'View the rankings of a contest'],
            ['c', 'Register a new contest or edit an existing contest'],
            ['s', 'View all problems on the judge'],
            ['a', 'See the about page']
        ])
        op = input("Please type in a command from the command list above:")
        
        if op.lower() == 'lang':
            data = [["Language", "Compilation", "Execution"]]
            g = settings.find({"type":"lang"})
            for x in g:
                lg = [x['name']]
                lg.append(x['compl'].format(x = 0, path="path") if len(x['compl']) > 0 else "not a compiled language")
                lg.append(x['run'].format(x = 0, t = 0, path="path"))
                data.append(lg)
            put_markdown("## Exact compilation and execution commands for all languages")
            put_table(data)
        elif op.lower() == 'info':
            put_markdown(open("problem_setting.md", "r").read())
        elif op.lower() == 'c':
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

            settings.insert_one({"type":"contest", "name":name, "start":start, "end":end, "problems":problems, "len":ll})

            put_text("Successfully created contest " + str(name) + "! You may now close this page.")
        elif op.lower() == 's':
            arr = sorted([(x['points'], x['name']) for x in settings.find({"type":"problem", "published":True})], key = cmp_to_key(cmpProblem))
            data = [
                ['Problem Name', 'Points/Difficulty'],
            ]
            for x in arr:
                data.append([x[1], x[0]])
            put_markdown("## All published problems on the judge:")
            put_table(data)

            pswd = input("To view private problems, type in the administrator password:")
            if pswd == settings.find_one({"type":"password"})['password']:
                arr = sorted([(x['points'], x['name'], x['contest']) for x in settings.find({"type":"problem", "published":False})], key = cmp_to_key(cmpProblem))
                data = [
                    ['Problem Name', 'Points/Difficulty', 'Contest'],
                ]
                for x in arr:
                    data.append([x[1], x[0], x[2]])
                put_markdown("## All private problems:")
                put_table(data)
                scroll_to(position = "bottom")
            else:
                put_markdown("Sorry, the password you entered was incorrect.")
                scroll_to(position = "bottom")
        elif op.lower() == 'u':
            f = file_upload("Upload a file")
            open('asset/'+f['filename'], 'wb').write(f['content'])  
        elif op.lower() == 'a':
            put_markdown(open("about.md", "r").read())
        elif op.lower().startswith("join"):
            arr = op.split(" ")
            if len(arr) < 2:
                put_text("Use join followed by the contest name")
                return
            pswd = input("Enter your account password:")
            user = settings.find_one({"type":"account", "pswd":pswd.strip()})
            if user is None:
                put_text("Could not find an account associated with the given password")
                return
            put_markdown("**Logged in as `" + user['name'] + "`**")
            if not judge.joinContest(settings, arr[1], user['name']):
                return
            judge.instructions(arr[1])
        elif op.lower().startswith("open"):
            arr = op.split(" ")
            if len(arr) < 2:
                put_text("Use open followed by the problem name")
                return
            pswd = input("Enter your account password:")
            user = settings.find_one({"type":"account", "pswd":pswd.strip()})
            if user is None:
                put_text("Could not find an account associated with the given password")
                return
            put_markdown("**Logged in as `" + user['name'] + "`**")
            judge.problemInterface(settings, arr[1], user['name'])
        elif op.lower() == "rank":
            contest = input("Enter the contest name:")
            put_markdown(judge.getScoreboard(settings, contest))
        elif op.lower() == "rem":
            pswd = input("Enter your account password:")
            user = settings.find_one({"type":"account", "pswd":pswd.strip()})
            if user is None:
                put_text("Could not find an account associated with the given password")
                return
            put_markdown("**Logged in as `" + user['name'] + "`**")
            put_markdown("## Time remaining for joined contests:\n" + judge.remaining(settings, user['name']))
        else:
            put_text("Invalid option. Please reload the page and try again.")

    except Exception as e:
        put_text("An error occurred. Please make sure your input is valid. Please reload to try again or contact me.")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)

if __name__ == '__main__':
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-service-key.json'
    pywebio.start_server(register, port=55)