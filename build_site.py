from pathlib import Path
import pandas as pd
import json

# Read the latest scraped data file
data_path = Path(__file__).parent / "data.csv"
if not data_path.exists():
    df = pd.DataFrame({
        "Faculty": ["Test Faculty"],
        "Journal Name": ["Test Journal"],
        "Article Name": ["Test Title"],
        "Publication Year": ["2026"],
        "ABDC Rating": ["Unrated"],
        "Abstract": [""]
    })
else:
    df = pd.read_csv(data_path)

# --- Clean data text structures safely ---
if "Publication Year" in df.columns:
    df["Publication Year"] = df["Publication Year"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["Publication Year"] = df["Publication Year"].replace("nan", "")

# Convert Abstract column into safe clickable HTML link syntax
if "Abstract" in df.columns:
    df['Abstract'] = df['Abstract'].apply(
        lambda x: f'<a href="{x}" target="_blank">View Abstract</a>' if pd.notnull(x) and str(x).startswith('http') else ""
    )

# --- 1. Generate Main Publications Table Rows ---
df_table = df.copy()
df_table.insert(0, "#", range(1, len(df_table) + 1))

main_table_rows = ""
for _, row in df_table.iterrows():
    main_table_rows += "<tr>"
    main_table_rows += f"<td>{row.get('#', '')}</td>"
    main_table_rows += f"<td>{row.get('Faculty', '')}</td>"
    main_table_rows += f"<td>{row.get('Journal Name', '')}</td>"
    main_table_rows += f"<td>{row.get('Article Name', '')}</td>"
    main_table_rows += f"<td>{row.get('Publication Year', '')}</td>"
    main_table_rows += f"<td><span class='badge-rating'>{row.get('ABDC Rating', 'Unrated')}</span></td>"
    main_table_rows += f"<td>{row.get('Abstract', '')}</td>"
    main_table_rows += "</tr>"

# --- 2. Generate Faculty Summary Table Rows ---
summary_rows = ""
if "Faculty" in df.columns:
    all_individual_faculty = []
    for faculty_entry in df['Faculty'].dropna():
        authors = [author.strip() for author in str(faculty_entry).split(',')]
        all_individual_faculty.extend(authors)
        
    faculty_series = pd.Series(all_individual_faculty)
    faculty_counts = faculty_series.value_counts().reset_index()
    faculty_counts.columns = ['Faculty Member', 'Total Publications']
    
    for _, row in faculty_counts.iterrows():
        if not row['Faculty Member']:
            continue
        summary_rows += "<tr>"
        summary_rows += f"<td>{row['Faculty Member']}</td>"
        summary_rows += f"<td><strong>{row['Total Publications']}</strong></td>"
        summary_rows += "</tr>"

# --- 3. Calculate Grouped Data metrics for Chart.js ---
df['ABDC Rating'] = df['ABDC Rating'].fillna('Unrated').astype(str).str.strip()
df['Is_ABDC_Rated'] = df['ABDC Rating'].str.upper() != 'UNRATED'

# Ensure years are processed as numeric safely
df_clean_years = df.dropna(subset=['Publication Year']).copy()
df_clean_years['Clean_Year'] = pd.to_numeric(df_clean_years['Publication Year'], errors='coerce')
df_clean_years = df_clean_years.dropna(subset=['Clean_Year'])

yearly_grouped = df_clean_years.groupby('Clean_Year').agg(
    Total=('Article Name', 'count'),
    Rated=('Is_ABDC_Rated', 'sum')
).sort_index()

if not yearly_grouped.empty:
    min_year = int(yearly_grouped.index.min())
    max_year = int(yearly_grouped.index.max())
    total_papers = int(yearly_grouped['Total'].sum())
    total_abdc = int(yearly_grouped['Rated'].sum())
    
    chart_title = f"Number of Papers Published, {min_year} - {max_year} (total = {total_papers}), [total ABDC journal = {total_abdc}]"
    chart_labels = [str(int(yr)) for yr in yearly_grouped.index]
    chart_data_total = [int(val) for val in yearly_grouped['Total'].values]
    chart_data_rated = [int(val) for val in yearly_grouped['Rated'].values]
else:
    chart_title = "No Publication Data Available"
    chart_labels = []
    chart_data_total = []
    chart_data_rated = []

# --- 4. Build HTML layout using clean replacement tokens instead of f-strings ---
html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>School of Business Faculty Research</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        body { font-family: "Inter", sans-serif; background-color: #f8f9fa; color: #333; padding: 40px 20px; margin: 0; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        h1 { color: #1a365d; border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; margin-top: 0; margin-bottom: 30px; }
        h2 { color: #2c5282; margin-top: 40px; margin-bottom: 20px; font-size: 1.4em; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; }
        .table-container { overflow-x: auto; margin-bottom: 40px; }
        table { width: 100%; border-collapse: collapse; min-width: 800px; margin-bottom: 10px; }
        .summary-table { min-width: 300px; max-width: 500px; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #e2e8f0; vertical-align: top; }
        th { background-color: #ebf8ff; color: #2b6cb0; font-weight: 600; }
        tr:hover { background-color: #f7fafc; }
        a { color: #3182ce; text-decoration: none; font-weight: 500; }
        a:hover { text-decoration: underline; }
        .badge-rating { background-color: #edf2f7; color: #4a5568; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 0.85em; }
        .chart-container { max-width: 850px; margin: 30px auto; position: relative; height: 380px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>School of Business Faculty Published Papers</h1>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th style="width: 40px;">#</th>
                        <th style="width: 180px;">Faculty</th>
                        <th style="width: 220px;">Journal Name</th>
                        <th>Article Title</th>
                        <th style="width: 80px;">Year</th>
                        <th style="width: 100px;">ABDC</th>
                        <th style="width: 120px;">Link</th>
                    </tr>
                </thead>
                <tbody>
                    __MAIN_TABLE_ROWS__
                </tbody>
            </table>
        </div>
        
        <hr style="border: 0; border-top: 2px solid #e2e8f0; margin: 40px 0;">
        
        <h2>Number of Publications 2022-2026</h2>
        <div class="table-container">
            <table class="summary-table">
                <thead>
                    <tr>
                        <th>Faculty Member</th>
                        <th style="width: 150px;">Total Publications</th>
                    </tr>
                </thead>
                <tbody>
                    __SUMMARY_ROWS__
                </tbody>
            </table>
        </div>

        <hr style="border: 0; border-top: 2px solid #e2e8f0; margin: 40px 0;">
        
        <div class="chart-container">
            <canvas id="publicationChart"></canvas>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        const ctx = document.getElementById('publicationChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: __CHART_LABELS__,
                datasets: [
                    {
                        label: 'Total Publications',
                        data: __CHART_DATA_TOTAL__,
                        backgroundColor: 'rgba(49, 130, 206, 0.75)',
                        borderColor: 'rgba(43, 108, 176, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'ABDC Rated (A*, A, B, C)',
                        data: __CHART_DATA_RATED__,
                        backgroundColor: 'rgba(49, 151, 149, 0.75)',
                        borderColor: 'rgba(35, 78, 82, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: __CHART_TITLE__,
                        font: { size: 15, weight: 'bold', family: "'Inter', sans-serif" },
                        color: '#1a365d',
                        padding: { bottom: 20 }
                    },
                    legend: {
                        display: true,
                        position: 'top',
                        labels: { font: { family: "'Inter', sans-serif", weight: '500' } }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1, font: { family: "'Inter', sans-serif" } }
                    },
                    x: {
                        ticks: { font: { family: "'Inter', sans-serif" } }
                    }
                }
            }
        });
    </script>
</body>
</html>
"""

# Perform safe manual updates to injection tokens
html_content = html_template.replace("__MAIN_TABLE_ROWS__", main_table_rows)
html_content = html_content.replace("__SUMMARY_ROWS__", summary_rows)
html_content = html_content.replace("__CHART_TITLE__", json.dumps(chart_title))
html_content = html_content.replace("__CHART_LABELS__", json.dumps(chart_labels))
html_content = html_content.replace("__CHART_DATA_TOTAL__", json.dumps(chart_data_total))
html_content = html_content.replace("__CHART_DATA_RATED__", json.dumps(chart_data_rated))

# Save out to public-facing docs folder context
output_dir = Path(__file__).parent / "docs"
output_dir.mkdir(exist_ok=True)

with open(output_dir / "index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Static index.html site built successfully inside /docs folder.")
