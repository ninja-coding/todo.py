#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import re
import operator
from collections import OrderedDict
from pathlib import Path
from datetime import date, datetime


def check_parameters():
    param_search = re.compile(r"(-.+)")  # Matches -X
    parse_parameters = [re.match(param_search, x) for x in sys.argv]
    param_list = [x.group(1) for x in parse_parameters if x != None]
    return param_list


def get_working_path():
    if '-d' in sys.argv:
        assigned_path = sys.argv[sys.argv.index('-d') + 1]
        return assigned_path
    else:
        default_path = os.getcwd()
        return default_path


def print_help():
    print(
        """
  Usage: todo.py [-d todo_directory] action [task_number] [task_description]

add       -- add TODO ITEM to todo.txt
addm      -- add TODO ITEMs, one per line, to todo.txt
addto     -- add text to file (not item)
append    -- adds to item on line NUMBER the text TEXT
archive   -- moves done items from todo.txt to done.txt
command   -- run internal commands only
del       -- deletes the item on line NUMBER in todo.txt
depri     -- remove prioritization from item
do        -- marks item on line NUMBER as done in todo.txt
help      -- display help
list      -- displays all todo items containing TERM(s), sorted by priority
listall   -- displays items including done ones containing TERM(s)
listcon   -- list all contexts
listfile  -- display all files in .todo directory
listpri   -- displays all items prioritized at PRIORITY
move      -- move item between files
prepend   -- adds to the beginning of the item on line NUMBER text TEXT
pri       -- adds or replace in NUMBER the priority PRIORITY (upper case letter)
remdup    -- remove exact duplicates from todo.txt
replace   -- replace in NUMBER the TEXT
report    -- adds the number of open and done items to report.txt
""")


def print_short_help():
    """
    shorthelp
      List the one-line usage of all built-in and add-on actions.
    """
    print("""
  Actions:
    add|a "THING I NEED TO DO +project @context"
    addto DEST "TEXT TO ADD"
    append|app ITEM# "TEXT TO APPEND"
    archive
    command [ACTIONS]
    deduplicate
    del|rm ITEM# [TERM]
    depri|dp ITEM#[, ITEM#, ITEM#, ...]
    do ITEM#[, ITEM#, ITEM#, ...]
    help [ACTION...]
    list|ls [TERM...]
    listall|lsa [TERM...]
    listaddons
    listcon|lsc [TERM...]
    listfile|lf [SRC [TERM...]]
    listpri|lsp [PRIORITIES] [TERM...]
    listproj|lsprj [TERM...]
    move|mv ITEM# DEST [SRC]
    prepend|prep ITEM# "TEXT TO PREPEND"
    pri|p ITEM# PRIORITY
    replace ITEM# "UPDATED TODO"
    report
    shorthelp
    """)


class Task:
    """
    Represents a task
    """
    def __init__(self, number, content, priority=None,
                 projects=None, contexts=None, done=None):
        self.num = number  # int
        self.content = content  # string
        self.priority = priority  # string
        self.projects = projects  # list
        self.contexts = contexts  # list
        self.done = done
        if not self.priority:
            self.priority = ''

    def deprioritize(self):
        """
        Remove priority
        """
        pr = "({0}) ".format(self.priority)  # The space after ) is not a typo
        self.content = self.content.replace(pr, "", 1)
        self.priority = ''

    def do(self):
        """
        Marks a task as done adding "x yyyy-mm-dd "
        """
        date_command = os.popen("date '+%F'")
        date = str(date_command.read())
        date = date.replace('\n', ' ')
        if self.priority != '':
            self.deprioritize()
            pr = 'x ' + date
            self.content = pr + self.content
        else:
            self.content = 'x ' + date + self.content


class colors:
    """
    Used to print text in colors
    """
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'


def get_file_dir(filename='todo.txt'):
    """
    Returns path of file,
    creates the file if it doesn't exist.
    """
    file_path = os.path.join(PATH, filename)

    # Create todo.txt if it doesn't exist
    if not os.path.exists(file_path):
        with open(str(file_path), 'w') as f:
            f.write("")

    return file_path


def parse_todo_file(file_name):
    """
    Parse a tasks file
    """
    task_list = []
    task_num = 0

    with open(file_name, 'r') as f:
        while True:
            line = f.readline()
            if not line:
                break
            else:
                task_num += 1
                task = parse_task(line, task_num)
            task_list.append(task)
    return task_list


def parse_task(line, number):
    """
    Parse a line containing a task
    """
    # Check for priority (Capital letters)
    pr_pattern = re.compile(r"^\(([A-Z])\)")  # Matches "A"
    priority = re.match(pr_pattern, line)

    # Check if it's a completed task
    comp_pattern = re.compile(r"(x\s\d{4}-\d{2}-\d{2}\s)")  # matches "x yyyy-mm-dd"
    completed = re.findall(comp_pattern, line)

    # Check for projects (+something)
    proj_pattern = re.compile(r".*\s*(\+\w+)\s.*")
    projects = re.findall(proj_pattern, line)  # returns a list

    # Check for contexts (@somewhere)
    con_pattern = re.compile(r".*\s*(\@\w+)\s.*")
    contexts = re.findall(con_pattern, line)

    content = str(line)
    if priority:
        task = Task(number, content, priority.group(1), projects, contexts, completed)
    else:
        task = Task(number, content, priority, projects, contexts, completed)

    return task


def write_tasks(task_list, file='todo.txt', mode='w'):
    """
    Rewrites the todo file with updated tasks
    """
    file_path = get_file_dir(file)
    with open(file_path, mode) as f:
        for task in task_list:
            f.write(task.content)


def print_by_priority(tasks):
    """
    Prints tasks from a list, by priority if they have it,
    and alphabetically if they don't.
    """
    # sort all tasks alphabetically first
    alpha_sorted = sorted(tasks, key=operator.attrgetter('content'))

    # make a list of items with priority and one of items without it
    with_pr = []
    without_pr = []
    for item in alpha_sorted:
        if item.priority == '':
            without_pr.append(item)
        else:
            with_pr.append(item)

    # sort the list of items with priority
    pr_sorted = sorted(with_pr, key=operator.attrgetter('priority'))
    # update the alphabetically sorted list without items with priority
    alpha_sorted = sorted(without_pr, key=operator.attrgetter('content'))

    # Print items with priority first
    for item in pr_sorted:
        # use colors for priorities
        task = "{:02d}".format(item.num) + " " + item.content
        if item.priority == 'A':
            print(colors.YELLOW + colors.BOLD + task + colors.ENDC, end='')
        elif item.priority == 'B':
            print(colors.GREEN + colors.BOLD + task + colors.ENDC, end='')
        elif item.priority == 'C':
            print(colors.BLUE + colors.BOLD + task + colors.ENDC, end='')
        else:
            print(colors.BOLD + task + colors.ENDC, end='')

    # Print items without priority alphabetically sorted
    for item in alpha_sorted:
        print("{:02d}".format(item.num), item.content, end='')


def match_keyword_arguments(tasks, terms):
    """
    Makes a list with the tasks that matched the terms given.
    If a term starts with '-' the tasks containing that term will
    be ignored.
    """
    matching = []
    if len(terms) > 0:
        found = 0
        for task in tasks:
            for x in range(arg+1, len(sys.argv)):
                # Don't print tasks if the term starts with '-'
                term = sys.argv[x]
                if term[0] == '-':
                    if term[1:] in task.content:
                        break
                    else:
                        matching.append(task)
                else:
                    if term in task.content:
                        matching.append(task)
                        break
    return matching


def check_word_arguments(argv, error_msg=None):
    """
    Discard unwanted arguments from a list and return the rest.
    """
    arguments = []
    if len(argv) > arg+1:
        for i in range(arg+1, len(argv)):
            arguments.append(argv[i])
    else:
        if error_msg:
            print(error_msg)
            sys.exit(1)
        else:
            return arguments

    return arguments


def check_int_arguments(argv, error_msg):
    """
    Checks a list of arguments, returns a list of ints.
    """
    arguments = []
    if len(argv) > arg+1:
        for i in range(arg+1, len(argv)):
            try:
                arguments.append(int(argv[i]))
            except ValueError:
                print(error_msg)
                sys.exit(1)
    else:
        print(error_msg)
        sys.exit(1)

    return arguments


# TODO.py functions
def add_task(task=None):
    """
    add "THING I NEED TO DO +project @context"
      a "THING I NEED TO DO +project @context"
      Adds THING I NEED TO DO to your todo.txt file on its own line.
      Project and context notation optional.
      Quotes optional.
    """
    file_path = get_file_dir()
    if not task:
        item = str(sys.argv[arg+1]) + '\n'
    else:
        item = task + '\n'
    with open(file_path, 'a') as f:
        f.write(item)


def add_multiple_tasks():
    """
    addm
      Adds FIRST THING I NEED TO DO to your todo.txt on its own line and
      Adds SECOND THING I NEED TO DO to you todo.txt on its own line.
      Project and context notation optional.
    """
    while True:
        task = str(input("Add: "))
        if task == "":
            sys.exit(0)
        else:
            add_task(task)

def add_to_file():
    """
    addto DEST "TEXT TO ADD"
      Adds a line of text to any file located in the todo.txt directory.
      For example, addto inbox.txt "decide about vacation"
    """
    error_msg = 'usage: todo.py addto DEST "TODO ITEM"'
    arguments = check_word_arguments(sys.argv, error_msg)
    file = get_file_dir(arguments[0])
    if len(arguments) == 2:
        with open(file, 'a') as f:
            f.write(arguments[1])
            f.write("\n")
    else:
        print(error_msg)
        sys.exit(1)

def append_to_task():
    """
    append ITEM# "TEXT TO APPEND"
    app ITEM# "TEXT TO APPEND"
      Adds TEXT TO APPEND to the end of the task on line ITEM#.
      Quotes optional.
    """
    error_msg = 'usage: todo.py addto DEST "TODO ITEM"'
    try:
        item_number = int(sys.argv[arg+1])
    except ValueError:
        print(error_msg)
        sys.exit(1)
    TEXT = sys.argv[arg+2]
    appended = False
    for task in current_tasks:
        if task.num == item_number:
            task.content = task.content.replace('\n', '')
            task.content += " " + TEXT + '\n'
            write_tasks(current_tasks)
            appended = True
            break

    if not appended:
        sys.exit(1)
    else:
        sys.exit(0)


def archive_tasks():
    """
    archive
      Moves all done tasks from todo.txt to done.txt and removes blank lines.
    """
    done_tasks = []
    for task in current_tasks:
        if task.content == '':
            current_tasks.remove(task)
        elif task.done:
            done_tasks.append(task)
            current_tasks.remove(task)
    write_tasks(current_tasks)
    write_tasks(done_tasks, 'done.txt', 'a')


def remove_duplicates():
    """
    deduplicate
      Removes duplicate lines from todo.txt.
    """
    file_path = get_file_dir()

    # Read the todo.txt file, make a list without duplicates
    with open(file_path, 'r') as f:
        lines = (line.rstrip() for line in f)
        unique_lines = OrderedDict.fromkeys((line for line in lines if line))
    deduplicated_list = unique_lines.keys()

    # Count deleted lines
    count_original = len(current_tasks)
    count_deduplicated = len(deduplicated_list)
    total = count_original - count_deduplicated

    # Write the list back to the file
    write_tasks(deduplicated_list)

    if total == 0:
        print("TODO: No duplicate tasks found")
    else:
        print(total, "duplicate task(s) removed")


def remove_task():
    """
    del ITEM# [TERM]
    rm ITEM# [TERM]
      Deletes the task on line ITEM# in todo.txt.
      If TERM specified, deletes only TERM from the task.
    """

    found = False
    try:
        number = int(sys.argv[arg+1])
    except:
        print("usage: todo.py del ITEM# [TERM]")
        sys.exit(1)

    for task in current_tasks:
        if task.num == number:
            content = task.content.replace('\n', '')
            input_prompt = "Delete '" + content + "'?  (y/n)\n"
            confirm = input(input_prompt)
            if confirm == 'y':
                current_tasks.remove(task)
                print(task.num, content)
                print("TODO: " + str(task.num) + " deleted.")
                found = True
                break
            else:
                print("TODO: No tasks were deleted")
                sys.exit(0)

    if not found:
        print("TODO: No task " + str(number))
        sys.exit(1)

    write_tasks(current_tasks)


def remove_priority():
    """
    depri ITEM#[, ITEM#, ITEM#, ...]
    dp ITEM#[, ITEM#, ITEM#, ...]
      Deprioritizes (removes the priority) from the task(s)
      on line ITEM# in todo.txt.
    """
    # Check arguments
    error_msg = "usage: todo.sh depri ITEM#[, ITEM#, ITEM#, ...]"
    arguments = check_int_arguments(sys.argv, error_msg)

    # Remove priorities
    for i in arguments:
        try:
            current_tasks[i-1].deprioritize()
            print(current_tasks[i-1].num, current_tasks[i-1].content, end='')
            print('TODO: {0} deprioritized.'.format(i))
        except IndexError:
            print("TODO: No task {0}.".format(i))
            sys.exit(1)

    write_tasks(current_tasks)


def mark_done():
    """
    do ITEM#[, ITEM#, ITEM#, ...]
      Marks task(s) on line ITEM# as done in todo.txt.
    """
    error_msg = "usage: todo.sh do ITEM#[, ITEM#, ITEM#, ...]"
    arguments = check_int_arguments(sys.argv, error_msg)
    done_tasks = []

    for i in arguments:
        try:
            task = current_tasks[i-1]
            task.do()
            done_tasks.append(task)
            current_tasks.remove(task)
            print(task.num, task.content, end='')
            print('TODO: {0} marked as done.'.format(i))
            print(task.content, end='')
        except IndexError:
            print("TODO: No task {0}.".format(i))
            sys.exit(1)

    write_tasks(current_tasks)
    write_tasks(done_tasks, 'done.txt', 'a')
    file_path = get_file_dir('todo.txt')
    print("TODO: " + file_path + " archived.")


def list_tasks(tasks=None):
    """
    list [TERM...]
    ls [TERM...]
      Displays all tasks that contain TERM(s) sorted by priority with line
      numbers.  Each task must match all TERM(s) (logical AND).
      Hides all tasks that contain TERM(s) preceded by a
      minus sign (i.e. -TERM). If no TERM specified, lists entire todo.txt.
    """
    if not tasks:
        tasks = current_tasks
    n_items = len(tasks)

    # Show items containing terms
    terms = check_word_arguments(sys.argv)
    if len(terms) > 0:
        matching = match_keyword_arguments(tasks, terms)
        print_by_priority(matching)
        print("--")
        print("TODO:", len(matching), "of", n_items, "tasks shown")
    # else print all of them
    else:
        print_by_priority(tasks)
        print("--")
        print("TODO:", n_items, "of", n_items, "tasks shown")


def list_all():
    """
    listall [TERM...]
    lsa [TERM...]
      Displays all the lines in todo.txt AND done.txt that contain TERM(s)
      sorted by priority with line  numbers.  Hides all tasks that
      contain TERM(s) preceded by a minus sign (i.e. -TERM).  If no
      TERM specified, lists entire todo.txt AND done.txt
      concatenated and sorted.

    """
    done = get_file_dir('done.txt')
    tasks = current_tasks
    done_tasks = parse_todo_file(done)
    terms = check_word_arguments(sys.argv)

    if len(terms) > 0:
        matching = match_keyword_arguments(tasks, terms)
        matching_done = match_keyword_arguments(done_tasks, terms)
        print_by_priority(matching)
        print_by_priority(matching_done)
        print("--")
        print("TODO:", len(matching), "of", len(tasks), "tasks shown")
        print("DONE:", len(matching_done), "of", len(done_tasks), "tasks shown")
    else:
        print_by_priority(tasks)
        print_by_priority(done_tasks)
        print("--")
        print("TODO:", len(tasks), "of", len(tasks), "tasks shown")
        print("DONE:", len(done_tasks), "of", len(done_tasks), "tasks shown")


def list_contexts():
    """
    listcon [TERM...]
    lsc [TERM...]
      Lists all the task contexts that start with the @ sign in todo.txt.
      If TERM specified, considers only tasks that contain TERM(s).
    """
    tasks_with_context = []
    contexts = []
    for item in current_tasks:
        if len(item.contexts) > 0:
            tasks_with_context.append(item)

    terms = check_word_arguments(sys.argv)
    if len(terms) > 0:
        matching = match_keyword_arguments(tasks_with_context, terms)
        for task in matching:
            for context in task.contexts:
                contexts.append(context)
    else:
        for task in tasks_with_context:
            for context in task.contexts:
                contexts.append(context)

    contexts = list(set(contexts))  # Remove duplicates
    for context in contexts:
        print(context)


def list_files():
    """
    listfile [SRC [TERM...]]
    lf [SRC [TERM...]]
      Displays all the lines in SRC file located in the todo.txt directory,
      sorted by priority with line  numbers.  If TERM specified, lists
      all lines that contain TERM(s) in SRC file.  Hides all tasks that
      contain TERM(s) preceded by a minus sign (i.e. -TERM).
      Without any arguments, the names of all text files in the todo.txt
      directory are listed.
    """
    dir_path = Path(PATH)
    files_list = list(dir_path.glob('**/*.txt'))  # List all .txt files
    print("Files in the todo.txt directory:")
    for file_name in files_list:
        print(file_name)


def list_priorities():
    """
    listpri [PRIORITIES] [TERM...]
    lsp [PRIORITIES] [TERM...]
      Displays all tasks prioritized PRIORITIES.
      PRIORITIES can be a single one (A) or a range (A-C).
      If no PRIORITIES specified, lists all prioritized tasks.
      If TERM specified, lists only prioritized tasks that contain TERM(s).
      Hides all tasks that contain TERM(s) preceded by a minus sign
      (i.e. -TERM).
    """
    tasks_with_priority = []
    for item in current_tasks:
        if item.priority != '':
            tasks_with_priority.append(item)

    terms = check_word_arguments(sys.argv)
    if len(terms) > 0:
        # Specific priority regex
        specific_pr = re.compile(r"\(([A-Z])\)")  # Matches (X)
        pr_char = specific_pr.match(terms[0])
        if pr_char:
            pr_char = pr_char.group(1)

        # Specific range of priorities regex
        pr_range = re.compile(r"\(([A-Z])-([A-Z])\)")  # Matches (X-X)
        start_char = pr_range.match(terms[0])  # Range start
        if start_char:
            start_char = ord(start_char.group(1))
        end_char = pr_range.match(terms[0])  # Range end
        if end_char:
            end_char = ord(end_char.group(2))

        # Check if user specified a priority
        if pr_char is not None:
            matching = []
            for task in current_tasks:
                if task.priority == pr_char:
                    matching.append(task)
            print_by_priority(matching)
            print("TODO:", len(matching), "of",
                  len(current_tasks), "tasks shown")
        # Check if user specified a priority range
        elif start_char is not None:
            matching = []
            for task in current_tasks:
                for c in range(start_char, end_char + 1):
                    if task.priority == chr(c):
                        matching.append(task)
            print_by_priority(matching)
            print("TODO:", len(matching), "of",
                  len(current_tasks), "tasks shown")
        # else print if they match the terms
        else:
            matching = match_keyword_arguments(tasks_with_priority, terms)
            print_by_priority(matching)
            print("TODO:", len(matching), "of",
                  len(current_tasks), "tasks shown")
    else:
        print_by_priority(tasks_with_priority)
        print("TODO:", len(tasks_with_priority), "of",
              len(current_tasks), "tasks shown")

def list_projects():
    """
    listproj [TERM...]
    lsprj [TERM...]
      Lists all the projects (terms that start with a + sign) in
      todo.txt.
      If TERM specified, considers only tasks that contain TERM(s).
    """
    tasks_with_projects = []
    for item in current_tasks:
        if item.projects != '':
            tasks_with_projects.append(item)

    terms = check_word_arguments(sys.argv)
    if len(terms) > 0:
        matching = match_keyword_arguments(tasks_with_projects, terms)
        print_by_priority(matching)
        print("TODO:", len(matching), "of", len(current_tasks), "tasks shown")
    else:
        print_by_priority(tasks_with_projects)
        print("TODO:", len(tasks_with_projects), "of", len(current_tasks),
              "tasks shown")


def move_task():
    """
    move ITEM# DEST [SRC]
    mv ITEM# DEST [SRC]
      Moves a line from source text file (SRC) to destination text file (DEST).
      Both source and destination file must be located in the directory defined
      in the configuration directory. When SRC is not defined
      it's by default todo.txt.
    """
    error_msg = "TODO: Destination file " + PATH + "does not exist."
    terms = check_word_arguments(sys.argv)
    if len(terms) >= 2:
        # Get argument values
        try:
            number = int(terms[0])
            dest = terms[1]
        except ValueError:
            print(error_msg)
            sys.exit(1)
        # Check for specific source
        if len(terms) == 3:
            src = terms[2]
        else:
            src = None

        if src:
            file_path += src
            if not os.path.exists(file_path):
                print(error_msg)
                sys.exit(1)
            text_file = parse_todo_file(src)
            for line in text_file:
                if line.num == number:
                    text_file.insert(dest-1, text_file.pop(number-1))
                    write_tasks(text_file, src)
        else:
            for task in current_tasks:
                if task.num == number:
                    current_tasks.insert(dest-1, current_tasks.pop(number-1))
                    write_tasks(current_tasks)
                    break

    else:
        sys.exit(1)


def prepend_text():
    """
    prepend ITEM# "TEXT TO PREPEND"
    prep ITEM# "TEXT TO PREPEND"
      Adds TEXT TO PREPEND to the beginning of the task on line ITEM#.
      Quotes optional.
    """
    error_msg = 'usage: todo.py prep ITEM# "TEXT TO PREPEND"'
    try:
        item_number = int(sys.argv[arg+1])
    except ValueError:
        print(error_msg)
        sys.exit(1)
    TEXT = sys.argv[arg+2]
    found = False
    for task in current_tasks:
        if task.num == item_number:
            task.content = task.content.replace('\n', '')
            task.content = TEXT + ' ' + task.content + '\n'
            write_tasks(current_tasks)
            found = True
            break

    if not found:
        print(error_msg)
        sys.exit(1)


def replace_priority():
    """
    pri ITEM# PRIORITY
    p ITEM# PRIORITY
      Adds PRIORITY to task on line ITEM#.  If the task is already
      prioritized, replaces current priority with new PRIORITY.
      PRIORITY must be a letter between A and Z.
    """
    error_msg = 'usage: todo.py pri ITEM# "PRIORITY"'
    # Check if item number input is correct
    try:
        item_number = int(sys.argv[arg+1])
    except ValueError:
        print(error_msg)
        sys.exit(1)
    # Check if priority input is correct
    try:
        priority = sys.argv[arg+2].capitalize()
        if len(priority) > 1:
            print(error_msg)
            sys.exit(1)
        pr_pattern = re.compile(r"([A-Z])")
        priority = re.match(pr_pattern, priority)
        priority = priority.group(1)
    except IndexError:
        print(error_msg)
        sys.exit(1)

    if not priority:
        print(error_msg)
        sys.exit(1)

    # Change item's priority
    for item in current_tasks:
        if item.num == item_number:
            item.priority = priority
            item.content = "(" + priority + ") " + item.content
    write_tasks(current_tasks)


def replace_text():
    """
    replace ITEM# "UPDATED TODO"
      Replaces task on line ITEM# with UPDATED TODO.
    """
    error_msg = 'usage: todo.py replace ITEM# "UPDATED ITEM"'
    arguments = check_word_arguments(sys.argv, error_msg)
    try:
        item_number = int(arguments[0])
    except ValueError:
        print(error_msg)
        sys.exit(1)

    if len(arguments) > 1:
        replacement = arguments[1] + '\n'
    else:
        replacement = input("Replacement: ") + '\n'

    new_task = parse_task(replacement, item_number)
    found = False
    for item in current_tasks:
        if item.num == item_number:
            print(item.num, item.content)
            print("TODO: Replaced task with:")
            print(item.num, new_task.content)
            current_tasks[current_tasks.index(item)] = new_task
            found = True
            break
    if not found:
        print("TODO: No task {0}.".format(item_number))
        sys.exit(1)

    write_tasks(current_tasks)


def make_task_report():
    """
    report
      Adds the number of open tasks and done tasks to report.txt.
    """
    done = len(parse_todo_file('done.txt'))  # Number of tasks completed
    todo = len(current_tasks)  # Number of tasks pending
    now = datetime.now()
    current_time = "{:02d}:{:02d}:{:02d}".format(now.hour,
                                                 now.minute, now.second)
    current_date = date.today()
    report_date = str(current_date) + "T" + str(current_time)
    new_report = "{0} {1} {2}".format(report_date, todo, done) + "\n"
    
    # Check if report exists
    report_path = get_file_dir('report.txt')

    # Make a list of old reports
    with open(report_path, 'r') as f:
        report_file = []
        while True:
            line = f.readline()
            if not line:
                break
            if line != '\n':
                report_file.append(line)

    # Get the last report in the file
    last_report = report_file[-1:]  
    try:
        last_report = last_report[0]
    except IndexError:  # If the file is empty
        last_report = ''

    # Parse last report's number of tasks
    report_regex = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\ (\d+)\ (\d+)')
    last_report_data = re.match(report_regex, last_report)
    try:
        last_report_todo = int(last_report_data.group(1))
        last_report_done = int(last_report_data.group(2))
    except:
        last_report_todo = 0
        last_report_done = 0

    if last_report_todo == todo and last_report_done == done:
        print(last_report, end='')
        print("TODO: Report file is up-to-date")
    else:
        report_file.append(new_report)
        with open(report_path, 'w') as f:
            for report in report_file:
                f.write(report)
        print(new_report, end='')
        print("TODO: Report file updated.")


def main():
    possible_actions = {
        'add': add_task, 'a': add_task,
        'addm': add_multiple_tasks,
        'addto': add_to_file,
        'append': append_to_task, 'app': append_to_task,
        'archive': archive_tasks,
        'deduplicate': remove_duplicates, 'remdup': remove_duplicates,
        'del': remove_task, 'rm': remove_task,
        'depri': remove_priority, 'dp': remove_priority,
        'do': mark_done,
        'help': print_help,
        'list': list_tasks, 'ls': list_tasks,
        'listall': list_all, 'lsa': list_all,
        'listcon': list_contexts, 'lsc': list_contexts,
        'listfile': list_files, 'lf': list_files,
        'listpri': list_priorities, 'lsp': list_priorities,
        'listproj': list_projects, 'lsprj': list_projects,
        'move': move_task, 'mv': move_task,
        'prepend': prepend_text, 'prep': prepend_text,
        'pri': replace_priority, 'p': replace_priority,
        'replace': replace_text,
        'report': make_task_report,
        'shorthelp': print_short_help
    }

    # Check parameters
    parameters = check_parameters()

    # Get the todo.txt path
    global PATH
    PATH = get_working_path()

    # Parse current todos
    global current_tasks
    todo_file = get_file_dir('todo.txt')
    current_tasks = parse_todo_file(todo_file)

    # Do user actions
    global arg  # Number of the action argument
    for arg in range(len(sys.argv)):
        if sys.argv[arg] in possible_actions.keys():
            user_action = possible_actions.get(sys.argv[arg])
            break
        else:
            user_action = None

    if not user_action:
        print_help()
        sys.exit(1)

    user_action()


if __name__ == '__main__':
    main()
