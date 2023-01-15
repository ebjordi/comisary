from __future__ import print_function

import datetime

import sqlite3
import logging

# system tools
import os.path
import os
from sys import argv

# not used yet
from dbHandle import commitHours

# Google API functions
from services import *

from dotenv import load_dotenv

load_dotenv()

import base64  # encoding
from email.message import EmailMessage


timezone = os.environ.get("USERTIMEZONE")
sender = os.environ.get("FROM")
calendarId = os.environ.get("CALID")
dbname = os.environ.get("COMMITDB")


def main():
    """Shows basic usage of the Google Calendar API.
    Create single events and recurring.
    """
    creds = get_google_creds()
    # determine which function to run
    if argv[1] == "help":
        print(
            "tm add <dd-mm-aa/dd-mm-aaaa> <hh:mm(24h)> <duración(horas:int)> <descripción> crea un evento en el día y horario especificado"
        )
        print(
            "tm add <duración> <descripción> crea un evento que empieza inmediatamente, de duracion especificada"
        )
        print(
            "tm addW <dd-mm-aa/dd-mm-aaaa> <hh:mm(24h)> <duración(horas:int)> <descripción> <mon,tues,su/lunes,martes,mie> crea un evento que se repite los días especificados"
        )
    if argv[1] == "test":
        for arg in argv[2:]:
            print(arg)
    if argv[1] == "add":
        day = argv[2].split("-")
        start = argv[3].split(":")
        duration = argv[4]
        description = argv[5]
        addEvent(creds, day, start, duration, description, timezone, calendarId)
    if argv[1] == "addW":
        day = argv[2].split("-")
        start = argv[3].split(":")
        duration = argv[4]
        description = argv[5]
        if len(argv) > 6:
            recurrence = [ar.split(",") for ar in argv[6:]]
            recurrence = flatten(recurrence)
        else:
            recurrence = None
        addEventWeekly(creds, day, start, duration, description, recurrence)
    if argv[1] == "addN":
        duration = argv[2]
        description = argv[3]
        addEventNow(creds, duration, description, timezone, calendarId)
    if argv[1] == "commit":
        events = getEvents(creds)
        commitHours(events, dbname)


def getEvents(creds, timezone=timezone, calendarId=calendarId):
    try:
        today = datetime.date.today()
        timeStart = str(today) + "T00:00:00Z"
        timeEnd = str(today) + "T23:59:59Z"  # 'Z' indicates UTC time
        print("Getting today's assigned hours")

        events = fetch_events(creds, calendarId, timeStart, timeEnd, timezone)
        if not events:
            print("No upcoming events found.")
        return events

    except HttpError as error:
        print(f"Ocurrió un error: {error}")


# add calendar event from curret time for length of 'duration'
def addEventNow(
    creds,
    duration,
    description,
    timezone=timezone,
    calendarId=calendarId,
):
    if timezone == "America/Argentina/Buenos_Aires":
        start = datetime.datetime.now().astimezone()
        end = datetime.datetime.now().astimezone() + datetime.timedelta(
            hours=int(duration)
        )
    else:
        start = datetime.datetime.now()
        end = datetime.datetime.now()

    start_formatted = start.isoformat()
    end_formatted = end.isoformat()

    event = {
        "summary": description,
        "start": {
            "dateTime": start_formatted,
            "timeZone": timezone,
        },
        "end": {
            "dateTime": end_formatted,
            "timeZone": timezone,
        },
    }

    prompt = f"Se creará el evento {description} con inicio {start.strftime('%d/%m/%Y, %H:%M')}, una duración de {duration} hora/s"
    confirm = confirmation(prompt)
    if confirm is True:
        dispatch_event(creds, event, calendarId=calendarId)
    else:
        print("No se creó el evento")
    return


def addEvent(
    creds,
    day,
    start,
    duration,
    description,
    timezone=timezone,
    calendarId=calendarId,
):
    day = [int(d) for d in day]
    if day[2] < 100:
        day[2] += 2000
    start = [int(h) for h in start]
    start = datetime.datetime(day[2], day[1], day[0], start[0], start[1])
    end = start + datetime.timedelta(hours=int(duration))
    start_formatted = start.isoformat()
    end_formatted = end.isoformat()

    event = {
        "summary": description,
        "start": {
            "dateTime": start_formatted,
            "timeZone": timezone,
        },
        "end": {
            "dateTime": end_formatted,
            "timeZone": timezone,
        },
    }
    prompt = f"Se creará el evento {description} con inicio {start.strftime('%d/%m/%Y, %H:%M')}, una duración de {duration} hora/s"
    confirm = confirmation(prompt)
    if confirm is True:
        dispatch_event(creds, event, calendarId=calendarId)
    else:
        print("No se creó el evento")
    return


def addEventWeekly(
    creds,
    day,
    start,
    duration,
    description,
    recurrence=None,
    timezone=timezone,
    calendarId=calendarId,
):
    if recurrence is None:
        raise Exception(
            "No se especificó días de recurrencia. Para eventos no recurrentes use <add>"
        )

    days_es = {
        "LU": "MO",
        "MA": "TU",
        "MI": "WE",
        "JU": "TH",
        "VI": "FR",
        "SA": "SA",
        "DO": "SU",
    }
    eng = {
        "MO": "Monday",
        "TU": "Tuesday",
        "WE": "Wednesday",
        "TH": "Thursday",
        "FR": "Friday",
        "SA": "Saturday",
        "SU": "Sunday",
    }

    esp = {
        "MO": "Lunes",
        "TU": "Martes",
        "WE": "Miércoles",
        "TH": "Jueves",
        "FR": "Viernes",
        "SA": "Sábado",
        "SU": "Domingo",
    }

    rec = ""
    eng_lang = False
    for r in recurrence:
        r_key = r[:2].upper()
        if r_key in rec:
            continue
        if r_key in days_es:
            rec += f",{days_es[r_key]}"
        else:
            rec += f",{r_key}"
            eng_lang = True
    rec = rec[1:]

    days_prompt = ",".join(
        [eng[key] if eng_lang is True else esp[key] for key in rec.split(",")]
    )

    day = [int(d) for d in day]
    if day[2] < 100:
        day[2] += 2000
    start = [int(h) for h in start]
    start = datetime.datetime(day[2], day[1], day[0], start[0], start[1])
    end = start + datetime.timedelta(hours=int(duration))
    start_formatted = start.isoformat()
    end_formatted = end.isoformat()

    event = {
        "summary": description,
        "start": {
            "dateTime": start_formatted,
            "timeZone": timezone,
        },
        "end": {
            "dateTime": end_formatted,
            "timeZone": timezone,
        },
        "recurrence": [f"RRULE:FREQ=WEEKLY;BYDAY={rec}"],
    }

    prompt = f"Se creará el evento {description} con inicio {start.strftime('%d/%m/%Y, %H:%M')}, una duración de {duration} hora/s, y recurrente los días {days_prompt}"

    confirm = confirmation(prompt)
    if confirm is True:
        dispatch_event(creds, event, calendarId=calendarId)
    else:
        print("No se creó el evento")
    return


def confirmation(prompt: str):
    response = input(prompt + ".\n¿Confirmar?[s/N]\n").upper()[0]

    if response == "S" or response == "Y":
        return True
    elif response == "N":
        return False
    else:
        raise Exception("No entendí, usá [y/s/n]")


def compose_mail(to, subject, body):
    message = EmailMessage()
    # body
    message.set_content(body)
    # header
    message["To"] = to
    message["From"] = sender
    message["Subject"] = subject

    draft_encoded = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}
    return draft_encoded


def flatten(l):
    return [item for sublist in l for item in sublist]


if __name__ == "__main__":
    main()
