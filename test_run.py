# main.py
from parser import load_project_from_file
from scheduler import calculate_schedule, assign_events
from renderer import render_aoa, export_table, export_input_table, export_summary

def main():
    print("=== Herramienta PERT AOA ===")
    filename = input("Ingrese el nombre del archivo de tareas (ej: proyecto1.txt): ").strip()

    try:
        project = load_project_from_file(filename)
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return

    # calcular cronograma
    project_duration, critical_path = calculate_schedule(project)
    # asignar eventos y ficticias
    assign_events(project)

    print("\n--- Resultados ---")
    print(f"Duración total del proyecto: {project_duration}")
    if critical_path:
        print(f"Ruta crítica: {' -> '.join(critical_path)}")
    else:
        print("Ruta crítica: (no se detectó)")

    # generar gráfico y tablas
    try:
        render_aoa(project, filename="pert_output")
    except Exception as e:
        print(f"Error al renderizar el diagrama: {e}")
    try:
        export_table(project, filename="tabla_resultados.csv")
        export_input_table(project, filename="tabla_ejercicio.csv")
        export_summary(project, project_duration, critical_path, filename="resumen.csv")
    except Exception as e:
        print(f"Error al exportar tablas: {e}")

    print("\nSe generó el diagrama PERT en 'pert_output.png' (si graphviz está instalado)")
    print("Se exportaron: 'tabla_resultados.csv', 'tabla_ejercicio.csv', 'resumen.csv'")

if __name__ == "__main__":
    main()
