from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from shiny import App, ui, render

# Read the uploaded CSV file from the repository
data_path = Path(__file__).parent / "data.csv"
df = pd.read_csv(data_path)

# --- Clean the Publication Year decimal issue so it doesn't break the HTML render ---
if "Publication Year" in df.columns:
    df["Publication Year"] = df["Publication Year"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["Publication Year"] = df["Publication Year"].replace("nan", "")

# Convert the "Abstract" column into clickable HTML links
if "Abstract" in df.columns:
    df['Abstract'] = df['Abstract'].apply(
        lambda x: f'<a href="{x}" target="_blank">View Abstract</a>' if pd.notnull(x) and str(x).startswith('http') else x
    )

# Create a copy for the table display to add the row index safely
df_table = df.copy()
df_table.insert(0, "#", range(1, len(df_table) + 1))

# Generate the clean HTML table structure
html_table = df_table.to_html(classes="table table-striped table-hover", index=False, escape=False)

app_ui = ui.page_fluid(
    ui.panel_title("School of Business Faculty Published Papers"),
    
    # 1. The Faculty Papers Table
    ui.div(
        ui.HTML(html_table),
        style="margin-top: 20px; overflow-x: auto;"
    ),
    
    # 2. Divider and Space for the Bar Chart at the Bottom
    ui.hr(style="margin-top: 40px; margin-bottom: 20px;"),
    ui.div(
        ui.output_plot("publication_chart"),
        style="display: flex; justify-content: center; margin-bottom: 40px;"
    )
)

def server(input, output, session):
    
    @output
    @render.plot
    def publication_chart():
        # Read a fresh copy of the data frame column for math calculations
        raw_years = pd.to_numeric(df['Publication Year'], errors='coerce').dropna().astype(int)
        
        # Count and sort chronological publication years
        year_counts = raw_years.value_counts().sort_index()
        
        if year_counts.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "No Publication Data Available", ha='center', va='center', fontsize=14)
            return fig

        # Extract dynamic values for your title specifications
        min_year = year_counts.index.min()
        max_year = year_counts.index.max()
        total_papers = year_counts.sum()
        
        # Build out the visualization structure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Generate bars
        bars = ax.bar(year_counts.index.astype(str), year_counts.values, color='skyblue', edgecolor='black')
        
        # Add labels directly above each bar height position
        ax.bar_label(bars, padding=3, fontsize=15)
        
        # Title string formatting 
        title_text = f"Number of Papers Published, {min_year} - {max_year} (total = {total_papers})"
        ax.set_title(title_text, fontsize=14, fontweight='bold')
        
        # Axes Labels and Scaling Controls
        ax.set_xlabel('Publication Year', fontsize=12)
        ax.set_ylabel('Number of Papers', fontsize=12)
        ax.set_ylim(0, 15)
        
        # Grid line alignments and layout sweeps
        ax.tick_params(axis='x', rotation=45)
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        fig.tight_layout()
        
        return fig

app = App(app_ui, server)
