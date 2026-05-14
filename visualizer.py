import matplotlib.pyplot as plt
import networkx as nx


class Visualizer:

    @staticmethod
    def draw_aoa(scheduler):

        G = nx.DiGraph()

        # -------------------------------------------------
        # 1️⃣ NODOS = EVENTOS
        # -------------------------------------------------

        for event in scheduler.events:
            G.add_node(event)

        # -------------------------------------------------
        # 2️⃣ ARISTAS = ACTIVIDADES
        # -------------------------------------------------

        for act in scheduler.activities:

            u = act["start"]
            v = act["end"]
            duration = act["duration"]
            name = act["name"]

            is_dummy = act.get("dummy", False)
            slack = act.get("TF", 0)
            is_critical = act.get("critical", False)

            # Label correcto
            if is_dummy:
                label = f"{name} (0)"
            else:
                label = f"{name} ({duration}) H={slack}"

            G.add_edge(
                u,
                v,
                label=label,
                critical=is_critical,
                dummy=is_dummy
            )

        # -------------------------------------------------
        # 3️⃣ LAYOUT AOA PROFESIONAL
        # Basado en tiempo temprano (early)
        # -------------------------------------------------

        pos = {}

        # Agrupar eventos por tiempo temprano
        levels = {}
        for event in scheduler.events:
            te = scheduler.early[event]
            levels.setdefault(te, []).append(event)

        # Asignar coordenadas
        for te in sorted(levels):
            for i, node in enumerate(sorted(levels[te])):
                x = te * 2
                y = -i * 2
                pos[node] = (x, y)

        # -------------------------------------------------
        # 4️⃣ DIBUJO
        # -------------------------------------------------

        plt.figure(figsize=(14, 8))

        # Nodos (eventos)
        nx.draw_networkx_nodes(
            G,
            pos,
            node_color="white",
            edgecolors="black",
            node_size=1500
        )

        nx.draw_networkx_labels(
            G,
            pos,
            font_size=10,
            font_weight="bold"
        )

        # Separar aristas
        critical_edges = []
        normal_edges = []
        dummy_edges = []

        for u, v in G.edges():
            if G[u][v]["dummy"]:
                dummy_edges.append((u, v))
            elif G[u][v]["critical"]:
                critical_edges.append((u, v))
            else:
                normal_edges.append((u, v))

        # Aristas normales
        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=normal_edges,
            width=1.5
        )

        # Aristas críticas (ROJO GRUESO)
        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=critical_edges,
            width=3,
            edge_color="red"
        )

        # Aristas ficticias (PUNTEADAS)
        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=dummy_edges,
            style="dashed",
            edge_color="gray"
        )

        # Labels de actividades
        edge_labels = nx.get_edge_attributes(G, "label")

        nx.draw_networkx_edge_labels(
            G,
            pos,
            edge_labels=edge_labels,
            font_size=9
        )

        plt.title("Diagrama PERT - AOA Correcto")
        plt.axis("off")
        plt.tight_layout()
        plt.show()