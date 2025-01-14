import pandas as pd
from faker import Faker
import random
import os
fake = Faker()

rows = 25
data = {
    "Exam_SEAT_NO": [random.randint(100000, 999999) for _ in range(rows)],
    "REG_NO": [random.randint(10000, 99999) for _ in range(rows)],
    "SUR_NAME": [fake.last_name() for _ in range(rows)],
    "FIRST_NAME": [fake.first_name() for _ in range(rows)],
    "LAST_NAME": [fake.last_name() for _ in range(rows)],
    "MOTHER_NAME": [fake.first_name_female() for _ in range(rows)],
    "DATE": [fake.date_this_decade() for _ in range(rows)],
    "SMART_CARD_NO": [random.randint(1000000000, 9999999999) for _ in range(rows)],
    "EXAM_HELD_IN": [fake.month_name() for _ in range(rows)],
    "BRANCH_NAME": [fake.random_element(elements=("Computer Engineering", "Information Technology", "Mechanical Engineering", "Electrical Engineering", "Electronics and Telecommunication")) for _ in range(rows)]
}

df = pd.DataFrame(data)
SEM_COUNT:int = 10
SUB_COUNT:int = 20

# Adding Subject columns
subjects = [f"Subject_{i}_Sem_{sem}" for sem in range(1, SEM_COUNT) for i in range(1, SUB_COUNT)]
for subject in subjects:
    df[subject] = [random.randint(0, 100) for _ in range(rows)]

# Adding Total marks for each semester
for sem in range(1, SEM_COUNT):
    sem_subjects = [f"Subject_{i}_Sem_{sem}" for i in range(1, SUB_COUNT)]
    df[f"Total_Sem_{sem}"] = df[sem_subjects].sum(axis=1)

# Save updated DataFrame to Excel
final_file_path = os.path.dirname(__file__) + "/sample.xlsx"
df.to_excel(final_file_path, index=False)

print(final_file_path)
