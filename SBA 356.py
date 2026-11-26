# colorama and prettytable installed with pip install
from colorama import Fore, Style, init # type: ignore
from prettytable import PrettyTable # type: ignore

init(autoreset=True, strip=True)

# ~~~~~~~~~~~~~~~~~~~~~~~ SBA ~~~~~~~~~~~~~~~~~~~~~~~~

# task
import datetime


class Task:
    # shows a single todo with title, optional due date, and completion status

    def __init__(self, title, due_date=None, completed=False):
        cleaned_title = title.strip()
        if not cleaned_title:
            raise ValueError("the task title cannot be empty.")

        self.title = cleaned_title
        self.completed = bool(completed)

        if isinstance(due_date, datetime.datetime):
            self.due_date = due_date.date()
        elif isinstance(due_date, datetime.date) or due_date is None:
            self.due_date = due_date
        elif isinstance(due_date, str):
            stripped = due_date.strip()
            if not stripped:
                self.due_date = None
            else:
                self.due_date = datetime.date.fromisoformat(stripped)
        else:
            raise TypeError("due_date must be a datetime.date, YYYY-MM-DD string, or None.")

    def mark_completed(self):
        # mark this task as complete
        self.completed = True

    def is_overdue(self, reference_date=None):
        # return true if the task is incomplete and the due date is before today
        if self.completed or self.due_date is None:
            return False
        today = reference_date or datetime.date.today()
        return self.due_date < today

    def __str__(self):
        status = "[X]" if self.completed else "[-]"
        if self.due_date is not None:
            return f"{status} {self.title} (due {self.due_date.isoformat()})"
        return f"{status} {self.title} (no due date)"


# task management
import csv
import datetime
import os

DEFAULT_TASKS_FILE = "tasks.csv"


def parse_due_date(due_date):
    # parse a date object, YYYY-MM-DD string, or none into a datetime.date or none
    if due_date is None or isinstance(due_date, datetime.date):
        return due_date
    if isinstance(due_date, str):
        text = due_date.strip()
        if not text:
            return None
        try:
            return datetime.datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            print(f"invalid date format '{text}'. Expected YYYY-MM-DD; saving without a due date.")
            return None
    print("unsupported due date type; going to save without a due date.")
    return None


def add_task(task_list, title, due_date=None):
    # create a task and append it to task_list
    try:
        parsed_date = parse_due_date(due_date)
        new_task = Task(title=title, due_date=parsed_date, completed=False)
        task_list.append(new_task)
        print(f"added task: {new_task}")
        return new_task
    except ValueError as exc:
        print(f"could not add task: {exc}")
        return None


def _resolve_index(task_list, index):
    # validate a 0-based or 1-based integer index against task_list
    if not isinstance(index, int) or isinstance(index, bool):
        raise IndexError("task index must be an integer.")
    if not task_list:
        raise IndexError("the task list is empty.")
    if index < 0 or index >= len(task_list):
        raise IndexError(f"task index {index} is out of range (0 to {len(task_list) - 1}).")
    return index


def complete_task(task_list, index):
    # mark the task at index as completed
    try:
        idx = _resolve_index(task_list, index)
        task = task_list[idx]
        task.mark_completed()
        print(f"completed task #{idx}: {task}")
        return True
    except IndexError as exc:
        print(f"error completing task: {exc}")
        return False


def delete_task(task_list, index):
    # remove and return the task at index
    try:
        idx = _resolve_index(task_list, index)
        removed = task_list.pop(idx)
        print(f"deleted task #{idx}: {removed}")
        return removed
    except IndexError as exc:
        print(f"error deleting task: {exc}")
        return None


def list_tasks(task_list):
    # print all tasks in a formatted table with color-coded statuses
    if not task_list:
        print(f"\n{Fore.YELLOW}no tasks in your list.")
        return

    today = datetime.date.today()
    table = PrettyTable()
    table.field_names = ["Index", "Status", "Title", "Due Date", "Notes"]
    table.align["Title"] = "l"

    for idx, task in enumerate(task_list):
        due_str = task.due_date.isoformat() if task.due_date else "None"

        if task.completed:
            status_cell = f"{Fore.GREEN}[X] Done{Style.RESET_ALL}"
            title_cell = f"{Fore.GREEN}{task.title}{Style.RESET_ALL}"
            note_cell = ""
        elif task.is_overdue(today):
            status_cell = f"{Fore.RED}[-] Pending{Style.RESET_ALL}"
            title_cell = f"{Fore.RED}{task.title}{Style.RESET_ALL}"
            note_cell = f"{Fore.RED}OVERDUE{Style.RESET_ALL}"
        else:
            status_cell = "[-] Pending"
            title_cell = task.title
            note_cell = ""

        table.add_row([idx, status_cell, title_cell, due_str, note_cell])

    print("\n=== current tasks ===")
    print(table)


def save_tasks(task_list, filepath=DEFAULT_TASKS_FILE):
    # save tasks to a csv file (title,due_date,completed)
    try:
        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["title", "due_date", "completed"])
            for task in task_list:
                due_str = task.due_date.isoformat() if task.due_date else ""
                writer.writerow([task.title, due_str, str(task.completed)])
        print(f"Tasks saved to '{filepath}'.")
        return True
    except OSError as exc:
        print(f"File error while saving to '{filepath}': {exc}")
        return False


def load_tasks(filepath=DEFAULT_TASKS_FILE):
    # load task objects from filepath if it exists if not return empty list
    if not os.path.exists(filepath):
        print(f"no existing task file '{filepath}' found. starting with an empty list.")
        return []

    loaded_tasks = []
    try:
        with open(filepath, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row_num, row in enumerate(reader, start=2):
                try:
                    title = (row.get("title") or "").strip()
                    if not title:
                        continue
                    raw_due = (row.get("due_date") or "").strip()
                    due_date = (
                        datetime.date.fromisoformat(raw_due) if raw_due else None
                    )
                    completed = (row.get("completed") or "").strip().lower() == "true"
                    loaded_tasks.append(
                        Task(title=title, due_date=due_date, completed=completed)
                    )
                except ValueError as exc:
                    print(f"skipping malformed row {row_num} in '{filepath}': {exc}")
        print(f"loaded {len(loaded_tasks)} task(s) from '{filepath}'.")
    except OSError as exc:
        print(f"file error while reading '{filepath}': {exc}")
    return loaded_tasks


# menu
def prompt_index(prompt_message):
    # read a non-negative integer index from user input
    raw = input(prompt_message).strip()
    try:
        value = int(raw)
        if value < 0:
            print("index must be 0 or greater.")
            return None
        return value
    except ValueError:
        print("invalid input. please enter a whole number.")
        return None


def main():
    tasks = load_tasks(DEFAULT_TASKS_FILE)

    while True:
        print("\n--- personal to-do list manager ---")
        print("(A) Add a new task")
        print("(C) Mark a task as completed")
        print("(D) Delete a task")
        print("(L) List all tasks")
        print("(Q) Quit")
        choice = input("select an option: ").strip().upper()

        if choice == "A":
            title = input("enter task title: ").strip()
            due_input = input("enter due date (YYYY-MM-DD, or leave blank): ").strip()
            add_task(tasks, title, due_input if due_input else None)
        elif choice == "C":
            list_tasks(tasks)
            idx = prompt_index("enter task index to mark completed: ")
            if idx is not None:
                complete_task(tasks, idx)
        elif choice == "D":
            list_tasks(tasks)
            idx = prompt_index("enter task index to delete: ")
            if idx is not None:
                delete_task(tasks, idx)
        elif choice == "L":
            list_tasks(tasks)
        elif choice == "Q":
            save_choice = input("save tasks before quitting? (y/n): ").strip().lower()
            if save_choice in ("y", "yes"):
                save_tasks(tasks, DEFAULT_TASKS_FILE)
            print("goodbye.")
            break
        else:
            print("unknown option. choose A, C, D, L, or Q.")


if __name__ == "__main__":
    main()
