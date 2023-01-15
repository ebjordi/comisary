import os


from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

timezone = os.environ.get("USERTIMEZONE")
calendarId = os.environ.get("CALID")


def fetch_events(creds, calendarId, timeStart, timeEnd, timezone):
    try:
        # Call the Calendar API
        service = build("calendar", "v3", credentials=creds)
        events_result = (
            service.events()
            .list(
                calendarId=calendarId,
                timeMin=timeStart,
                timeMax=timeEnd,
                singleEvents=True,
                orderBy="startTime",
                timeZone=timezone,
            )
            .execute()
        )
        return events_result.get("items", [])
    except HttpError as error:
        print(f"Ocurrió un error: {error}")


def get_email_address(creds):
    service = build("people", "v1", credentials=creds)
    results = (
        service.people()
        .get(resourceName="people/me", personFields="emailAddresses")
        .execute()
    )
    return results.get("emailAddresses", [])[0].get("value", "")


def send_mail_gmail_api(creds, message):
    try:
        service = build("gmail", "v1", credentials=creds)
        send_message = (
            service.users().messages().send(userId="me", body=message).execute()
        )
        print(f"Mail enviado. Message Id: {send_message['id']}")
    #        logging.debug(f"Mail enviado .Message Id: {send_message['id']}")
    except HttpError as error:
        print(f"Ocurrio un error: {error}. Mail no enviado")


def dispatch_event(creds, event, calendarId=calendarId):
    try:
        service = build("calendar", "v3", credentials=creds)
        event = service.events().insert(calendarId=calendarId, body=event).execute()
        print(f'Evento creado: {event.get("htmlLink")}')
    #        logging.error(f'Event created: {event.get("htmlLink")}')
    except HttpError as error:
        print(f"Ocurrió un error: {error}. No se creó el evento")


#        logging.error(f"An error occurred: {error}. Event not created")


def get_google_creds():
    creds = None
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/userinfo.email",
    ]
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds
