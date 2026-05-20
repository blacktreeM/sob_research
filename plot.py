import pandas as pd
import matplotlib.pyplot as plt

# --- Data Preparation ---
# Ensure the ABDC Rating column handles missing values and text consistently
df['ABDC Rating'] = df['ABDC Rating'].fillna('Unrated').astype(str).str.strip()

# Create a boolean helper column identifying if a paper is ABDC rated
df['Is_ABDC_Rated'] = df['ABDC Rating'].str.upper() != 'UNRATED'

# Group by year to get total counts and total rated counts
yearly_data = df.groupby('Publication Year').agg(
    Total_Publications=('Article Name', 'count'),
    ABDC_Rated_Publications=('Is_ABDC_Rated', 'sum')
).sort_index()

# Calculate metadata metrics for your updated title string
min_year = int(yearly_data.index.min())
max_year = int(yearly_data.index.max())
total_papers = int(yearly_data['Total_Publications'].sum())
total_abdc = int(yearly_data['ABDC_Rated_Publications'].sum())

# --- Plotting Code ---
fig, ax = plt.subplots(figsize=(12, 6))

# Plotting the side-by-side bars using a clean corporate color scheme
yearly_data.plot(
    kind='bar', 
    ax=ax, 
    width=0.75,
    color=['#3182ce', '#319795'], # Muted blue for Total, Teal for ABDC Rated
    edgecolor='black',
    linewidth=0.7
)

# Rename the legend categories nicely for the user interface
ax.legend(['Total Publications', 'ABDC Rated (A*, A, B, C)'], loc='upper left', frameon=True)

# Add numeric value labels directly on top of each bar structure
for container in ax.containers:
    ax.bar_label(container, padding=3, fontsize=12, fontweight='bold')

# Construct your updated custom metadata title string
title_text = f"Number of Papers Published, {min_year} - {max_year} (total = {total_papers}), [total ABDC journal = {total_abdc}]"
plt.title(title_text, fontsize=13, fontweight='bold', pad=20, color='#1a365d')

plt.xlabel('Publication Year', fontsize=12, labelpad=10)
plt.ylabel('Number of Papers', fontsize=12, labelpad=10)
plt.xticks(rotation=0)  # Rotated to 0 so the years read perfectly horizontally
plt.ylim(0, max(yearly_data['Total_Publications'].max() + 2, 15)) # Dynamic ceiling limit
plt.grid(axis='y', linestyle='--', alpha=0.5)  
plt.tight_layout()  

# Automatically save out file assets
plt.savefig('publication_trends.png', dpi=300)
plt.show()
