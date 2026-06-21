import csv

with open("/Users/joshuawilding/Downloads/Graded_Jobs_June2026.csv", "r") as f:
    reader = csv.DictReader(f)
    jobs = [row for row in reader if row.get("Work_Match_Score", "").isdigit()]
    jobs.sort(key=lambda x: int(x["Work_Match_Score"]), reverse=True)
    
    for i, j in enumerate(jobs[:5], 1):
        print(f"Top {i}: {j['title']} at {j['company']}")
        print(f"  Score: {j['Work_Match_Score']}")
        print(f"  Rationale: {j['Work_Rationale']}")
        print(f"  Qual: {j['Qualification_Probability']} - {j['Qualification_Rationale']}")
        print(f"  Comp: {j['Pessimistic_Comp_Band']}")
        print(f"  WLB: {j['WLB_Indicators']}")
        print(f"  URL: {j['url']}")
        print("-" * 40)
