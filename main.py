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

    # 1) calcular cronograma
    project_duration, critical_path = calculate_schedule(project)

    # 2) asignar eventos AOA  ← debe ir ANTES de cualquier exportación
    assign_events(project)

    print("\n--- Resultados ---")
    print(f"Duración total del proyecto: {project_duration}")
    print(f"Ruta crítica: {' -> '.join(critical_path) if critical_path else '(no detectada)'}")

    # 3) generar gráfico y tablas
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

    print("\nArchivos generados:")
    print("  pert_output.png  (diagrama PERT)")
    print("  tabla_resultados.csv")
    print("  tabla_ejercicio.csv")
    print("  resumen.csv")

if __name__ == "__main__":
    main()