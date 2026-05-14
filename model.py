# model.py
class Task:
    def __init__(self, name, duration, predecessors=None):
        self.name = name
        self.duration = int(duration)
        self.predecessors = predecessors if predecessors else []
        # AOA events
        self.start_event = None
        self.end_event = None
        # scheduling times
        self.ES = 0
        self.EF = 0
        self.LS = 0
        self.LF = 0
        self.slack = 0

    def __repr__(self):
        return f"Task({self.name}, dur={self.duration}, pred={self.predecessors})"


class Project:
    def __init__(self):
        self.tasks = {}            # name -> Task
        self.fictitious = []       # list of (from_event, to_event, label)
        self.events = {}           # event_name -> time (numeric)

    def add_task(self, task):
        self.tasks[task.name] = task

    def get_task(self, name):
        return self.tasks.get(name)

    def all_tasks(self):
        return list(self.tasks.values())
