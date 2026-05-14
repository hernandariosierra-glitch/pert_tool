# scheduler.py
from collections import deque
from model import Project


def successors(tasks, name):
    return [t.name for t in tasks.values() if name in t.predecessors]


def topological_sort(tasks):
    indegree = {name: 0 for name in tasks}
    for task in tasks.values():
        for p in task.predecessors:
            if p in indegree:
                indegree[task.name] += 1
    queue = deque([name for name, deg in indegree.items() if deg == 0])
    order = []
    while queue:
        current = queue.popleft()
        order.append(current)
        for succ in successors(tasks, current):
            indegree[succ] -= 1
            if indegree[succ] == 0:
                queue.append(succ)
    return order


def calculate_schedule(project):
    """Calcula ES, EF, LS, LF y holguras. Devuelve (duracion_total, camino_critico)."""
    tasks = project.tasks
    order = topological_sort(tasks)
    if not order:
        return 0, []

    # Forward pass
    for name in order:
        task = tasks[name]
        task.ES = 0 if not task.predecessors else max(tasks[p].EF for p in task.predecessors)
        task.EF = task.ES + task.duration

    project_duration = max((t.EF for t in tasks.values()), default=0)

    # Backward pass
    for name in reversed(order):
        task = tasks[name]
        succs = successors(tasks, name)
        task.LF = project_duration if not succs else min(tasks[s].LS for s in succs)
        task.LS = task.LF - task.duration
        task.slack = task.LS - task.ES

    critical_path = compute_critical_path(project)
    return project_duration, critical_path


def compute_critical_path(project):
    """
    Devuelve la secuencia de nombres de tareas críticas (slack == 0)
    siguiendo la cadena de precedencias.
    """
    tasks = project.all_tasks()
    critical = {t.name for t in tasks if t.slack == 0}
    if not critical:
        return []

    # Nodos de inicio: críticos sin predecesores críticos
    starts = [
        t for t in tasks
        if t.name in critical and not any(p in critical for p in t.predecessors)
    ]
    if not starts:
        starts = [min((t for t in tasks if t.name in critical), key=lambda t: t.ES)]

    # Seguir la cadena de mayor EF
    path = []
    current = min(starts, key=lambda t: t.ES).name
    visited = set()
    while current and current not in visited:
        path.append(current)
        visited.add(current)
        next_candidates = [
            s for s in successors(project.tasks, current) if s in critical and s not in visited
        ]
        current = min(next_candidates, key=lambda n: project.get_task(n).ES) if next_candidates else None

    return path


def assign_events(project):
    """
    Construye la red AOA (Activity On Arrow):
    - Cada actividad es una flecha entre dos nodos (eventos).
    - El nodo de fin de una actividad ES el nodo de inicio de sus sucesoras directas.
    - Si varias actividades terminan en el mismo instante Y comparten sucesoras,
      comparten el mismo nodo de evento.
    - Si dos actividades tienen el mismo par (predecesor, sucesor) se agrega
      una actividad ficticia para distinguirlas.
    - Las convergencias (varios predecesores) se resuelven con ficticias cuando
      los tiempos de fin difieren.
    """
    tasks = project.tasks
    order = topological_sort(tasks)
    project.fictitious = []

    # ------------------------------------------------------------------ #
    # PASO 1: Crear un nodo de evento para cada "punto de sincronización" #
    # Un punto de sincronización = conjunto de actividades que terminan   #
    # exactamente donde otro conjunto de actividades comienza.            #
    # ------------------------------------------------------------------ #

    # Mapeamos: frozenset(predecesores_directos) -> nombre_evento
    # Si una tarea no tiene predecesores -> viene de "Inicio"
    # Si una tarea no tiene sucesores   -> termina en "Fin"

    # Primero asignamos end_event a cada tarea basado en sus sucesoras.
    # Tareas que tienen exactamente las mismas sucesoras comparten end_event.

    # Calcular qué sucesoras directas tiene cada tarea
    task_successors = {name: successors(tasks, name) for name in tasks}

    # Calcular tiempos
    project_duration = max((t.EF for t in tasks.values()), default=0)
    min_time = min((t.ES for t in tasks.values()), default=0)

    # ------------------------------------------------------------------ #
    # PASO 2: Asignar end_event                                           #
    # Regla: si dos tareas A y B terminan al mismo tiempo Y todas las     #
    # sucesoras de A son también sucesoras de B (y viceversa),            #
    # comparten end_event. Caso contrario, end_event propio.              #
    # ------------------------------------------------------------------ #

    # Agrupar tareas por (EF, frozenset_de_sucesoras)
    # Para tareas sin sucesoras -> grupo "Fin"
    end_event_groups = {}  # key -> event_name
    task_end_key = {}

    event_counter = [1]

    def new_event(time):
        name = f"E{event_counter[0]}"
        event_counter[0] += 1
        return name

    for name in order:
        task = tasks[name]
        succs = frozenset(task_successors[name])
        if not task_successors[name]:
            key = ("FIN",)
        else:
            key = (task.EF, succs)
        task_end_key[name] = key
        if key not in end_event_groups:
            end_event_groups[key] = new_event(task.EF)

    # Asignar end_event
    for name in tasks:
        key = task_end_key[name]
        if key == ("FIN",):
            tasks[name].end_event = "Fin"
        else:
            tasks[name].end_event = end_event_groups[key]

    # ------------------------------------------------------------------ #
    # PASO 3: Asignar start_event                                         #
    # El start_event de una tarea = end_event de su(s) predecesor(es).    #
    # Si no tiene predecesores -> "Inicio"                                #
    # Si tiene UN predecesor   -> end_event del predecesor                #
    # Si tiene VARIOS          -> puede haber divergencia de tiempos      #
    # ------------------------------------------------------------------ #

    for name in order:
        task = tasks[name]
        if not task.predecessors:
            task.start_event = "Inicio"
        elif len(task.predecessors) == 1:
            pred = tasks[task.predecessors[0]]
            task.start_event = pred.end_event
        else:
            # Convergencia: varios predecesores
            pred_tasks = [tasks[p] for p in task.predecessors if p in tasks]
            max_ef = max(p.EF for p in pred_tasks)
            # El start_event será el end_event del predecesor con mayor EF
            # (si hay empate, cualquiera; agregamos ficticias para los demás)
            main_pred = max(pred_tasks, key=lambda p: (p.EF, p.name))
            task.start_event = main_pred.end_event
            # Agregar ficticias desde predecesores con menor EF
            for p in pred_tasks:
                if p.name != main_pred.name:
                    fict = (p.end_event, main_pred.end_event, "F0")
                    if fict not in project.fictitious:
                        project.fictitious.append(fict)

    # ------------------------------------------------------------------ #
    # PASO 4: Detectar y resolver paralelismo (mismo start y end event)   #
    # Si dos tareas comparten start_event Y end_event, una necesita       #
    # un nodo intermedio y una ficticia.                                  #
    # ------------------------------------------------------------------ #
    pair_map = {}
    for name in tasks:
        task = tasks[name]
        key = (task.start_event, task.end_event)
        pair_map.setdefault(key, []).append(name)

    for (start, end), names in pair_map.items():
        if len(names) <= 1:
            continue
        # Dejar la primera sin cambios, las demás añaden nodo intermedio
        for name in names[1:]:
            task = tasks[name]
            mid = f"M_{name}"
            # La tarea pasa por el nodo intermedio
            old_end = task.end_event
            task.end_event = mid
            # Ficticia desde mid hasta el end_event original
            fict = (mid, old_end, "F0")
            if fict not in project.fictitious:
                project.fictitious.append(fict)
            # Actualizar start_event de tareas que usaban old_end como start
            # y cuyo predecesor es esta tarea
            for other_name in tasks:
                if name in tasks[other_name].predecessors:
                    # su start_event ya fue asignado a old_end, no hay que cambiarlo

                    pass

    # ------------------------------------------------------------------ #
    # PASO 5: Construir project.events con tiempos numéricos             #
    # ------------------------------------------------------------------ #
    project.events = {"Inicio": min_time, "Fin": project_duration}

    for name in tasks:
        task = tasks[name]
        se, ee = task.start_event, task.end_event
        project.events.setdefault(se, task.ES)
        project.events.setdefault(ee, task.EF)
        # Para nodos intermedios M_X el tiempo es el EF de la tarea
        if se not in ("Inicio", "Fin"):
            project.events[se] = task.ES
        if ee not in ("Inicio", "Fin"):
            project.events[ee] = task.EF

    # Tiempos de ficticias
    for (frm, to, lab) in project.fictitious:
        # el nodo 'to' ya debería tener tiempo; 'frm' puede ser M_X
        if frm not in project.events:
            # buscar la tarea que termina en frm
            for t in tasks.values():
                if t.end_event == frm:
                    project.events[frm] = t.EF
                    break


def generate_table(project):
    rows = []
    for task in project.all_tasks():
        rows.append({
            "Tarea": task.name,
            "Duración": task.duration,
            "ES": task.ES,
            "EF": task.EF,
            "LS": task.LS,
            "LF": task.LF,
            "Holgura": task.slack,
            "StartEvent": task.start_event,
            "EndEvent": task.end_event
        })
    return rows