# parser.py
from model import Task, Project

def parse_predecessors(field):
    if not field:
        return []
    field = field.strip()
    if not field:
        return []
    for sep in [",", ";"]:
        if sep in field:
            return [p.strip() for p in field.split(sep) if p.strip()]
    return [p.strip() for p in field.split() if p.strip()]

def load_project_from_file(filename):
    """
    Lee archivo con líneas:
    Nombre,Duración,Predecesores
    Predecesores pueden separarse por espacios, comas o ;
    """
    project = Project()
    with open(filename, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 2:
                continue
            name = parts[0]
            duration = parts[1] if parts[1] != "" else "0"
            preds_field = parts[2] if len(parts) > 2 else ""
            predecessors = parse_predecessors(preds_field)
            task = Task(name, duration, predecessors)
            project.add_task(task)
    return project
