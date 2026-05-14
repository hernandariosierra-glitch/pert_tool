def parse_file(filename):
    tasks = {}

    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = [p.strip() for p in line.split(',')]

            name = parts[0]
            duration = int(parts[1])

            deps = []

            if len(parts) > 2:
                raw_deps = ",".join(parts[2:])

                for sep in ['|', ';']:
                    raw_deps = raw_deps.replace(sep, ',')

                deps = [d.strip() for d in raw_deps.split(',') if d.strip()]

            if not deps:
                deps = ['-']

            tasks[name] = (duration, deps)

    return tasks