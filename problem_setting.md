## Setting a problem on the judge

To set a problem on the judge, first ask me (`jiminycricket#2701`) to provide you with problem setting permissions (previous admins should already have the permissions). 

**On the website:** Click the "Upload problem data" button above (under "Problem setting") and upload the zip file problem contents (format described below). Make sure to log in with your personal admin account. *If the upload progress bar gets stuck at 100% with no response, please reload the page and try again. It should work the second time.*

**On the discord bot** (has an 8 MB upload size limit):
Open a direct message channel with the judge bot (`Judge#5642`) or a secure private channel with the judge and upload a zip file with the problem data contents, along with the comment `-export` (HYPHEN export).

**The zip file contents should contain the following files:**
1. A `params.yaml` file containing the following information:
```yaml
name: problemName
authors: [author1, author2, ... , tester1, tester2, ...]
difficulty: numberOfPoints
types: [problemType1, problemType2, ...] # (e.g. "Implementation", "Graph Theory")
time-limit:
	general: [-> General time limit]
	java: [-> Language-specific time limits (optional)]
	python: ... 
	# ... (State time limits in seconds)
memory-limit:
	general: [-> General memory limit]
	java: [-> Language-specific memory limits (optional)]
	# ... (State memory limits in Kilo-Bytes (KB); 1024 KB = 1 MB)
batches: [casesInBatch1, casesInBatch2, ...]
points: [pointsForBatch1, pointsForBatch2, ...]
private: # 1 for true, 0 for false
contest: contestName  # [should only be set if "private" is true]
```

2. A problem statement description contained in the file `description.md`. You may write the statement using Discord message markdown. Bold, italics, code segments, and hyperlinks will be picked up.
3. Testdata: Every test data file will start with `data`, followed by the batch number, followed by a `.`, followed by the case number, followed by either `.in` for an input file or `.out` for an output file. For example, `data3.2.out` is the output file for batch 3 case 2 of the testdata.

Please do **not** zip a folder containing these files; **directly zip the file contents only**.
After you upload the problem data, only you will be able to re-upload and modify the problem contents.

**Sample problem data zip file**: [problem.zip](https://drive.google.com/uc?export=download&id=1HjHx6Z7TUCvAQ6ymqF6n-_3TYIgAgngp)

## Hosting a Contest on the Judge
To host a contest:
1. Make the contest problems (problem names should end with the associated problem number in the contest. For example, problem 3 of a contest could be named xxxp3)

2. Add the contest instructions to the ContestInstructions folder saved to a text file with the name [contestName].txt. The contents of this file will be shown to the user upon joining the contest.

3. Register the contest on the database using the `"c"` command on this web app

4. Use the `-set [contest1] [contest2]...` command to set up live scoreboards.

5. Ask me for permissions to send an announcement in the discord server

## Custom Checkers
To feature custom grading in your problem, add a checker.py python program in the folder with the testdata. This program needs to read the current case input data from the file `data.in` and read the output provided by the user’s program from `data.out` after processing this information, if you deem the output as correct, print `AC` to the standard output stream. Otherwise, if it is incorrect, you don’t need to print anything. If the judge encounters a runtime-error while running the checker program, it will give a `Wrong Answer` verdict for the test case. If you use a custom checker, you do not need to include output files in your test data; just input files is sufficient.

For an example of custom checkers, see problem `ec4p2`.
