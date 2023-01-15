import sqlite3


def create_db(name, table_name, **kwargs):
    conn = sqlite3.connect(name)
    cur = conn.cursor()
    print("Base de datos conectada")
    column_names = "id INTEGER PRIMATY KEY"
    for key, value in kwargs.items():
        column_names += f", {key.lower()} {value.upper()}"
    conn.execute(f"CREATE TABLE {table_name}.db ({column_names})")
    print(f"Base de datos {name} creada con tabla {table_name}")
    conn.commit()
    conn.close()


def commitHours(events,dbname):
    if events in None:
        return

    total_duration = datetime.timedelta(
        seconds=0,
        minutes=0,
        hours=0,
    )
    id = 0
    print("Dedicated hours:")
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        end = event["end"].get("dateTime", event["end"].get("date"))

        start_formatted = parser.isoparse(
            start
        )  # changing the start time to datetime format
        end_formatted = parser.isoparse(end)  # changing the end time to datetime format
        duration = end_formatted - start_formatted

        total_duration += duration
        print(f"{event['summary']}, duration: {duration}")
    print(f"Total commited time: {total_duration}")

    conn = sqlite3.connect(dbname)
    cur = conn.cursor()
    print("Opened database successfully")
    date = datetime.date.today()

    formatted_total_duration = total_duration.seconds / 60 / 60
    commited_hours = (date, "ASSINGMENT", formatted_total_duration)
    cur.execute(
        "INSERT INTO hours VALUES(?,?,?);", commited_hours
    )  # ? se cambian por los valores de committed_hours
    conn.commit()
    print("Assigned hours added to database successfully")
