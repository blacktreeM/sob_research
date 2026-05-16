import pandas as pd
import matplotlib.pyplot as plt

# --- Plotting Code ---
year_counts = df['Publication Year'].value_counts().sort_index()

min_year = year_counts.index.min()
max_year = year_counts.index.max()
total_papers = year_counts.sum()

fig, ax = plt.subplots(figsize=(10, 6))
bars = year_counts.plot(kind='bar', color='skyblue', edgecolor='black', ax=ax)
ax.bar_label(ax.containers[0], padding=3, fontsize=15)

title_text = f"Number of Papers Published, {min_year} - {max_year} (total = {total_papers})"
plt.title(title_text, fontsize=14, fontweight='bold')

plt.xlabel('Publication Year', fontsize=12)
plt.ylabel('Number of Papers', fontsize=12)
plt.xticks(rotation=45)  
plt.ylim(0, 15)
plt.grid(axis='y', linestyle='--', alpha=0.7)  
plt.tight_layout()  

# Optional: Save the figure automatically so it can be viewed in GitHub
plt.savefig('publication_trends.png', dpi=300)
plt.show()
