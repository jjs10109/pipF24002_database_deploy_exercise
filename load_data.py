"""Create the intake schema and load class_dataset.csv into Postgres."""

import csv
from pathlib import Path

import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parent
TABLES = (
    "students",
    "tools",
    "student_tools",
    "availability_slots",
    "student_availability",
)


def database_url():
    env_path = ROOT / ".env"
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
        if line.startswith(("postgres://", "postgresql://")):
            return line
    raise SystemExit("DATABASE_URL not found in .env")


def csv_path():
    for candidate in (ROOT / "data" / "class_dataset.csv", ROOT / "class_dataset.csv"):
        if candidate.is_file():
            return candidate
    raise SystemExit("class_dataset.csv not found in data/ or the project root")


def schema_statements():
    text = (ROOT / "schema.sql").read_text(encoding="utf-8")
    return [part.strip() for part in text.split(";") if part.strip()]


def text_or_none(value):
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def working_style(value):
    cleaned = text_or_none(value)
    if cleaned == "#NAME?":
        return None
    return cleaned


def split_list(value):
    if not value:
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def parse_slot(label):
    period, time_of_day = label.split()
    return period.lower(), time_of_day.lower().rstrip("s")


def load(cur, path):
    cur.execute("SELECT name, tool_id FROM tools")
    tools = dict(cur.fetchall())
    cur.execute("SELECT period, time_of_day, slot_id FROM availability_slots")
    slots = {(period, time_of_day): slot_id for period, time_of_day, slot_id in cur.fetchall()}

    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            cur.execute(
                """
                INSERT INTO students (
                    identifier, name, school_year, intro_programming,
                    skill_programming, skill_data_stats,
                    skill_frontend_design, skill_business_pitch,
                    working_style, interests, semester_goal, submitted_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING student_id
                """,
                (
                    row["netid"].strip(),
                    row["name"].strip(),
                    row["school_year"].strip(),
                    row["intro_programming"].strip(),
                    int(row["skill_programming"]),
                    int(row["skill_data_stats"]),
                    int(row["skill_frontend_design"]),
                    int(row["skill_business_pitch"]),
                    working_style(row["working_style"]),
                    text_or_none(row["interests"]),
                    text_or_none(row["semester_goal"]),
                    row["submitted_at"].strip(),
                ),
            )
            student_id = cur.fetchone()[0]
            identifier = row["netid"].strip()

            for tool_name in split_list(row["tools"]):
                tool_id = tools.get(tool_name)
                if tool_id is None:
                    raise SystemExit(f"Unknown tool {tool_name!r} for {identifier}")
                cur.execute(
                    "INSERT INTO student_tools (student_id, tool_id) VALUES (%s, %s)",
                    (student_id, tool_id),
                )

            for label in split_list(row["availability"]):
                key = parse_slot(label)
                slot_id = slots.get(key)
                if slot_id is None:
                    raise SystemExit(f"Unknown availability {label!r} for {identifier}")
                cur.execute(
                    "INSERT INTO student_availability (student_id, slot_id) VALUES (%s, %s)",
                    (student_id, slot_id),
                )


def main():
    url = database_url()
    if "sslmode=" not in url:
        url = url + ("&" if "?" in url else "?") + "sslmode=require"

    with psycopg2.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DROP TABLE IF EXISTS
                    student_availability,
                    student_tools,
                    availability_slots,
                    tools,
                    students
                CASCADE
                """
            )
            for statement in schema_statements():
                cur.execute(statement)
            load(cur, csv_path())
            for table in TABLES:
                cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table)))
                print(f"{table}: {cur.fetchone()[0]}")


if __name__ == "__main__":
    main()
