from pywebio.input import input, FLOAT, file_upload, textarea
from pywebio.output import put_text, put_html, put_markdown, put_table, put_file, scroll_to, use_scope, clear, popup, toast, put_loading
from google.cloud import storage
import contests
import sys
import os
import grpc
import judge_pb2_grpc
import judge_pb2
import time
from functools import cmp_to_key
from multiprocessing import Process, Manager

setting = None

def instructions(contest):
    stc = storage.Client()
    bucket = stc.get_bucket("discord-bot-oj-file-storage")
    try:
        blob = bucket.blob("ContestInstructions/" + contest + ".txt")
        blob.download_to_filename("instructions.txt")
        put_text(open("instructions.txt").read())
    except Exception as e:
        put_markdown("This contest does not yet have an instructions file.")

        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)

def amt(len):
    h = len // 3600
    len %= 3600
    m = len // 60
    len %= 60
    s = len

    return "{hh} hours, {mm} minutes, and {ss} seconds".format(hh = h, mm = m, ss = s)

def cmp(a, b):
    if a[1] != b[1]:
        return b[1] - a[1]
    return a[2] - b[2]

def cmpProblem(a, b):
    return a[0] - b[0]

def remaining(settings, name):
    acc = settings.find({"type":"access", "name":name})
    msg = ""
    for x in acc:
        if x['mode'] != "admin" and x['mode'] != "owner":
            try:
                total = getLen(settings, x['mode'])
                elapsed = contests.compare(x['start'], contests.current_time())
                rem = total - elapsed
                if rem <= 0:
                    msg += "Time's up! `" + name + "`'s participation in contest `" + x['mode'] + "` has ended.\n"
                else:
                    msg += "`" + name + "` still has `" + amt(rem) + "` left on contest `" + x['mode'] + "`\n"
            except:
                pass
    if len(msg) == 0:
        return "`" + name + "` has not joined any contests"
    return msg
    

def getScoreboard(settings, contest):
    ct = settings.find_one({"type":"contest", "name":contest})
    if ct is None:
        return "Error: Contest not found"

    time_bonus = ct['has-time-bonus']
    penalty = ct['has-penalty']

    fnd = settings.find({"type":"access", "mode":contest})
    arr = [x for x in fnd]

    msg = "## Current rankings for participants in contest `" + contest + "`\n```\n"
    cnt = 0

    namWid = 0
    pWid = [0] * (ct['problems'] + 1)
    comp = []

    for x in arr:
        namWid = max(namWid, len(x['name']))
        for y in range(1, len(x['solved'])):
            dt = "P" + str(y) + "-" + str(x['solved'][y])

            if time_bonus and x['time-bonus'][y] > 0:
                dt += "(+" + str(x['time-bonus'][y]) + ")"
            if penalty and x['penalty'][y] > 0:
                dt += "(" + str(x['penalty'][y]) + ")"
            pWid[y] = max(pWid[y], len(dt))
    for x in arr:
        m = x['name'].ljust(namWid) + " : "
        total = 0
        for y in range(1, len(x['solved'])):
            dt = "P" + str(y) + "-" + str(x['solved'][y])

            if time_bonus and x['time-bonus'][y] > 0:
                dt += "(+" + str(x['time-bonus'][y]) + ")"
            if penalty and x['penalty'][y] > 0:
                dt += "(" + str(x['penalty'][y]) + ")"
                
            m += dt.ljust(pWid[y]) + " "
            total += x['solved'][y] + x['time-bonus'][y]
        m += "total: " + str(total)
        comp.append((m, total, sum(x['penalty'])))
    
    comp.sort(key = cmp_to_key(cmp))
    idx = 0
    cur = 0
    for i in range(len(comp)):
        cur += 1
        if i == 0 or comp[i - 1][1] != comp[i][1] or comp[i - 1][2] != comp[i][2]:
            idx = cur
        msg += str(idx) + ") " + comp[i][0] + "\n"

    if len(comp) <= 0:
        msg += "---No participants are in this contest yet---\n"
        
    return msg + "```"

def put_timer(settings, user):
    with use_scope("timer"):
        clear(scope = "timer")
        script = None
        for x in settings.find({"type":"access", "name":user}):
            if x['mode'] != "owner" and x['mode'] != "admin":
                len = getLen(settings, x['mode'])
                s = x['start'].split()
                session = settings.find_one({"type":"timerCount"})['cnt']
                settings.update_one({"type":"timerCount"}, {"$inc":{"cnt":1}})
                script = open("countdown.html").read().replace("%year%", s[0]).replace("%month%", s[1]).replace("%day%", s[2]).replace("%hh%", s[3]).replace("%mm%", s[4]).replace("%ss%", s[5]).replace("%len%", str(len)).replace("%name%", x['mode']).replace("%session%", str(session))
        if not script is None: put_html(script)

def joinContest(settings, contest, user):
    cont = settings.find_one({"type":"contest", "name":contest})
    if (not contests.date(cont['start'], cont['end'], contests.current_time())):
        toast("This contest is not currently active.")
        return False
    if not settings.find_one({"type":"access", "mode":contest, "name":user}) is None:
        toast("You already joined this contest.")
        return False

    solved = [0] * (cont['problems'] + 1)
    penalties = [0] * (cont['problems'] + 1)
    time_bonus = [0] * (cont['problems'] + 1)

    start = contests.current_time()
    settings.insert_one({"type":"access", "mode":contest, "name":user, "solved":solved, "penalty":penalties, "time-bonus":time_bonus, "start":start, "taken":0})
    with use_scope("scope1"):
        put_markdown("Successfully joined contest `" + contest + "` as user `" + user + "`! You have " + amt(cont['len']) + " to complete the contest. Good Luck!\n")
        toast("Successfully started contest countdown!", color = "success")
    put_timer(settings, user)
    return True

def perms(settings, found, author):
    acc = settings.find_one({"type":"access", "mode":found['contest'], "name":author})
    if (not settings.find_one({"type":"access", "mode":"owner", "name":author}) is None):
        return False # Has owner perms
    if (not settings.find_one({"type":"access", "mode":"admin", "name":author}) is None) and (author in found['authors']):
        return False # Has admin perms
    elif (not acc is None) and (found['status'] == "s") and contests.compare(acc['start'], contests.current_time()) <= getLen(settings, found['contest']):
        return False # Has contest participant perms
    return (not found['published']) or (found['status'] != "s")

def getLen(settings, contest):
    return settings.find_one({"type":"contest", "name":contest})['len']

def get_bonus(rem, pts):
    return (pts * rem) // 30000

def updateScore(settings, contest, problem, user, score, ct):
    post = settings.find_one({"type":"access", "name":user, "mode":contest})
    if post is None:
        print("Failed to update score (no access post)")
        return
    elapsed = contests.compare(post['start'], ct)
    contest_len = getLen(settings, contest)
    if elapsed > contest_len:
        print("Invalid score update")
        return
    arr = post['solved']
    penalty = post['penalty']
    time_bonus = post['time-bonus']

    num = int(problem[len(problem) - 1])

    if score <= arr[num] and arr[num] < 100:
        penalty[num] += 1
    if arr[num] < 100:
        settings.update_one({"_id":post['_id']}, {"$set":{"taken":elapsed}})

    arr[num] = max(arr[num], score)
    time_bonus[num] = max(time_bonus[num], get_bonus(contest_len - elapsed, score))

    settings.update_one({"_id":post['_id']}, {"$set":{"solved":arr, "penalty":penalty, "time-bonus":time_bonus}})

def runSubmission(judges, username, cleaned, lang, problm, attachments, return_dict, sub_id):
    with grpc.insecure_channel(judges['ip'] + ":" + str(judges['port'])) as channel:
        stub = judge_pb2_grpc.JudgeServiceStub(channel)
        response = stub.judge(judge_pb2.SubmissionRequest(username = username, source = cleaned, lang = lang, problem = problm['name'], attachment = attachments, sub_id=sub_id))
        finalscore = response.finalScore
        return_dict['finalscore'] = finalscore

def judgeSubmission(settings, username, problem, lang, cleaned):
    try:
        ct = contests.current_time()

        problm = settings.find_one({"type":"problem", "name":problem})
        judges = settings.find_one({"type":"judge", "status":0})

        if judges is None:
            toast("All of the judge's grading servers are currently offline or in use. Please resubmit in a few seconds.", color = "error")
            return

        settings.update_one({"_id":judges['_id']}, {"$set":{"status":1}})

        avail = judges['num']

        sub_cnt = settings.find_one({"type":"sub_cnt"})['cnt']
        settings.update_one({"type":"sub_cnt"}, {"$inc":{"cnt":1}})

        settings.insert_one({"type":"use", "author":username, "message":cleaned})
        settings.insert_one({"type":"submission", "author":username, "message":cleaned, "id":sub_cnt, "output":""})

        sub = settings.find_one({"type":"submission", "id":sub_cnt})

        global setting
        setting = settings

        finalscore = -1

        manager = Manager()
        return_dict = manager.dict()
        rpc = Process(target = runSubmission, args = (judges, username, cleaned, lang, problm, False, return_dict, sub_cnt,))
        rpc.start()

        msgContent = "```\nWaiting for response from Judge " + str(avail) + "\n```"
        with use_scope("scope1"):
            with use_scope("scope1-1"):
                clear(scope = "scope1-1")
                put_markdown("**Submission grading in progress. See execution results below:**")
                with put_loading(shape = "border", color = "success"):
                    with use_scope('submission1'):
                        scroll_to(scope = "submission1")
                        put_markdown(msgContent)

                        while rpc.is_alive():
                            newcontent = settings.find_one({"_id":sub['_id']})['output'].replace("diff", "").replace("`", "").replace("+ ", "  ").replace("- ", "  ")
                            if newcontent != msgContent and len(newcontent) > 0:
                                msgContent = newcontent
                                try:
                                    clear(scope = "submission1")
                                    put_markdown("```diff\n" + msgContent + "\n```")
                                    scroll_to(position = "bottom")
                                except:
                                    print("Edited empty message")
                            time.sleep(1)

                    finalscore = return_dict['finalscore']
                    
                    output = settings.find_one({"_id":sub['_id']})['output'].replace("diff", "").replace("`", "").replace("+ ", "  ").replace("- ", "  ")
                    clear(scope = "scope1-1")
                    put_markdown("**Grading complete. See execution results below:**", scope = "scope1-1")
                    put_markdown("```diff\n" + output + "\n```", scope = "scope1-1")
                    scroll_to(position = "bottom")

        if len(problm['contest']) > 0 and finalscore >= 0:
            updateScore(settings, problm['contest'], problem, username, finalscore, ct)
        
        settings.update_one({"_id":judges['_id']}, {"$set":{"output":""}})
    except Exception as e:
        toast("Judging error: Fatal error occured while grading solution", color = "error")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)

    settings.update_one({"_id":judges['_id']}, {"$set":{"status":0}})