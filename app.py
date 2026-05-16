from pathlib import Path
import pandas as pd
from shiny import App, ui

# Read the uploaded CSV file from the repository
data_path = Path(__file__).parent / "data.csv"
df = pd.read_csv(data_path)
# Convert the "Abstract" column into clickable HTML links
if "Abstract" in df.columns:
    df['Abstract'] = df['Abstract'].apply(
        lambda x: f'<a href="{x}" target="_blank">View Abstract</a>' if pd.notnull(x) and str(x).startswith('http') else x
    )

# Add a row number column at the start (starting from 1)
df.insert(0, "#", range(1, len(df) + 1))

# Generate the clean HTML table structure
html_table = df.to_html(classes="table table-striped table-hover", index=False, escape=False)

app_ui = ui.page_fluid(
    ui.panel_title("School of Business Faculty Published Papers"),
    ui.div(
        ui.HTML(html_table),
        style="margin-top: 20px; overflow-x: auto;"
    )
)

def server(input, output, session):
    pass

app = App(app_ui, server)
