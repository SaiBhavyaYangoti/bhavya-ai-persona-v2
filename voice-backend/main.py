from fastapi import FastAPI, Request, Query
from typing import Optional
import requests

app = FastAPI()

CAL_API_KEY = "cal_live_46446a7bf96c703ddcabfad086c5cd91"
USERNAME = "saibhavya-yangoti-s9xhms"
EVENT_SLUG = "30min"


def get_slots(date: str):
    start = f"{date}T00:00:00Z"
    end = f"{date}T18:30:00Z"
    url = f"https://api.cal.com/v2/slots?eventTypeSlug={EVENT_SLUG}&username={USERNAME}&start={start}&end={end}"
    headers = {
        "Authorization": f"Bearer {CAL_API_KEY}",
        "cal-api-version": "2024-09-04"
    }
    res = requests.get(url, headers=headers)
    data = res.json()
    print(f"Cal.com slots response for {date}: {data}")
    all_slots = []
    for day_slots in data.get("data", {}).values():
        for s in day_slots:
            all_slots.append(s["start"])
    return all_slots[:5]


def parse_vapi_body(body: dict, tool_name: str):
    """Extract toolCallId and arguments from Vapi request body."""
    tool_call_id = None
    arguments = {}
    try:
        tool_calls = body.get("message", {}).get("toolCallList", [])
        for tc in tool_calls:
            if tc.get("function", {}).get("name") == tool_name:
                tool_call_id = tc.get("id")
                arguments = tc.get("function", {}).get("arguments", {})
                break
        # fallback to first tool call
        if not tool_call_id and tool_calls:
            tool_call_id = tool_calls[0].get("id")
            arguments = tool_calls[0].get("function", {}).get("arguments", {})
    except Exception as e:
        print(f"Error parsing Vapi body: {e}")
    return tool_call_id, arguments


@app.post("/check-availability")
async def check_availability(request: Request, date: str = Query(None)):
    tool_call_id = None
    actual_date = date

    try:
        body = await request.json()
        print(f"check-availability raw body: {body}")
        tool_call_id, args = parse_vapi_body(body, "checkAvailability")
        if args.get("date"):
            actual_date = args["date"]
        elif "date" in body:
            actual_date = body["date"]
    except Exception as e:
        print(f"Parse error: {e}")

    if not actual_date:
        return {"results": [{"toolCallId": tool_call_id, "result": "I need a date to check availability."}]}

    print(f"Checking availability for: {actual_date}")
    slots = get_slots(actual_date)

    if slots:
        # Convert UTC to IST for readable output
        readable = []
        for s in slots:
            # e.g. 2026-06-10T03:30:00.000Z -> 9:00 AM IST
            time_part = s.split("T")[1][:5]
            h, m = int(time_part.split(":")[0]), int(time_part.split(":")[1])
            h_ist = (h + 5) % 24
            m_ist = m + 30
            if m_ist >= 60:
                m_ist -= 60
                h_ist = (h_ist + 1) % 24
            period = "AM" if h_ist < 12 else "PM"
            h_12 = h_ist if h_ist <= 12 else h_ist - 12
            if h_12 == 0:
                h_12 = 12
            readable.append(f"{h_12}:{m_ist:02d} {period} IST")
        result_str = f"Bhavya is available at: {', '.join(readable)} on {actual_date}. Which slot works for you?"
    else:
        result_str = f"No available slots on {actual_date}. Please try another date."

    return {"results": [{"toolCallId": tool_call_id, "result": result_str}]}


@app.post("/book-meeting")
async def book_meeting(request: Request):
    tool_call_id = None
    name = email = start = None

    try:
        body = await request.json()
        print(f"book-meeting raw body: {body}")
        tool_call_id, args = parse_vapi_body(body, "bookMeeting")
        name = args.get("name")
        email = args.get("email")
        start = args.get("start")
        # fallback direct body
        if not name:
            name = body.get("name")
        if not email:
            email = body.get("email")
        if not start:
            start = body.get("start")
    except Exception as e:
        print(f"Parse error: {e}")
        return {"results": [{"toolCallId": tool_call_id, "result": f"Error parsing request: {e}"}]}

    if not all([name, email, start]):
        return {"results": [{"toolCallId": tool_call_id, "result": "I need your name, email, and preferred time slot to book."}]}

    print(f"Booking for {name} ({email}) at {start}")
    url = "https://api.cal.com/v2/bookings"
    headers = {
        "Authorization": f"Bearer {CAL_API_KEY}",
        "cal-api-version": "2024-08-13",
        "Content-Type": "application/json"
    }
    payload = {
        "eventTypeSlug": EVENT_SLUG,
        "username": USERNAME,
        "start": start,
        "attendee": {
            "name": name,
            "email": email,
            "timeZone": "Asia/Kolkata"
        }
    }
    res = requests.post(url, json=payload, headers=headers)
    data = res.json()
    print(f"Booking response: {data}")

    if data.get("status") == "success" or data.get("uid"):
        result_str = f"Done! I've booked a 30-minute interview slot for {name} on {start}. A confirmation email will be sent to {email}."
    else:
        error = data.get("message", "Unknown error")
        result_str = f"Booking failed: {error}. Please try a different slot."

    return {"results": [{"toolCallId": tool_call_id, "result": result_str}]}


@app.get("/ping")
def ping():
    return {"status": "alive"}


@app.get("/test-cal")
def test_cal(date: str = Query("2026-06-10")):
    slots = get_slots(date)
    return {"date": date, "slots": slots}
