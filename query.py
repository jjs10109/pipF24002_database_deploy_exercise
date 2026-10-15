"""Run read-only SQL against the intake database.

Start an interactive prompt:

    py query.py

Run every starter query and exit:

    py query.py all

Run one starter query by its number:

    py query.py 3
"""

import sys

import psycopg2

from load_data import database_url

STARTER_QUERIES = (
    (
        "Roster and skill ratings",
        """
        SELECT name, school_year, intro_programming,
               skill_programming, skill_data_stats,
               skill_frontend_design, skill_business_pitch
        FROM students
        ORDER BY name
        """,
    ),
    (
        "Tools each student listed",
        """
        SELECT s.name,
               string_agg(t.name, ', ' ORDER BY t.name) AS tools
        FROM students s
        LEFT JOIN student_tools st ON st.student_id = s.student_id
        LEFT JOIN tools t ON t.tool_id = st.tool_id
        GROUP BY s.student_id, s.name
        ORDER BY s.name
        """,
    ),
    (
        "Students per tool",
        """
        SELECT t.name AS tool, COUNT(st.student_id) AS students
        FROM tools t
        LEFT JOIN student_tools st ON st.tool_id = t.tool_id
        GROUP BY t.name
        ORDER BY students DESC, tool
        """,
    ),
    (
        "Free on weekday evenings",
        """
        SELECT s.name, s.school_year
        FROM students s
        JOIN student_availability sa ON sa.student_id = s.student_id
        JOIN availability_slots sl ON sl.slot_id = sa.slot_id
        WHERE sl.period = 'weekday' AND sl.time_of_day = 'evening'
        ORDER BY s.name
        """,
    ),
    (
        "Average skills by school year",
        """
        SELECT school_year,
               ROUND(AVG(skill_programming), 2) AS programming,
               ROUND(AVG(skill_data_stats), 2) AS data_stats,
               ROUND(AVG(skill_frontend_design), 2) AS frontend,
               ROUND(AVG(skill_business_pitch), 2) AS business_pitch,
               COUNT(*) AS students
        FROM students
        GROUP BY school_year
        ORDER BY CASE school_year
            WHEN 'First-year' THEN 1
            WHEN 'Sophomore' THEN 2
            WHEN 'Junior' THEN 3
            WHEN 'Senior' THEN 4
        END
        """,
    ),
)


def connect():
    url = database_url()
    if "sslmode=" not in url:
        url = url + ("&" if "?" in url else "?") + "sslmode=require"
    conn = psycopg2.connect(url)
    conn.set_session(readonly=True, autocommit=True)
    return conn


def format_cell(value):
    if value is None:
        return ""
    text = str(value).replace("\n", " ")
    if len(text) > 80:
        return text[:79] + "…"
    return text


def display(cur):
    if cur.description is None:
        print("Statement finished with no rows to show.")
        return
    headers = [col.name for col in cur.description]
    rendered = [[format_cell(value) for value in row] for row in cur.fetchall()]
    widths = [len(header) for header in headers]
    for row in rendered:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))

    def line(cells):
        print("  ".join(cell.ljust(widths[index]) for index, cell in enumerate(cells)))

    line(headers)
    print("  ".join("-" * width for width in widths))
    for row in rendered:
        line(row)
    noun = "row" if len(rendered) == 1 else "rows"
    print(f"({len(rendered)} {noun})")


def run_query(cur, statement):
    try:
        cur.execute(statement)
    except psycopg2.Error as error:
        print(error.pgerror.strip() if error.pgerror else error)
        return
    display(cur)


def print_menu():
    print("Starter queries:")
    for number, (title, _) in enumerate(STARTER_QUERIES, start=1):
        print(f"  {number}  {title}")
    print("Type a number, a SQL statement, help, or quit.")


def run_starter(cur, number):
    title, statement = STARTER_QUERIES[number - 1]
    print(title)
    run_query(cur, statement)


def interactive(cur):
    print_menu()
    while True:
        try:
            command = input("sql> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not command:
            continue
        if command.lower() in {"quit", "exit", "q"}:
            return
        if command.lower() in {"help", "menu"}:
            print_menu()
            continue
        if command.isdigit():
            number = int(command)
            if 1 <= number <= len(STARTER_QUERIES):
                run_starter(cur, number)
                continue
            print(f"Pick a starter from 1 to {len(STARTER_QUERIES)}.")
            continue
        run_query(cur, command.rstrip(";"))


def main():
    choice = sys.argv[1] if len(sys.argv) > 1 else None
    starters = range(1, len(STARTER_QUERIES) + 1)
    if choice is not None and choice != "all" and not (
        choice.isdigit() and int(choice) in starters
    ):
        raise SystemExit(f"Usage: py query.py [all | {starters.start}-{starters.stop - 1}]")

    with connect() as conn:
        with conn.cursor() as cur:
            if choice is None:
                interactive(cur)
            elif choice == "all":
                for number in starters:
                    run_starter(cur, number)
                    print()
            else:
                run_starter(cur, int(choice))


if __name__ == "__main__":
    main()
