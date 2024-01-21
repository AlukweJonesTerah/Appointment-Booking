import datetime as dt
import json
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/calendar']


def main():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            print(f"creds.expired: {creds.expired}")
            print(f"creds.refresh_token: {creds.refresh_token}")

        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds = flow.run_local_server(port=0)
            print(f"creds.expired: {creds.expired}")
            print(f"creds.refresh_token: {creds.refresh_token}")

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    # Getting the list of events in google calendar

    try:
        service = build("calendar", "v3", credentials=creds)

        # Call the Calendar API
        now = dt.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time

        print("Getting the upcoming 10 events")
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            print("No upcoming events found.")
            return
            # Prints the start and name of the next 10 events
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            print(start, event["summary"])
    except HttpError as error:
        print("An error occurred: ", error)

    # Adding events to google calendar
    try:
        service = build("calendar", "v3", credentials=creds)
        event = {
            "summary": "My Python Event",
            "location": "Somewhere Online",
            "description": "some more description on this event",
            "colorId": 6,
            "start": {
                "dateTime": "2024-01-24T09:00:00+03:00",
                "timeZone": "Africa/Nairobi"
            },
            "end": {
                "dateTime": "2024-01-07T17:00:00+03:00",
                "timeZone": "Africa/Nairobi"
            },
            "recurrence": [
                "RRULE:FREQ=DAILY;COUNT=3"
            ],
            "attendees": [
                {"email": "tj.papajones@gmail.com"},
                {"email": "jtalukwe@kabarak.ac.ke"},
                {"email": "example@gmail.com"},
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
        event = service.events().insert(calendarId="primary", body=event).execute()
        print(f"Event created {event.get('htmlLink')}")

    except HttpError as error:
        print("An error occurred: ", error)
        print(f"An error occurred: {error}")
        print(f"Error content: {error.content}")


if __name__ == '__main__':
    main()
