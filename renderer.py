# renderer.py
import graphviz
import csv
import subprocess
import os
from scheduler import generate_table


def _build_event_times(project):
    """
    Calcula para cada evento su tiempo Early (min ES de salientes)
    y tiempo Late (max LF de entrantes).
    """
    events = project.events
    tasks  = project.all_tasks()

    early = {ev: tm for ev, tm in events.items()}
    late  = {ev: tm for ev, tm in events.items()}

    # Early de un evento = max EF de todas las tareas que llegan a él
    # Late  de un evento = min LS de todas las tareas que salen de él
    for ev in events:
        arrivals   = [t.EF for t in tasks if t.end_event   == ev]
        departures = [t.LS for t in tasks if t.start_event == ev]
        if arrivals:
            early[ev] = max(arrivals)
        if departures:
            late[ev] = min(departures)

    return early, late


def render_aoa(project, filename="pert_output"):
    """
    Diagrama PERT AOA con:
    - Nodos simples: número de evento + tiempo
    - Flechas: nombre de actividad + duración
    - Ruta crítica en rojo
    - Tabla resumen + leyenda renderizada con matplotlib debajo del grafo
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D

    events     = project.events
    tasks      = project.all_tasks()
    critical_path_names = {t.name for t in tasks if t.slack == 0}
    early, late = _build_event_times(project)

    # ------------------------------------------------------------------ #
    # 1) Construir el grafo Graphviz                                      #
    # ------------------------------------------------------------------ #
    dot = graphviz.Digraph(comment="PERT AOA")
    dot.attr(rankdir="LR", splines="true", overlap="false",
             nodesep="1.0", ranksep="1.4", fontname="Helvetica", dpi="150")

    # Agrupar eventos por tiempo para alinear columnas
    time_to_events: dict = {}
    for ev, tm in events.items():
        time_to_events.setdefault(tm, []).append(ev)

    # Numeración limpia de eventos (Inicio=0, Fin=N, resto 1..N-1)
    sorted_evs = sorted(events.keys(), key=lambda e: (events[e], e))
    ev_number  = {}
    num = 0
    for ev in sorted_evs:
        ev_number[ev] = num
        num += 1

    # Nodos
    for tm in sorted(time_to_events):
        with dot.subgraph() as s:
            s.attr(rank="same")
            for ev in sorted(time_to_events[tm]):
                n   = ev_number[ev]
                lbl = f"{n}\nt={tm}"
                is_critical_node = (
                    ev in ("Inicio", "Fin") or
                    any(t.start_event == ev or t.end_event == ev
                        for t in tasks if t.slack == 0)
                )
                if ev in ("Inicio", "Fin"):
                    fill  = "#c8f0c8"
                    color = "#2a7a2a"
                    pw    = "2.5"
                elif is_critical_node:
                    fill  = "#ffffff"
                    color = "#cc0000"
                    pw    = "2.5"
                else:
                    fill  = "#ffffff"
                    color = "#444444"
                    pw    = "1.5"

                s.node(ev, label=lbl, shape="circle",
                       style="filled", fillcolor=fill,
                       color=color, penwidth=pw,
                       fontsize="11", width="0.85", fixedsize="true")

    # Aristas — actividades reales
    for task in tasks:
        start = task.start_event or "Inicio"
        end   = task.end_event   or "Fin"
        is_crit = task.slack == 0
        lbl  = f" {task.name} (d={task.duration})"
        dot.edge(start, end,
                 label=lbl,
                 color    ="#cc0000" if is_crit else "#333333",
                 penwidth ="2.5"     if is_crit else "1.3",
                 fontsize ="10",
                 fontcolor="#cc0000" if is_crit else "#333333",
                 fontname ="Helvetica-Bold" if is_crit else "Helvetica")

    # Aristas — ficticias
    for (frm, to, lab) in project.fictitious:
        for node in (frm, to):
            if node not in events:
                dot.node(node, label=node, shape="circle",
                         style="filled", fillcolor="#fffbe6",
                         fontsize="9", width="0.7")
        dot.edge(frm, to,
                 label     =" F(0)",
                 style     ="dashed",
                 color     ="gray60",
                 penwidth  ="1.0",
                 fontsize  ="8",
                 fontcolor ="gray50",
                 arrowsize ="0.6")

    # Renderizar a PNG temporal
    tmp_graph = "/tmp/pert_graph_only"
    dot.render(tmp_graph, format="png", cleanup=True)

    # ------------------------------------------------------------------ #
    # 2) Tabla resumen con matplotlib                                     #
    # ------------------------------------------------------------------ #
    rows_data = generate_table(project)
    col_labels = ["Act.", "Dur.", "ES", "EF", "LS", "LF", "Holgura", "¿Crítica?"]
    table_rows = []
    row_colors = []
    CRIT_BG  = "#ffe5e5"
    NORM_BG  = "#f9f9f9"
    ALT_BG   = "#ffffff"

    for i, row in enumerate(rows_data):
        is_c = row["Holgura"] == 0
        table_rows.append([
            row["Tarea"],
            row["Duración"],
            row["ES"],
            row["EF"],
            row["LS"],
            row["LF"],
            row["Holgura"],
            "Sí ★" if is_c else "No",
        ])
        bg = CRIT_BG if is_c else (NORM_BG if i % 2 == 0 else ALT_BG)
        row_colors.append([bg] * len(col_labels))

    # ------------------------------------------------------------------ #
    # 3) Combinar grafo + tabla + leyenda en una sola imagen              #
    # ------------------------------------------------------------------ #
    graph_img = mpimg.imread(tmp_graph + ".png")
    gh, gw    = graph_img.shape[:2]

    n_rows    = len(table_rows)
    row_h     = 0.28          # pulgadas por fila
    tbl_h_in  = n_rows * row_h + 0.8   # alto tabla
    leg_h_in  = 1.0                     # alto leyenda

    fig_w_in  = max(gw / 150, 10)
    fig_h_in  = gh / 150 + tbl_h_in + leg_h_in + 0.3

    fig = plt.figure(figsize=(fig_w_in, fig_h_in), facecolor="white")

    # Proporciones de altura: grafo / tabla / leyenda
    graph_frac = (gh / 150) / fig_h_in
    tbl_frac   = tbl_h_in   / fig_h_in
    leg_frac   = leg_h_in   / fig_h_in

    # Panel del grafo
    ax_graph = fig.add_axes([0, 1 - graph_frac, 1, graph_frac])
    ax_graph.imshow(graph_img)
    ax_graph.axis("off")
    ax_graph.set_title("DIAGRAMA PERT — AOA",
                       fontsize=14, fontweight="bold", pad=8)

    # Panel de la tabla
    ax_tbl = fig.add_axes([0.03, leg_frac + 0.02, 0.94, tbl_frac - 0.04])
    ax_tbl.axis("off")
    tbl = ax_tbl.table(
        cellText    =table_rows,
        colLabels   =col_labels,
        cellColours =row_colors,
        loc         ="center",
        cellLoc     ="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1, 1.4)
    # Cabecera en azul oscuro
    for j in range(len(col_labels)):
        tbl[(0, j)].set_facecolor("#1a3a5c")
        tbl[(0, j)].set_text_props(color="white", fontweight="bold")

    ax_tbl.set_title("RESUMEN DE ACTIVIDADES",
                     fontsize=11, fontweight="bold", pad=6)

    # Panel de leyenda
    ax_leg = fig.add_axes([0.03, 0.01, 0.94, leg_frac - 0.02])
    ax_leg.axis("off")

    legend_elements = [
        Patch(facecolor="#c8f0c8", edgecolor="#2a7a2a", linewidth=2,
              label="Inicio / Fin"),
        Patch(facecolor="white",   edgecolor="#cc0000", linewidth=2,
              label="Evento en ruta crítica"),
        Patch(facecolor="white",   edgecolor="#444444", linewidth=1.5,
              label="Evento normal"),
        Line2D([0], [0], color="#cc0000", linewidth=2.5,
               label="Actividad crítica (holgura = 0)"),
        Line2D([0], [0], color="#333333", linewidth=1.3,
               label="Actividad no crítica"),
        Line2D([0], [0], color="gray",    linewidth=1,
               linestyle="--", label="Actividad ficticia (d=0)"),
    ]
    ax_leg.legend(handles=legend_elements, loc="center",
                  ncol=3, fontsize=9, frameon=True,
                  title="LEYENDA", title_fontsize=9,
                  edgecolor="#cccccc")

    plt.savefig(filename + ".png", dpi=150,
                bbox_inches="tight", facecolor="white")
    plt.close(fig)

    # Limpiar tmp
    try:
        os.remove(tmp_graph + ".png")
    except Exception:
        pass

    print(f"Diagrama PERT AOA generado en '{filename}.png'")


def export_table(project, filename="tabla_resultados.csv"):
    rows = generate_table(project)
    fieldnames = ["Actividad", "Duración", "ES", "EF", "LS", "LF",
                  "Holgura", "StartEvent", "EndEvent", "Critica"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "Actividad":  row["Tarea"],
                "Duración":   row["Duración"],
                "ES":         row["ES"],
                "EF":         row["EF"],
                "LS":         row["LS"],
                "LF":         row["LF"],
                "Holgura":    row["Holgura"],
                "StartEvent": row["StartEvent"],
                "EndEvent":   row["EndEvent"],
                "Critica":    "Sí" if row["Holgura"] == 0 else "No",
            })
    print(f"Tabla de resultados exportada en '{filename}'")


def export_input_table(project, filename="tabla_ejercicio.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ID", "Duración", "Predecesores"])
        writer.writeheader()
        for task in project.all_tasks():
            writer.writerow({
                "ID":           task.name,
                "Duración":     task.duration,
                "Predecesores": " ".join(task.predecessors),
            })
    print(f"Tabla del ejercicio exportada en '{filename}'")


def export_summary(project, project_duration, critical_path, filename="resumen.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["DuracionTotal", "CaminoCritico"])
        writer.writeheader()
        writer.writerow({
            "DuracionTotal": project_duration,
            "CaminoCritico": " -> ".join(critical_path) if critical_path else "",
        })
    print(f"Resumen exportado en '{filename}'")