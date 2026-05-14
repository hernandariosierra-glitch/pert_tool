def print_event_table(scheduler):

    print("\n" + "=" * 50)
    print("TABLA DE EVENTOS")
    print("=" * 50)
    print(f"{'Evento':<10}{'TE':<10}{'TL':<10}")
    print("-" * 50)

    for e in sorted(scheduler.events):
        print(
            f"{e:<10}"
            f"{scheduler.events[e]['TE']:<10}"
            f"{scheduler.events[e]['TL']:<10}"
        )


def print_activity_table(scheduler):

    print("\n" + "=" * 70)
    print("TABLA DE ACTIVIDADES")
    print("=" * 70)
    print(f"{'Act':<10}{'Inicio':<10}{'Fin':<10}{'Dur':<10}{'Holgura':<10}")
    print("-" * 70)

    for act in sorted(scheduler.activity_info):
        data = scheduler.activity_info[act]

        print(
            f"{act:<10}"
            f"{data['start']:<10}"
            f"{data['end']:<10}"
            f"{data['duration']:<10}"
            f"{data['slack']:<10}"
        )