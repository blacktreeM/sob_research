# f64115a7dae86ae150769602280d8e7f 
# 774a6cccb40fa1ec293635a974d43b82
import time
import requests
import pandas as pd
from selectolax.parser import HTMLParser
import re
import os
import shutil

def scrape_entire_scholar_profile(api_key, profile_id, faculty_name):
    publications = []
    cstart = 0       # Starting index (0 means article #1)
    pagesize = 100   # Max allowed articles per request batch
    
    print(f"\nFetching ALL data via proxy tunnel for {faculty_name}...")
    
    while True:
        # Construct a URL that forces Google to give us 100 articles at a time
        scholar_url = f"https://scholar.google.com/citations?user={profile_id}&hl=en&cstart={cstart}&pagesize={pagesize}"
        
        proxy_url = "http://api.scraperapi.com"
        payload = {
            'api_key': api_key,
            'url': scholar_url,
            'keep_headers': 'true'
        }
        
        try:
            # Short pause between page chunks to remain undetected
            time.sleep(2) 
            response = requests.get(proxy_url, params=payload, timeout=30)
            
            if response.status_code != 200:
                print(f"  --> Proxy error on batch starting at {cstart}: Status {response.status_code}")
                break
                
            html = response.text
            tree = HTMLParser(html)
            rows = tree.css("tr.gsc_a_tr")
            
            # If no rows are returned, we have reached the end of their publication list
            if not rows:
                break
                
            print(f"  --> Found articles {cstart + 1} to {cstart + len(rows)}...")
            
            for row in rows:
                title_element = row.css_first("a.gsc_a_at")
                article_name = title_element.text(strip=True) if title_element else None
                
                relative_link = title_element.attributes.get("href") if title_element else ""
                article_link = f"https://scholar.google.com{relative_link}" if relative_link else None
                
                # --- FIXED PARSING LOGIC TO PRESERVE COMMAS ---
                details = row.css("div.gs_gray")
                if len(details) >= 2:
                    journal_text = details[1].text(strip=True)
                    
                    # Instead of breaking on every comma, extract the text up to the trailing volume metrics
                    # 1. Clear any trailing issue parenthesis like (4) or (2-3)
                    s = re.sub(r'\s*\([^)]*\)\s*$', '', journal_text)
                    # 2. Clear trailing volume descriptions like "vol. 23"
                    s = re.sub(r'[\s,]+\b(vol|vols|issue|no|v|part|pt)\b\.?\s*\d+.*$', '', s, flags=re.IGNORECASE)
                    # 3. Clear isolated trailing volume digits (leaving internal list words completely alone)
                    s = re.sub(r'[\s,]+\d+\s*$', '', s)
                    
                    journal_name = s.strip()
                else:
                    journal_name = None
                # ----------------------------------------------
                    
                year_element = row.css_first("td.gsc_a_y span.gsc_a_h")
                pub_year = year_element.text(strip=True) if year_element else None
                
                publications.append({
                    "Faculty Name": faculty_name,
                    "Article Name": article_name,
                    "Journal Name": journal_name,
                    "Abstract": article_link,
                    "Publication Year": pub_year
                })
            
            # If Google returns fewer rows than our requested pagesize, it means we hit the final page
            if len(rows) < pagesize:
                break
                
            # Shift the starting pointer forward by 100 for the next loop iteration
            cstart += pagesize

        except Exception as e:
            print(f"  --> Network or parsing error during batch execution: {e}")
            break
            
    print(f"  --> Success! Total extracted for {faculty_name}: {len(publications)} articles.")
    return publications

# --- Configuration ---
SCRAPERAPI_KEY = "774a6cccb40fa1ec293635a974d43b82" # "f64115a7dae86ae150769602280d8e7f"

faculty_list = [
    {"name": "Masa Kuroki", "id": "Q6SsuLgAAAAJ"},
    {"name": "Sidd Bhambhwani", "id": "xpOekbMAAAAJ"},
    {"name": "Roc Huang", "id": "Jo7y9I8AAAAJ"},
    {"name": "Kevin Mason", "id": "XEpHGWAAAAAJ"},
    {"name": "John Narcum", "id": "0pA9ZlgAAAAJ"},
    {"name": "Stephen Jones", "id": "N_pT9awAAAAJ"},
    {"name": "Kuldeep Singh", "id": "k3uL__cAAAAJ"},
    {"name": "Wan Wei", "id": "8OlELbcAAAAJ"},
    {"name": "Aditya Limaye", "id": "0o-hM4oAAAAJ"},
    {"name": "Loretta Smith", "id": "4AEZrqMAAAAJ"},
    {"name": "David Pumphrey", "id": "BvVBHSAAAAAJ"},
    {"name": "Matt Brown", "id": "LZacl3wAAAAJ"}
]

# --- Main Processing Loop ---
all_data = []
for faculty in faculty_list:
    faculty_data = scrape_entire_scholar_profile(SCRAPERAPI_KEY, faculty["id"], faculty["name"])
    all_data.extend(faculty_data)
    time.sleep(3) # Brief buffer gap between switching faculty profiles

# Compile into data frame
df = pd.DataFrame(all_data)

if not df.empty:
    df.to_csv("faculty_publications.csv", index=False)
    print("\nExtraction fully complete! Saved to 'faculty_publications.csv'")
else:
    print("\nExecution finished, but output table is empty.")
# ---------------------------------------------------------
# Part 1: Filter Publications (2022 or Later)
# ---------------------------------------------------------
print("Filtering data matrix...")
df['Publication Year'] = pd.to_numeric(df['Publication Year'], errors='coerce')
df_filtered = df[df['Publication Year'] >= 2022].copy()

# ---------------------------------------------------------
# Part 2: Extract Clean Journal Names & Drop Blanks
# ---------------------------------------------------------
print("Standardizing journal columns...")

def clean_journal_name(text):
    if pd.isna(text):
        return ""
    s = str(text).strip()
    # Strip any trailing publication noise (volumes, issues, parentheses)
    split_pattern = r'[\s,]+(\d+|\b(vol|vols|issue|no|v|part|pt)\b\.?\s*\d+.*|\()'
    match = re.search(split_pattern, s, flags=re.IGNORECASE)
    if match:
        s = s[:match.start()]
    return s.strip()

df_filtered['Journal Name'] = df_filtered['Journal Name'].apply(clean_journal_name)

# Drop entries where Journal Name is NaN or completely empty
df_filtered = df_filtered[df_filtered['Journal Name'].notna() & (df_filtered['Journal Name'] != "")]

# ---------------------------------------------------------
# Part 3: Deduplicate and Merge Coauthors Into a Single Row
# ---------------------------------------------------------
print("Consolidating coauthored publications...")

# Create normalized keys specifically to group duplicates accurately (ignoring casing/whitespace)
df_filtered['_norm_title'] = df_filtered['Article Name'].astype(str).str.lower().str.strip()
df_filtered['_norm_journal'] = df_filtered['Journal Name'].astype(str).str.lower().str.strip()

# Group by the normalized fields to merge names, while pulling the first available match for other metrics
df_grouped = df_filtered.groupby(['_norm_title', '_norm_journal']).agg({
    'Faculty Name': lambda x: ", ".join(sorted(list(set(x.dropna().astype(str))))),
    'Article Name': 'first',
    'Journal Name': 'first',
    'Abstract': 'first',
    'Publication Year': 'first'
}).reset_index(drop=True)

# Rename the merged list column to "Faculty"
df_grouped = df_grouped.rename(columns={'Faculty Name': 'Faculty'})
df_filtered = df_grouped

# ---------------------------------------------------------
# Part 4: Fetch and Parse ABDC Reference Sheet
# ---------------------------------------------------------
print("Downloading latest ABDC Master Journal List...")
abdc_url = "https://abdc.edu.au/wp-content/uploads/2026/03/ABDC-JQL-2025-v1-260326.xlsx"

try:
    abdc_df = pd.read_excel(abdc_url, header=7)
    abdc_df.columns = abdc_df.columns.astype(str).str.strip()
    
    title_col = 'Journal Title'
    rating_col = '2025 rating'
    
    abdc_clean = abdc_df[[title_col, rating_col]].copy()
    abdc_clean.columns = ['ABDC_Journal_Title', 'Assigned_Rating']
    
    # ---------------------------------------------------------
    # Part 5: Match-Key Normalization Engine (Exact matches except for "The")
    # ---------------------------------------------------------
    def build_strict_key(series):
        return (series.astype(str)
                .str.lower()
                # 1. Strip leading "the ", "a ", "an " structural articles
                .str.replace(r'^(the|a|an)\s+', '', regex=True)
                # 2. Clear punctuation and collapse spaces to make string comparisons absolute
                .str.replace(r'[^\w\s]', '', regex=True)
                .str.replace(r'\s+', ' ', regex=True)
                .str.strip())

    df_filtered['match_key'] = build_strict_key(df_filtered['Journal Name'])
    abdc_clean['match_key'] = build_strict_key(abdc_clean['ABDC_Journal_Title'])
    
    # Drop duplicates in lookup table to preserve structure geometry
    abdc_clean = abdc_clean.drop_duplicates(subset=['match_key'])
    
    # ---------------------------------------------------------
    # Part 6: Execute Left Merge (Strict Equality Only)
    # ---------------------------------------------------------
    print("Aligning rankings via strict equality map...")
    df_final = pd.merge(df_filtered, abdc_clean[['match_key', 'Assigned_Rating']], on='match_key', how='left')
    
    # Clean up column outputs and map missing keys cleanly to "Unrated"
    df_final['ABDC Rating'] = df_final['Assigned_Rating'].fillna("Unrated")
    
    # Drop temporary processing metrics keys
    if 'Assigned_Rating' in df_final.columns:
        df_final = df_final.drop(columns=['Assigned_Rating'])
    df_final = df_final.drop(columns=['match_key'])
    
    # Sort chronologically by year descending
    df_final = df_final.sort_values(by='Publication Year', ascending=False)
    
    print(f"\nProcessing complete! Strictly rated and sorted {len(df_final)} publications.")
    df = df_final

except Exception as e:
    print(f"\nProcessing failure: {e}")
    df_filtered['ABDC Rating'] = "Unrated"
    df = df_filtered.sort_values(by='Publication Year', ascending=False)

# Save the raw data tracking file
df.to_csv("data.csv", index=False)
print("Data matrix updated.")
print("\nExtraction and data cleaning fully complete!")
