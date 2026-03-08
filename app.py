from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import pandas as pd
import os
import uvicorn

app = FastAPI()

# your routes here

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

try:
    print("Loading data/crime.csv ...")
    crime_df = pd.read_csv("data/crime.csv")
    print(crime_df.head())
except Exception as e:
    print("Error loading crime.csv:", e)
    crime_df = pd.DataFrame()

try:
    print("Loading data/code_violations.csv ...")
    violations_df = pd.read_csv("data/code_violations.csv")
    print(violations_df.head())
except Exception as e:
    print("Error loading code_violations.csv:", e)
    violations_df = pd.DataFrame()


@app.get("/", response_class=HTMLResponse)
def home():
    return page()


@app.get("/plan")
def generate_plan(issue: str = Query(...)):
    issue_lower = issue.lower()

    # Code violation related issues
    if (
        "abandoned" in issue_lower
        or "house" in issue_lower
        or "dumping" in issue_lower
        or "trash" in issue_lower
        or "overgrown" in issue_lower
    ):
        matching_violations = violations_df[
            violations_df["type"].str.lower().str.contains(
                "abandoned|dumping|overgrown|unsafe|trash", na=False
            )
        ]

        examples = matching_violations.head(3).to_dict(orient="records")

        return {
            "category": "Code Violation",
            "action_plan": [
                "Take a photo of the issue.",
                "Note the exact address.",
                "Report it through the city service channel.",
                "Track the case if no response comes."
            ],
            "dataset_examples": examples
        }

    # Safety related issues
    if (
        "safe" in issue_lower
        or "crime" in issue_lower
        or "unsafe" in issue_lower
        or "robbery" in issue_lower
        or "theft" in issue_lower
    ):
        recent_crimes = crime_df.head(3).to_dict(orient="records")

        return {
            "category": "Safety Concern",
            "action_plan": [
                "Check recent incidents in the area.",
                "Avoid isolated routes at night.",
                "Report suspicious activity if needed.",
                "Call emergency services for immediate danger."
            ],
            "dataset_examples": recent_crimes
        }

    # Default response
    return {
        "category": "General Civic Issue",
        "action_plan": [
            "Clarify the issue type.",
            "Find the right city service channel.",
            "Submit the request with details and location."
        ],
        "dataset_examples": []
    }

@app.get("/planner-summary")
def planner_summary():
    total_crimes = int(len(crime_df))
    total_violations = int(len(violations_df))

    top_crime_types = crime_df["type"].value_counts().head(5).to_dict()
    top_violation_types = violations_df["type"].value_counts().head(5).to_dict()

    # Simple prototype scoring logic
    safety_score = max(0, 100 - total_crimes * 2)
    maintenance_score = max(0, 100 - total_violations * 5)
    urbanpulse_score = round((safety_score + maintenance_score) / 2)

    crime_areas = crime_df["address"].value_counts().head(3).to_dict()
    violation_areas = violations_df["address"].value_counts().head(3).to_dict()

    top_issue_areas = []

    for address, count in crime_areas.items():
        top_issue_areas.append({
            "area": address,
            "issue_type": "Crime hotspot",
            "count": int(count),
            "recommended_action": "Review patrol coverage and lighting conditions."
        })

    for address, count in violation_areas.items():
        top_issue_areas.append({
            "area": address,
            "issue_type": "Maintenance hotspot",
            "count": int(count),
            "recommended_action": "Schedule inspection or cleanup follow-up."
        })

    top_issue_areas = top_issue_areas[:5]

    priority_actions = []

    if "Illegal Dumping" in top_violation_types:
        priority_actions.append({
            "title": "Illegal dumping response",
            "reason": f"{top_violation_types['Illegal Dumping']} dumping cases found in dataset.",
            "action": "Increase cleanup scheduling and install temporary signage or monitoring."
        })

    if "Abandoned House" in top_violation_types or "Unsafe Structure" in top_violation_types:
        priority_actions.append({
            "title": "Property inspection sweep",
            "reason": "Abandoned or unsafe property signals appear in code violations.",
            "action": "Prioritize inspection and code enforcement follow-up."
        })

    if "Vehicle Break-in" in top_crime_types or "Robbery" in top_crime_types:
        priority_actions.append({
            "title": "Targeted public safety intervention",
            "reason": "Vehicle break-ins or robbery incidents appear in crime records.",
            "action": "Review patrol timing, street lighting, and neighborhood awareness measures."
        })

    if len(priority_actions) == 0:
        priority_actions.append({
            "title": "General monitoring",
            "reason": "No dominant pattern detected.",
            "action": "Continue monitoring issue distribution across neighborhoods."
        })

    return {
        "total_crimes": total_crimes,
        "total_violations": total_violations,
        "top_crime_types": top_crime_types,
        "top_violation_types": top_violation_types,
        "urbanpulse_score": urbanpulse_score,
        "safety_score": safety_score,
        "maintenance_score": maintenance_score,
        "priority_actions": priority_actions,
        "top_issue_areas": top_issue_areas,
        "calculation_logic": {
            "urbanpulse_score": f"UrbanPulse Index = (Safety Score + Maintenance Score) / 2 = ({safety_score} + {maintenance_score}) / 2 = {urbanpulse_score}",
            "safety_score": f"Safety Score = max(0, 100 - total crimes × 2) = max(0, 100 - {total_crimes} × 2) = {safety_score}",
            "maintenance_score": f"Maintenance Score = max(0, 100 - total violations × 5) = max(0, 100 - {total_violations} × 5) = {maintenance_score}",
            "total_crimes": f"Total Crime Records = number of rows loaded from crime.csv = {total_crimes}",
            "total_violations": f"Total Code Violations = number of rows loaded from code_violations.csv = {total_violations}"
        }
    }
    
@app.get("/planner-map-data")
def planner_map_data():
    crime_points = crime_df.to_dict(orient="records")
    violation_points = violations_df.to_dict(orient="records")

    return {
        "crime_points": crime_points,
        "violation_points": violation_points
    }
@app.get("/page", response_class=HTMLResponse)
def page():
    return """
    <html>
        <head>
            <title>UrbanPulse</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>

            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 1100px;
                    margin: 30px auto;
                    padding: 20px;
                    background: #f5f7fa;
                    color: #222;
                }

                h1 {
                    margin-bottom: 10px;
                }

                .subtitle {
                    color: #555;
                    margin-bottom: 20px;
                }

                .toggle-bar {
                    display: flex;
                    gap: 10px;
                    margin-bottom: 25px;
                }

                .toggle-btn {
                    padding: 10px 18px;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    background: #d9e2ec;
                    color: #1f2d3d;
                    font-weight: bold;
                }

                .toggle-btn.active {
                    background: #1f4e79;
                    color: white;
                }

                .card {
                    margin-top: 20px;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 12px;
                    background: white;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                }

                input {
                    width: 420px;
                    padding: 10px;
                    font-size: 14px;
                    border: 1px solid #ccc;
                    border-radius: 6px;
                }

                button.action-btn {
                    padding: 10px 14px;
                    font-size: 14px;
                    margin-left: 10px;
                    cursor: pointer;
                    border: none;
                    border-radius: 6px;
                    background: #1f4e79;
                    color: white;
                }

                button.action-btn:hover {
                    background: #163a5a;
                }

                .category {
                    font-weight: bold;
                    font-size: 18px;
                    color: #1f4e79;
                    margin-bottom: 12px;
                }

                .section-title {
                    margin-top: 20px;
                    font-weight: bold;
                    color: #333;
                }

                ul {
                    margin-top: 10px;
                    padding-left: 20px;
                }

                li {
                    margin-bottom: 8px;
                }

                #map {
                    height: 400px;
                    margin-top: 25px;
                    border-radius: 12px;
                    overflow: hidden;
                }

                .hidden {
                    display: none;
                }

                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 16px;
                    margin-top: 20px;
                }

                .stat-box {
                    background: #eef4f8;
                    border-radius: 10px;
                    padding: 20px;
                    text-align: center;
                }

                .stat-number {
                    font-size: 28px;
                    font-weight: bold;
                    color: #1f4e79;
                }

                .two-col {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin-top: 20px;
                }

                .small-note {
                    color: #666;
                    font-size: 13px;
                    margin-top: 10px;
                }

                .tooltip-box {
    position: relative;
    cursor: help;
}

.tooltip-box .tooltip-text {
    visibility: hidden;
    opacity: 0;
    transition: opacity 0.2s ease;
    width: 260px;
    background-color: #1f2d3d;
    color: #fff;
    text-align: left;
    border-radius: 8px;
    padding: 10px;
    position: absolute;
    z-index: 999;
    bottom: 110%;
    left: 50%;
    transform: translateX(-50%);
    font-size: 12px;
    line-height: 1.4;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.tooltip-box:hover .tooltip-text {
    visibility: visible;
    opacity: 1;
}
            </style>
        </head>

        <body>
            <h1>UrbanPulse</h1>
            <div class="subtitle">Turn neighborhood concerns into action plans and city insights.</div>

            <div class="toggle-bar">
                <button id="residentBtn" class="toggle-btn active" onclick="showResident()">Resident Mode</button>
                <button id="plannerBtn" class="toggle-btn" onclick="showPlanner()">Planner Mode</button>
            </div>

            <div id="residentView">
                <div class="card">
                    <p>Describe what is happening in your neighborhood:</p>
                    <input id="issueInput" placeholder="Example: abandoned house next door">
                    <button class="action-btn" onclick="generatePlan()">Generate Action Plan</button>
                </div>

                <div id="result" class="card hidden">
                    <div class="category" id="category"></div>

                    <div class="section-title">Action Plan</div>
                    <ul id="actionList"></ul>

                    <div class="section-title">Related City Data</div>
                    <ul id="dataExamples"></ul>
                </div>

                <div id="map"></div>
            </div>

         <div id="plannerView" class="hidden">
    <div class="card">
        <div class="category">Planner Dashboard</div>
        <div class="small-note">Action-oriented city insights based on loaded local datasets.</div>

        <div class="stats-grid" style="grid-template-columns: repeat(3, 1fr);">
    <div class="stat-box tooltip-box">
        <div class="stat-number" id="urbanPulseScore">0</div>
        <div>UrbanPulse Index</div>
        <div class="tooltip-text" id="tooltipUrbanPulse">Calculation logic will appear here.</div>
    </div>
    <div class="stat-box tooltip-box">
        <div class="stat-number" id="safetyScore">0</div>
        <div>Safety Score</div>
        <div class="tooltip-text" id="tooltipSafety">Calculation logic will appear here.</div>
    </div>
    <div class="stat-box tooltip-box">
        <div class="stat-number" id="maintenanceScore">0</div>
        <div>Maintenance Score</div>
        <div class="tooltip-text" id="tooltipMaintenance">Calculation logic will appear here.</div>
    </div>
</div>

<div class="stats-grid">
    <div class="stat-box tooltip-box">
        <div class="stat-number" id="totalCrimes">0</div>
        <div>Total Crime Records</div>
        <div class="tooltip-text" id="tooltipCrimes">Calculation logic will appear here.</div>
    </div>
    <div class="stat-box tooltip-box">
        <div class="stat-number" id="totalViolations">0</div>
        <div>Total Code Violations</div>
        <div class="tooltip-text" id="tooltipViolations">Calculation logic will appear here.</div>
    </div>
</div>

        <div class="card">
            <div class="section-title">Planner Map Controls</div>
            <label><input type="checkbox" id="showCrimeLayer" checked onchange="refreshPlannerMap()"> Show Crime</label>
            <label style="margin-left:20px;"><input type="checkbox" id="showViolationLayer" checked onchange="refreshPlannerMap()"> Show Code Violations</label>
        </div>

        <div id="plannerMap" style="height: 420px; margin-top: 20px; border-radius: 12px; overflow: hidden;"></div>

        <div class="two-col">
            <div class="card">
                <div class="section-title">Priority Action Recommendations</div>
                <ul id="priorityActionList"></ul>
            </div>

            <div class="card">
                <div class="section-title">Top Issue Areas</div>
                <ul id="issueAreaList"></ul>
            </div>
        </div>

        <div class="two-col">
            <div class="card">
                <div class="section-title">Top Crime Types</div>
                <ul id="topCrimeList"></ul>
            </div>

            <div class="card">
                <div class="section-title">Top Code Violation Types</div>
                <ul id="topViolationList"></ul>
            </div>
        </div>
    </div>
</div>

            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

            <script>
                var residentMap = L.map('map').setView([32.3668, -86.3000], 13);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: 'OpenStreetMap'
}).addTo(residentMap);

var plannerMap = L.map('plannerMap').setView([32.3668, -86.3000], 13);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: 'OpenStreetMap'
}).addTo(plannerMap);

var residentMarkers = [];
var plannerMarkers = [];
var plannerCrimePoints = [];
var plannerViolationPoints = [];


                function showResident() {
    document.getElementById("residentView").classList.remove("hidden");
    document.getElementById("plannerView").classList.add("hidden");

    document.getElementById("residentBtn").classList.add("active");
    document.getElementById("plannerBtn").classList.remove("active");

    setTimeout(function() {
        residentMap.invalidateSize();
    }, 200);
}

              async function showPlanner() {
    document.getElementById("residentView").classList.add("hidden");
    document.getElementById("plannerView").classList.remove("hidden");

    document.getElementById("residentBtn").classList.remove("active");
    document.getElementById("plannerBtn").classList.add("active");

    setTimeout(function() {
        plannerMap.invalidateSize();
    }, 200);

    const summaryResponse = await fetch("/planner-summary");
    const summaryData = await summaryResponse.json();

    document.getElementById("urbanPulseScore").textContent = summaryData.urbanpulse_score;
    document.getElementById("safetyScore").textContent = summaryData.safety_score;
    document.getElementById("maintenanceScore").textContent = summaryData.maintenance_score;

    document.getElementById("totalCrimes").textContent = summaryData.total_crimes;
    document.getElementById("totalViolations").textContent = summaryData.total_violations;
    document.getElementById("tooltipUrbanPulse").textContent = summaryData.calculation_logic.urbanpulse_score;
document.getElementById("tooltipSafety").textContent = summaryData.calculation_logic.safety_score;
document.getElementById("tooltipMaintenance").textContent = summaryData.calculation_logic.maintenance_score;
document.getElementById("tooltipCrimes").textContent = summaryData.calculation_logic.total_crimes;
document.getElementById("tooltipViolations").textContent = summaryData.calculation_logic.total_violations;

    const topCrimeList = document.getElementById("topCrimeList");
    topCrimeList.innerHTML = "";
    for (const [key, value] of Object.entries(summaryData.top_crime_types)) {
        const li = document.createElement("li");
        li.textContent = key + ": " + value;
        topCrimeList.appendChild(li);
    }

    const topViolationList = document.getElementById("topViolationList");
    topViolationList.innerHTML = "";
    for (const [key, value] of Object.entries(summaryData.top_violation_types)) {
        const li = document.createElement("li");
        li.textContent = key + ": " + value;
        topViolationList.appendChild(li);
    }

    const priorityActionList = document.getElementById("priorityActionList");
    priorityActionList.innerHTML = "";
    summaryData.priority_actions.forEach(item => {
        const li = document.createElement("li");
        li.innerHTML = "<strong>" + item.title + "</strong><br>" +
                       "Why: " + item.reason + "<br>" +
                       "Suggested action: " + item.action;
        priorityActionList.appendChild(li);
    });

    const issueAreaList = document.getElementById("issueAreaList");
    issueAreaList.innerHTML = "";
    summaryData.top_issue_areas.forEach(item => {
        const li = document.createElement("li");
        li.style.cursor = "pointer";
        li.innerHTML = "<strong>" + item.area + "</strong><br>" +
                       item.issue_type + " (" + item.count + ")<br>" +
                       "Recommended: " + item.recommended_action;
        issueAreaList.appendChild(li);
    });

    const mapResponse = await fetch("/planner-map-data");
    const mapData = await mapResponse.json();

    plannerCrimePoints = mapData.crime_points || [];
    plannerViolationPoints = mapData.violation_points || [];

    refreshPlannerMap();

    setTimeout(function() {
        plannerMap.invalidateSize();
    }, 200);
}
function refreshPlannerMap() {
    plannerMarkers.forEach(marker => plannerMap.removeLayer(marker));
    plannerMarkers = [];

    const showCrime = document.getElementById("showCrimeLayer").checked;
    const showViolation = document.getElementById("showViolationLayer").checked;

    if (showCrime) {
        plannerCrimePoints.forEach(item => {
            if (item.latitude && item.longitude) {
                const marker = L.circleMarker([item.latitude, item.longitude], {
                    radius: 7
                }).addTo(plannerMap).bindPopup("Crime: " + item.type + "<br>" + item.address);
                plannerMarkers.push(marker);
            }
        });
    }

    if (showViolation) {
        plannerViolationPoints.forEach(item => {
            if (item.latitude && item.longitude) {
                const marker = L.marker([item.latitude, item.longitude])
                    .addTo(plannerMap)
                    .bindPopup("Violation: " + item.type + "<br>" + item.address);
                plannerMarkers.push(marker);
            }
        });
    }

    if (plannerMarkers.length > 0) {
        const group = new L.featureGroup(plannerMarkers);
        plannerMap.fitBounds(group.getBounds().pad(0.2));
    } else {
        plannerMap.setView([32.3668, -86.3000], 13);
    }
}

                async function generatePlan() {
                    const issue = document.getElementById("issueInput").value;
                    const response = await fetch("/plan?issue=" + encodeURIComponent(issue));
                    const data = await response.json();

                    document.getElementById("result").classList.remove("hidden");
                    document.getElementById("category").textContent = "Category: " + data.category;

                    const actionList = document.getElementById("actionList");
                    actionList.innerHTML = "";

                    data.action_plan.forEach(step => {
                        const li = document.createElement("li");
                        li.textContent = step;
                        actionList.appendChild(li);
                    });

                    const dataExamples = document.getElementById("dataExamples");
                    dataExamples.innerHTML = "";

                   residentMarkers.forEach(marker => residentMap.removeLayer(marker));
residentMarkers = [];

                    if (data.dataset_examples && data.dataset_examples.length > 0) {
                        data.dataset_examples.forEach(item => {
                            const li = document.createElement("li");
                            li.textContent = item.type + " | " + item.address + " | " + item.date;
                            dataExamples.appendChild(li);

                            if (item.latitude && item.longitude) {
                                const marker = L.marker([item.latitude, item.longitude])
    .addTo(residentMap)
                                    .bindPopup(item.type + " | " + item.address);
                                residentMarkers.push(marker);
                            }
                        });
                    } else {
                        const li = document.createElement("li");
                        li.textContent = "No related city data found.";
                        dataExamples.appendChild(li);
                    }

                    if (residentMarkers.length > 0) {
                        const group = new L.featureGroup(residentMarkers);
                        residentMap.fitBounds(group.getBounds().pad(0.2));
                    } else {
                        residentMap.setView([32.3668, -86.3000], 13);
                    }
                }
            </script>
        </body>
    </html>
    """