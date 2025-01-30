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

subject_names = [
    "Advanced Theoretical and Practical Applications of Artificial Intelligence, Digital Logic Design, Computer Organization and Architecture, Generative Adversarial Networks, Cryptographic Security Systems, and Efficient Data Management Techniques for Modern Computing Environments",
    "Comprehensive Study of Secure and Efficient Data Processing Techniques Using Cryptographic Algorithms, Distributed Computing, and High-Performance Machine Learning Architectures for Scalable and Reliable Systems",
    "Innovative Approaches to Digital Signal Processing, Embedded Systems Design, and Optimization of Computer Vision Algorithms for Real-Time Applications in Edge and Cloud Computing",
    "Multidisciplinary Perspectives on Neural Network Architectures, Reinforcement Learning, and Explainable AI for Ethical and Responsible Artificial Intelligence Deployment in Various Industries",
    "Exploring the Synergy of Quantum Computing, Blockchain Technology, and AI-Driven Decision Making for Next-Generation Secure and Decentralized Computing Paradigms",
    "High-Speed Data Compression, Storage Optimization, and Secure Transmission Mechanisms for Large-Scale Cloud and IoT-Enabled Smart Environments",
    "Design and Analysis of Scalable Computational Models for AI-Based Systems with a Focus on Federated Learning, Privacy-Preserving Techniques, and Edge Computing Integration",
    "Comprehensive Exploration of Logic Gates, Finite State Machines, Microprocessor Architectures, and FPGA-Based System Design for High-Efficiency Computing Applications",
    "Advanced Concepts in Virtual Reality, Augmented Reality, and Haptic Feedback Systems for Next-Generation Human-Computer Interaction and Immersive Experience Design",
    "Cutting-Edge Research in Bioinformatics, Computational Biology, and the Application of AI in Genomics for Precision Medicine and Healthcare Innovation",
    "Theoretical Foundations and Practical Implementations of Cyber-Physical Systems, IoT Networks, and Autonomous Intelligent Systems for Smart Cities and Industry 4.0",
    "Exploring the Mathematical and Statistical Foundations of Machine Learning, Deep Learning, and Data Science for Predictive Analytics and Decision-Making",
    "Advancements in Optical Computing, Neuromorphic Engineering, and Photonic Circuit Design for Ultra-Fast Data Processing and Energy-Efficient AI Systems",
    "Development and Optimization of Parallel and Distributed Computing Architectures for Large-Scale Simulations, High-Performance Computing, and Cloud-Based AI Services",
    "Integration of Edge AI, 5G Technologies, and Next-Generation Wireless Networks for Real-Time Data Processing and Intelligent Decision-Making in Smart Environments",
]

df = pd.DataFrame(data)
SEM_COUNT:int = 8
SUB_COUNT:int = 20

# Adding Subject columns
subjects = [f"{i}_Sem_{sem}" for sem in range(1, SEM_COUNT) for i in subject_names]
for subject in subjects:
    df[subject] = [random.randint(0, 100) for _ in range(rows)]

# Adding Total marks for each semester
for sem in range(1, SEM_COUNT):
    sem_subjects = [f"{i}_Sem_{sem}" for i in subject_names]
    df[f"Total_Sem_{sem}"] = df[sem_subjects].sum(axis=1)

# Save updated DataFrame to Excel
final_file_path = os.path.dirname(__file__) + "/sample.xlsx"
df.to_excel(final_file_path, index=False)

print(final_file_path)
