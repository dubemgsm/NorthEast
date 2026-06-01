import pandas as pd
import json
import holidays
from datetime import timedelta

# Load Data
stats_csv = "data/clean/bay_lga_vulnerability_stats.csv"
conflict_csv = "data/data/conflict_data_nga.csv"

df = pd.read_csv(stats_csv)
conflict_df = pd.read_csv(conflict_csv, low_memory=False)

# --- 1. Existing Analysis (Education Gap) ---
df['edu_access_gap'] = df['Population'] / (df['Open_Schools'] + 1)

top_10_gap = df.nlargest(10, 'edu_access_gap')[['LGA', 'State', 'edu_access_gap']]
chart1_labels = [f"{row['LGA']} ({row['State']})" for _, row in top_10_gap.iterrows()]
chart1_data = top_10_gap['edu_access_gap'].tolist()

top_20_pop = df.nlargest(20, 'Population')[['LGA', 'State', 'Population', 'Open_Schools', 'Closed_Schools']]
chart2_labels = [f"{row['LGA']} ({row['State']})" for _, row in top_20_pop.iterrows()]
chart2_pop = top_20_pop['Population'].tolist()
chart2_open = top_20_pop['Open_Schools'].tolist()
chart2_closed = top_20_pop['Closed_Schools'].tolist()

scatter_data = []
for _, row in df.iterrows():
    scatter_data.append({
        'x': row['Conflict_Events'],
        'y': row['Open_Schools'],
        'r': max(row['Population'] / 25000, 3),
        'label': f"{row['LGA']} ({row['State']})"
    })

# --- 2. New Conflict Trend Analysis ---
bay_states = ['Borno state', 'Adamawa state', 'Yobe state']
bay_conflicts = conflict_df[conflict_df['adm_1'].isin(bay_states)].copy()
bay_conflicts['date_start'] = pd.to_datetime(bay_conflicts['date_start'], errors='coerce')
bay_conflicts = bay_conflicts.dropna(subset=['date_start'])
bay_conflicts['year'] = bay_conflicts['date_start'].dt.year
bay_conflicts['month'] = bay_conflicts['date_start'].dt.month
bay_conflicts['date_only'] = bay_conflicts['date_start'].dt.date

min_year = int(bay_conflicts['year'].min())
max_year = int(bay_conflicts['year'].max())

ng_holidays = holidays.CountryHoliday('NG', years=range(min_year, max_year + 1))

holiday_dates = {}
for date, name in sorted(ng_holidays.items()):
    holiday_dates[date] = name

additional_dates = {}
for date, name in holiday_dates.items():
    if 'eid al-fitr' in name.lower() or 'id el fitr' in name.lower():
        ramadan_start = date - timedelta(days=29)
        additional_dates[ramadan_start] = 'Start of Ramadan'
holiday_dates.update(additional_dates)

def get_holiday_offset(event_date):
    for offset in range(-3, 4):
        check_date = event_date + timedelta(days=offset)
        if check_date in holiday_dates:
            return offset, holiday_dates[check_date]
    return None, None

bay_conflicts['holiday_info'] = bay_conflicts['date_only'].apply(get_holiday_offset)
bay_conflicts['offset'] = bay_conflicts['holiday_info'].apply(lambda x: x[0])
bay_conflicts['holiday_name'] = bay_conflicts['holiday_info'].apply(lambda x: x[1])

# Data for Chart 4: Monthly Seasonality
monthly_counts = bay_conflicts.groupby('month').size()
month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
chart4_data = [int(monthly_counts.get(i, 0)) for i in range(1, 13)]

# Data for Chart 5: Days to Holiday
offset_counts = bay_conflicts['offset'].value_counts().sort_index()
chart5_labels = ['3 Days Before', '2 Days Before', '1 Day Before', 'On the Day', '1 Day After', '2 Days After', '3 Days After']
chart5_data = [int(offset_counts.get(i, 0)) for i in range(-3, 4)]

# Data for Chart 6: Top Holidays
top_holidays = bay_conflicts['holiday_name'].value_counts().head(5)
chart6_labels = top_holidays.index.tolist()
chart6_data = [int(x) for x in top_holidays.values.tolist()]


# --- HTML Template ---
html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deep Dive: BAY States Analysis</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; color: #333; }}
        h1, h2 {{ text-align: center; color: #2c3e50; }}
        h2 {{ margin-top: 50px; border-bottom: 2px solid #ccc; padding-bottom: 10px; max-width: 1200px; margin-left: auto; margin-right: auto; }}
        .nav-btn {{ display: inline-block; margin-bottom: 20px; padding: 10px 15px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; transition: background 0.3s; }}
        .nav-btn:hover {{ background-color: #218838; }}
        .dashboard {{ display: grid; grid-template-columns: 1fr; gap: 20px; max-width: 1200px; margin: 0 auto; }}
        .chart-container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .chart-wrapper {{ position: relative; height: 400px; width: 100%; }}
        @media (min-width: 900px) {{
            .dashboard {{ grid-template-columns: 1fr 1fr; }}
            .full-width {{ grid-column: 1 / -1; }}
        }}
    </style>
</head>
<body>

    <a href="index.html" class="nav-btn">🔙 Back to Map</a>
    
    <h1>Deep Dive: Education & Vulnerability Analysis</h1>
    
    <h2>Section 1: Educational Infrastructure</h2>
    <div class="dashboard">
        <div class="chart-container full-width">
            <h3>1. Top 10 LGAs by Education Access Gap</h3>
            <div class="chart-wrapper" style="height: 350px;"><canvas id="gapChart"></canvas></div>
        </div>
        <div class="chart-container full-width">
            <h3>2. Population vs. Number of Schools</h3>
            <div class="chart-wrapper" style="height: 450px;"><canvas id="popSchoolChart"></canvas></div>
        </div>
        <div class="chart-container full-width">
            <h3>3. Conflict Intensity vs. School Availability</h3>
            <div class="chart-wrapper" style="height: 500px;"><canvas id="scatterChart"></canvas></div>
        </div>
    </div>

    <h2>Section 2: Predictive Conflict Patterns</h2>
    <p style="text-align:center; max-width:800px; margin:0 auto 30px;">
        Analysis of historical conflict events (2003-2024) in the BAY states against public and religious holidays to identify predictive patterns.
    </p>

    <div class="dashboard">
        <div class="chart-container">
            <h3>4. Monthly Seasonality (All Years)</h3>
            <p><small>January shows the highest peak, correlating with the dry season which increases mobility.</small></p>
            <div class="chart-wrapper" style="height: 300px;"><canvas id="monthChart"></canvas></div>
        </div>

        <div class="chart-container">
            <h3>5. Tactical Timing (Proximity to Holidays)</h3>
            <p><small>Analyzes the 7-day window around events. Spikes are visible 3 days <b>before</b> holidays.</small></p>
            <div class="chart-wrapper" style="height: 300px;"><canvas id="timingChart"></canvas></div>
        </div>

        <div class="chart-container full-width">
            <h3>6. Top 5 High-Risk Holidays / Events</h3>
            <p><small>The specific holidays and periods that see the highest concentration of conflict in their 7-day window.</small></p>
            <div class="chart-wrapper" style="height: 350px;"><canvas id="holidayChart"></canvas></div>
        </div>
    </div>

    <script>
        // --- Infrastructure Charts ---
        new Chart(document.getElementById('gapChart'), {{
            type: 'bar',
            data: {{ labels: {json.dumps(chart1_labels)}, datasets: [{{ label: 'People per Open School', data: {json.dumps(chart1_data)}, backgroundColor: 'rgba(220, 53, 69, 0.7)' }}] }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});

        new Chart(document.getElementById('popSchoolChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(chart2_labels)},
                datasets: [
                    {{ label: 'Population', data: {json.dumps(chart2_pop)}, backgroundColor: 'rgba(54, 162, 235, 0.6)', yAxisID: 'y' }},
                    {{ label: 'Open Schools', data: {json.dumps(chart2_open)}, type: 'line', borderColor: '#28a745', yAxisID: 'y1' }}
                ]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ position: 'left' }}, y1: {{ position: 'right' }} }} }}
        }});

        new Chart(document.getElementById('scatterChart'), {{
            type: 'bubble',
            data: {{ datasets: [{{ label: 'LGAs (Size = Population)', data: {json.dumps(scatter_data)}, backgroundColor: 'rgba(253, 126, 20, 0.6)' }}] }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});

        // --- Conflict Pattern Charts ---
        new Chart(document.getElementById('monthChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps(month_labels)},
                datasets: [{{ label: 'Total Historical Conflicts', data: {json.dumps(chart4_data)}, borderColor: '#6f42c1', backgroundColor: 'rgba(111, 66, 193, 0.2)', fill: true, tension: 0.3 }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});

        new Chart(document.getElementById('timingChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(chart5_labels)},
                datasets: [{{ 
                    label: 'Conflict Events', 
                    data: {json.dumps(chart5_data)}, 
                    backgroundColor: ['#dc3545', '#ffc107', '#ffc107', '#28a745', '#17a2b8', '#17a2b8', '#17a2b8'] 
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
        }});

        new Chart(document.getElementById('holidayChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(chart6_labels)},
                datasets: [{{ label: 'Conflict Events (Within 7-day window)', data: {json.dumps(chart6_data)}, backgroundColor: '#6610f2' }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, indexAxis: 'y' }}
        }});
    </script>
</body>
</html>
"""

with open("deep_dive.html", "w") as f:
    f.write(html_template)
print("Deep Dive HTML generated at deep_dive.html")
