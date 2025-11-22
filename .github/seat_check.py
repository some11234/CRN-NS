import os
import re
import requests

UVM_URL = "https://soc.uvm.edu/api/?page=fose&route=details"

# List of courses to watch for your friend
COURSES = [
    {
        "name": "ANTH 1140 (CRN 15447)",
        "body": {
            "group": "code:ANTH 1140",
            "key": "crn:15447",
            "srcdb": "202601",
            "matched": ""
        },
    },
    {
        "name": "BUS 2620 (CRN 11518)",
        "body": {
            "group": "code:BUS 2620",
            "key": "crn:11518",
            "srcdb": "202601",
            "matched": ""
        },
    },
    {
        "name": "NR 1100 (CRN 13970)",
        "body": {
            "group": "code:NR 1100",
            "key": "crn:13970",
            "srcdb": "202601",
            "matched": ""
        },
    },
]

HEADERS = {
    "Content-Type": "application/json",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "UVM-Seat-Checker/2.0 (personal; 1req/15min)"
}

WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # IFTTT webhook URL (full URL)


def check_course(course):
    """Check one course, return True if webhook was triggered."""
    name = course["name"]
    body = course["body"]

    print(f"\n----- Checking {name} -----")
    r = requests.post(UVM_URL, json=body, headers=HEADERS, timeout=10)
    r.raise_for_status()

    data = r.json()

    title = data.get("title")
    crn = data.get("crn")
    code = data.get("code")
    print(f"Course from API: {code} (CRN {crn}) – {title}")

    seats_html = data.get("seats", "")
    print("Seats HTML:", seats_html)

    m = re.search(r"seats_avail[^>]*>(\d+)<", seats_html)
    if not m:
        print("❌ Could not find seats_avail in the response.")
        return False

    seats_avail = int(m.group(1))
    print(f"Parsed seats_avail = {seats_avail}")

    if seats_avail <= 0:
        print("😔 No open seats for this course. Not triggering webhook.")
        return False

    print("🎉 THERE ARE OPEN SEATS for this course!")

    if not WEBHOOK_URL:
        print("WEBHOOK_URL not set, skipping IFTTT trigger.")
        return False

    print("Triggering IFTTT webhook (no payload)...")
    resp = requests.post(WEBHOOK_URL, timeout=10)
    print(f"IFTTT HTTP status: {resp.status_code}")
    print(f"IFTTT response body: {resp.text}")
    resp.raise_for_status()
    print("✅ IFTTT webhook fired successfully for this course.")
    return True


def main():
    if not WEBHOOK_URL:
        print("⚠️ Warning: WEBHOOK_URL env var is not set. "
              "Script will check seats but will not alert.")
    any_triggered = False

    for course in COURSES:
        try:
            triggered = check_course(course)
            any_triggered = any_triggered or triggered
        except Exception as e:
            print(f"⚠️ Error checking {course['name']}: {e}")

    if not any_triggered:
        print("\nAll courses checked; no alerts triggered this run.")


if __name__ == "__main__":
    main()
