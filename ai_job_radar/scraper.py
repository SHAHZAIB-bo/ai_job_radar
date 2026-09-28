import sys
import os
import json
import pandas as pd
from jobspy import scrape_jobs

def main():
    if len(sys.argv) < 5:
        sys.exit(1)
        
    search_term = sys.argv[1]
    location = sys.argv[2]
    results_wanted = int(sys.argv[3])
    platforms = sys.argv[4].split(",")

    all_jobs = []
    
    # Try scraping each selected platform with error isolation
    for platform in platforms:
        try:
            jobs = scrape_jobs(
                site_name=[platform.strip()],
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                country_indeed='pakistan'
            )
            if jobs is not None and not jobs.empty:
                all_jobs.append(jobs)
        except Exception as e:
            print(f"Warning on platform {platform}: {e}")

    if all_jobs:
        combined_df = pd.concat(all_jobs, ignore_index=True)
        combined_df.to_json("jobs_temp.json", orient="records")
        print("SUCCESS")
    else:
        print("EMPTY")

if __name__ == "__main__":
    main()