import pandas as pd
import csv

negative_examples = [
    ("New Jersey", "Passaic", "Paterson Public School District", "C-"),
    ("New Jersey", "Camden", "Camden City School District", "C-"),
    ("New Jersey", "Essex", "Newark Public School District", "C+"),
    ("New Jersey", "Hudson", "Jersey City Public Schools", "B-"),
    ("New Jersey", "Essex", "Irvington Public School District", "D+"),
    ("New Jersey", "Union", "Plainfield Public School District", "D+"),
    ("New Jersey", "Monmouth", "Asbury Park School District", "C"),
    ("New Jersey", "Bergen", "Hackensack School District", "C"),
    ("New Jersey", "Union", "Linden Public School District", "C+"),
    ("New Jersey", "Union", "Rahway Public School District", "B-"),
    ("New Jersey", "Middlesex", "Carteret Public School District", "C"),
    ("New Jersey", "Middlesex", "Perth Amboy Public School District", "C"),
    ("New Jersey", "Middlesex", "New Brunswick Public Schools", "C-"),
    ("New Jersey", "Atlantic", "Pleasantville Public Schools", "C-"),
    ("New Jersey", "Cumberland", "Vineland Public School District", "C"),
    ("New York", "Nassau", "Freeport Union Free School District", "B+"),
    ("New York", "Nassau", "Uniondale Union Free School District", "B-"),
    ("New York", "Nassau", "Hempstead Union Free School District", "D+"),
    ("New York", "Nassau", "Roosevelt Union Free School District", "C+"),
    ("New York", "Suffolk", "Copiague Union Free School District", "C+"),
    ("New York", "Suffolk", "South Country Central School District", "B-"),
    ("New York", "Suffolk", "Amityville Union Free School District", "B-"),
    ("New York", "Suffolk", "Brentwood Union Free School District", "B-"),
    ("New York", "Suffolk", "Central Islip Union Free School District", "C"),
    ("New York", "Suffolk", "Wyandanch Union Free School District", "B-"),
    ("New York", "Westchester", "Peekskill City School District", "C+"),
    ("New York", "Westchester", "Yonkers City School District", "B"),
    ("New York", "Westchester", "New Rochelle City School District", "B"),
    ("New York", "Rockland", "East Ramapo Central School District", "C-"),
    ("Connecticut", "Fairfield", "Danbury Public Schools", "C+"),
    ("Connecticut", "Fairfield", "Bridgeport Public Schools", "C-"),
    ("Connecticut", "Fairfield", "Stratford School District", "B"),
    ("Connecticut", "Fairfield", "Norwalk School District", "B+"),
    ("Connecticut", "Fairfield", "Stamford Public Schools", "B")
]

csv_file = "commutable_districts.csv"

# Read existing to avoid duplicates
df_existing = pd.read_csv(csv_file)
existing_names = set(df_existing['School District Name'])

new_rows = []
for state, county, name, grade in negative_examples:
    if name not in existing_names:
        new_rows.append([state, county, name, grade, "", ""])

if new_rows:
    with open(csv_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(new_rows)
    print(f"Appended {len(new_rows)} new negative examples to the dataset.")
else:
    print("No new examples to append.")
