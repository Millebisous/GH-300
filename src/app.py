"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import csv
import io
import json
import os
import re
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

NSW_PACKAGE_ID = "a97a46fc-2bdd-4b90-ac7f-0cb1e8d7ac3b"
NSW_PACKAGE_URL = (
    f"https://data.nsw.gov.au/data/api/3/action/package_show?id={NSW_PACKAGE_ID}"
)
MONTH_NAME_TO_INDEX = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}
RESOURCE_NAME_PATTERN = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
    re.IGNORECASE,
)
ALLOWED_FUEL_CODES = {"P98", "P95", "U91", "E10"}

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Competitive basketball team and practice sessions",
        "schedule": "Mondays, Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 15,
        "participants": ["james@mergington.edu"]
    },
    "Tennis Club": {
        "description": "Learn tennis skills and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["sarah@mergington.edu"]
    },
    "Art Studio": {
        "description": "Painting, drawing, and visual arts exploration",
        "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
        "max_participants": 18,
        "participants": ["lucas@mergington.edu", "ava@mergington.edu"]
    },
    "Music Ensemble": {
        "description": "Instrumental and vocal music performance",
        "schedule": "Mondays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 25,
        "participants": ["isabella@mergington.edu"]
    },
    "Science Club": {
        "description": "Explore scientific concepts through experiments and projects",
        "schedule": "Fridays, 3:30 PM - 4:30 PM",
        "max_participants": 16,
        "participants": ["ethan@mergington.edu", "mia@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Tuesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 14,
        "participants": ["noah@mergington.edu"]
    }
}


def _fetch_url(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
        if payload:
            return payload
        if hasattr(response, "json"):
            return json.dumps(response.json()).encode("utf-8")
        return b""


def _parse_xlsx_bytes(content: bytes):
    with zipfile.ZipFile(io.BytesIO(content)) as workbook:
        namespace = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        shared_strings_xml = workbook.read("xl/sharedStrings.xml")
        shared_strings = ET.fromstring(shared_strings_xml)
        values = []
        for shared_string in shared_strings.findall("a:si", namespace):
            values.append("".join(text.text or "" for text in shared_string.findall(".//a:t", namespace)))

        sheet_xml = workbook.read("xl/worksheets/sheet1.xml")
        sheet = ET.fromstring(sheet_xml)
        rows = []
        for sheet_row in sheet.findall(".//a:sheetData/a:row", namespace):
            cells = []
            for cell in sheet_row.findall("a:c", namespace):
                cell_type = cell.get("t")
                value_node = cell.find("a:v", namespace)
                if cell_type == "s" and value_node is not None and value_node.text is not None:
                    value = values[int(value_node.text)]
                elif cell_type == "inlineStr":
                    value = "".join(text.text or "" for text in cell.findall(".//a:t", namespace))
                elif value_node is not None and value_node.text is not None:
                    value = value_node.text
                else:
                    value = ""
                cells.append(value)
            rows.append(cells)
    return rows


def _load_resource_rows(url: str):
    content = _fetch_url(url)
    lower_url = url.lower()

    if isinstance(content, bytes):
        try:
            payload = json.loads(content.decode("utf-8-sig"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = None

        if isinstance(payload, dict) and "rows" in payload:
            rows = payload.get("rows", [])
            if not rows:
                return []
            if isinstance(rows[0], dict):
                return rows
            if isinstance(rows[0], list):
                header = [str(value).strip() for value in rows[0]]
                return [dict(zip(header, row)) for row in rows[1:]]

    if lower_url.endswith(".csv"):
        reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
        return list(reader)

    if lower_url.endswith(".xlsx"):
        rows = _parse_xlsx_bytes(content)
        if not rows:
            return []
        header = [value.strip() for value in rows[0]]
        return [dict(zip(header, row)) for row in rows[1:]]

    return []


def _safe_float(value):
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _build_fuel_trend_summary(points):
    if not points:
        return {
            "overall": "mixed",
            "average_weeks_between_dips": 0,
            "next_predicted_drop_week": None,
        }

    sorted_points = sorted(points, key=lambda item: item["date"])
    prices = [point["average"] for point in sorted_points]

    overall = "mixed"
    if prices[-1] > prices[0]:
        overall = "rising"
    elif prices[-1] < prices[0]:
        overall = "falling"

    dip_dates = []
    dip_intervals_days = []
    for index in range(1, len(sorted_points)):
        previous_average = sorted_points[index - 1]["average"]
        current_average = sorted_points[index]["average"]
        if current_average < previous_average:
            dip_dates.append(datetime.fromisoformat(sorted_points[index]["date"]))
            if len(dip_dates) > 1:
                dip_intervals_days.append((dip_dates[-1] - dip_dates[-2]).days)

    average_weeks_between_dips = 0
    if dip_intervals_days:
        average_weeks_between_dips = round(sum(dip_intervals_days) / len(dip_intervals_days) / 7, 1)

    next_predicted_drop_week = None
    if dip_dates:
        average_interval_days = round(sum(dip_intervals_days) / len(dip_intervals_days)) if dip_intervals_days else 7
        next_drop_date = dip_dates[-1].date() + timedelta(days=average_interval_days)
    else:
        next_drop_date = datetime.fromisoformat(sorted_points[-1]["date"]).date() + timedelta(days=7)

    if next_drop_date:
        week_start = next_drop_date - timedelta(days=next_drop_date.weekday())
        next_predicted_drop_week = week_start.isoformat()

    return {
        "overall": overall,
        "average_weeks_between_dips": average_weeks_between_dips,
        "next_predicted_drop_week": next_predicted_drop_week,
    }


def _build_fuel_trends():
    package_response = json.loads(_fetch_url(NSW_PACKAGE_URL).decode("utf-8-sig"))
    resources = package_response.get("result", {}).get("resources", [])

    matching_resources = []
    for resource in resources:
        resource_name = resource.get("name", "")
        if "FuelCheck Price History" not in resource_name:
            continue

        match = RESOURCE_NAME_PATTERN.search(resource_name)
        if not match:
            continue

        month_name = match.group(1).capitalize()
        year = match.group(2)
        if year != "2026":
            continue

        matching_resources.append((month_name, resource.get("url")))

    matching_resources = sorted(matching_resources, key=lambda item: MONTH_NAME_TO_INDEX[item[0]])
    six_month_resources = matching_resources[:6]
    months = [f"{month_name} 2026" for month_name, _ in six_month_resources]

    fuel_daily_points = defaultdict(lambda: defaultdict(list))

    for month_name, resource_url in six_month_resources:
        rows = _load_resource_rows(resource_url)
        for row in rows:
            fuel_code = row.get("FuelCode") or row.get("Fuel Type") or row.get("FuelType")
            price_value = row.get("Price") or row.get("Price (cpl)") or row.get("Average Price")
            timestamp = row.get("PriceUpdatedDate") or row.get("Price Date") or row.get("Date")

            if not fuel_code or fuel_code not in ALLOWED_FUEL_CODES or not price_value or not timestamp:
                continue

            numeric_price = _safe_float(price_value)
            if numeric_price is None:
                continue

            try:
                parsed_date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    parsed_date = datetime.fromisoformat(timestamp)
                except ValueError:
                    continue

            date_key = parsed_date.date().isoformat()
            fuel_daily_points[fuel_code][date_key].append(numeric_price)

    fuel_types = {}
    for fuel_code in sorted(ALLOWED_FUEL_CODES):
        points = []
        for date_key in sorted(fuel_daily_points.get(fuel_code, {})):
            values = fuel_daily_points[fuel_code][date_key]
            if values:
                points.append({"date": date_key, "average": round(sum(values) / len(values), 1)})

        if not points:
            continue

        fuel_types[fuel_code] = {
            "points": points,
            "trend": _build_fuel_trend_summary(points),
        }

    return {"months": months, "fuelTypes": fuel_types}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.get("/fuel-trends")
def get_fuel_trends():
    return _build_fuel_trends()


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student already signed up for this activity")

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/signup")
def unregister_for_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]

    if email not in activity["participants"]:
        raise HTTPException(status_code=404, detail="Student not signed up for this activity")

    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
