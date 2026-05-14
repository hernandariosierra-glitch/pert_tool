# debug.py
from parser import load_project_from_file
from scheduler import calculate_schedule, assign_events, generate_table
from model import Project

fn = "proyecto1.txt"
print("Archivo leído:", fn)
proj = load_project_from_file(fn)

dur, crit = calculate_schedule(proj)
assign_events(proj)

print("\n--- Duración total y camino crítico ---")
print("Duración total:", dur)
print("Camino crítico:", " -> ".join(crit) if crit else "(ninguno)")

print("\n--- Tabla de actividades (calculada) ---")
rows = generate_table(proj)
for r in rows:
    print(f"{r['Tarea']}: Dur={r['Duración']} ES={r['ES']} EF={r['EF']} LS={r['LS']} LF={r['LF']} Holg={r['Holgura']} Start={r['StartEvent']} End={r['EndEvent']}")

print("\n--- Eventos (nombre -> tiempo) ---")
events = getattr(proj, "events", {})
for ev, t in sorted(events.items(), key=lambda x:(x[1], x[0])):
    print(f"{ev} -> T={t}")

print("\n--- Aristas AOA (actividades) ---")
for t in proj.all_tasks():
    print(f"{t.name}: {t.start_event} -> {t.end_event}   label='{t.name} ({t.duration})'   crit={'Sí' if t.slack==0 else 'No'}")

print("\n--- Aristas ficticias registradas ---")
for frm,to,lab in getattr(proj, "fictitious", []):
    print(f"Ficticia: {frm} -> {to}   label='{lab}'")
