"""
Legacy nickname registry used to bootstrap player_registry.csv.

The canonical source of truth is now player_registry.csv. This file remains only as
the migration input for bootstrap scripts and team-scoped nickname resolution.
"""

# Format: (nickname, full_name, role, is_overseas)
# role: BAT = Batter, BOWL = Bowler, AR = All-Rounder, WK = Wicketkeeper-Batter

PLAYER_REGISTRY = {
    # === CSK ===
    "Samson": ("Sanju Samson", "WK", False),
    "R Chahar": ("Rahul Chahar", "BOWL", False),
    "Henry": ("Matt Henry", "BOWL", True),
    "Kartik": ("Kartik Sharma", "BOWL", False),
    "prashant": ("Prashant Veer", "BOWL", False),
    "Dube": ("Shivam Dube", "AR", False),
    "Khaleel": ("Khaleel Ahmed", "BOWL", False),
    "MSD": ("MS Dhoni", "WK", False),
    "Noor": ("Noor Ahmad", "BOWL", True),
    "Anshul": ("Anshul Kamboj", "AR", False),
    "Gurjapneet": ("Gurjapneet Singh", "BOWL", False),
    "Brewis": ("Dewald Brevis", "BAT", True),
    "Sarfaraz": ("Sarfaraz Khan", "BAT", False),
    "Urvil": ("Urvil Patel", "BAT", False),
    "Overton": ("Jamie Overton", "AR", True),
    "Akeal": ("Akeal Hosein", "BOWL", True),
    "Ruturaj": ("Ruturaj Gaikwad", "BAT", False),
    "Mhatre": ("Ayush Mhatre", "BAT", False),
    "Ellis": ("Nathan Ellis", "BOWL", True),

    # === MI ===
    "HP": ("Hardik Pandya", "AR", False),
    "Jacks": ("Will Jacks", "AR", True),
    "Boult": ("Trent Boult", "BOWL", True),
    "Naman": ("Naman Dhir", "BAT", False),
    "Santner": ("Mitchell Santner", "AR", True),
    "Bumrah": ("Jasprit Bumrah", "BOWL", False),
    "Markande": ("Mayank Markande", "BOWL", False),
    "Rickelton": ("Ryan Rickelton", "BAT", True),
    "Allah": ("Allah Ghazanfar", "BOWL", True),
    "Izhar": ("Mohammad Izhar Khan", "BOWL", False),
    "QDK": ("Quinton de Kock", "WK", True),
    "Rutherford": ("Sherfane Rutherford", "BAT", True),
    "Thakur": ("Shardul Thakur", "AR", False),
    "Rohit": ("Rohit Sharma", "BAT", False),
    "Tilak": ("Tilak Varma", "BAT", False),
    "Sky": ("Suryakumar Yadav", "BAT", False),
    "Deepak": ("Deepak Chahar", "BOWL", False),
    "Ashwini": ("Ashwani Kumar", "BOWL", False),

    # === SRH ===
    "Klaasen": ("Heinrich Klaasen", "WK", True),
    "E Malinga": ("Eshan Malinga", "BOWL", False),
    "Abhishek": ("Abhishek Sharma", "AR", False),
    "Jaydev": ("Jaydev Unadkat", "BOWL", False),
    "Fuletra": ("Krains Fuletra", "BAT", False),
    "Harshal": ("Harshal Patel", "AR", False),
    "Cummins": ("Pat Cummins", "BOWL", True),
    "Aniket": ("Aniket Verma", "BAT", False),
    "NKR": ("Nitish Kumar Reddy", "AR", False),
    "Shivang": ("Shivang Kumar", "BAT", False),
    "Zeeshan": ("Zeeshan Ansari", "BOWL", False),
    "Head": ("Travis Head", "BAT", True),
    "Livingstone": ("Liam Livingstone", "AR", True),
    "Smaran": ("Smaran Ravichandran", "BAT", False),
    "Kishan": ("Ishan Kishan", "WK", False),
    "Mavi": ("Shivam Mavi", "BOWL", False),
    "Carse": ("Brydon Carse", "AR", True),
    "Salil": ("Salil Arora", "BAT", False),
    "Harsh Dubey": ("Harsh Dubey", "BOWL", False),

    # === RCB ===
    "Krunal": ("Krunal Pandya", "AR", False),
    "Hazelwood": ("Josh Hazlewood", "BOWL", True),
    "Jitesh": ("Jitesh Sharma", "WK", False),
    "Rasikh": ("Rasikh Dar", "BOWL", False),
    "Bethell": ("Jacob Bethell", "AR", True),
    "Salt": ("Phil Salt", "WK", True),
    "Romario": ("Romario Shepherd", "AR", True),
    "Patidar": ("Rajat Patidar", "BAT", False),
    "Dayal": ("Yash Dayal", "BOWL", False),
    "Mangesh": ("Mangesh Yadav", "BOWL", False),
    "David": ("Tim David", "BAT", True),
    "Suyash": ("Suyash Sharma", "BOWL", False),
    "Swapnil": ("Swapnil Singh", "AR", False),
    "VK": ("Virat Kohli", "BAT", False),
    "Bhuvi": ("Bhuvneshwar Kumar", "BOWL", False),
    "DDP": ("Devdutt Padikkal", "BAT", False),
    "Venky": ("Venkatesh Iyer", "AR", False),
    "Duffy": ("Jacob Duffy", "BOWL", True),

    # === PBKS ===
    "Marco": ("Marco Jansen", "AR", True),
    "Bartlett": ("Xavier Bartlett", "BOWL", True),
    "Musheer": ("Musheer Khan", "AR", False),
    "Dwarshuis": ("Ben Dwarshuis", "BOWL", True),
    "Cooper": ("Cooper Connolly", "AR", True),
    "Prabhsimran": ("Prabhsimran Singh", "WK", False),
    "Yash Thakur": ("Yash Thakur", "BOWL", False),
    "Wadhera": ("Nehal Wadhera", "BAT", False),
    "Stoinis": ("Marcus Stoinis", "AR", True),
    "Suyansh": ("Suryansh Shedge", "AR", False),
    "P Dube": ("Pravin Dubey", "BOWL", False),
    "Iyer": ("Shreyas Iyer", "BAT", False),
    "Omarzai": ("Azmatullah Omarzai", "AR", True),
    "Shashank": ("Shashank Singh", "AR", False),
    "Brar": ("Harpreet Brar", "AR", False),
    "Priyansh": ("Priyansh Arya", "BAT", False),
    "Chahal": ("Yuzvendra Chahal", "BOWL", False),
    "Arshdeep": ("Arshdeep Singh", "BOWL", False),

    # === RR ===
    "Kwena": ("Kwena Maphaka", "BOWL", True),
    "Jurel": ("Dhruv Jurel", "WK", False),
    "Donovan": ("Donovan Ferreira", "AR", True),
    "Deshpande": ("Tushar Deshpande", "BOWL", False),
    "Parag": ("Riyan Parag", "AR", False),
    "Shubham": ("Shubham Dubey", "BAT", False),
    "Shanaka": ("Dasun Shanaka", "AR", True),
    "Vaibhav": ("Vaibhav Suryavanshi", "BAT", False),  # Note: There's also Vaibhav Arora in KKR
    "bishnoi": ("Ravi Bishnoi", "BOWL", False),
    "Sushant": ("Sushant Mishra", "BOWL", False),
    "Jofra": ("Jofra Archer", "BOWL", True),
    "Kuldeep Sen": ("Kuldeep Sen", "BOWL", False),
    "Puthur": ("Vignesh Puthur", "BOWL", False),
    "Jaiswal": ("Yashasvi Jaiswal", "BAT", False),
    "Burger": ("Nandre Burger", "BOWL", True),
    "Yudhvir": ("Yudhvir Singh Charak", "AR", False),
    "Hetmyr": ("Shimron Hetmyer", "BAT", True),
    "Jadeja": ("Ravindra Jadeja", "AR", False),
    "Sandeep": ("Sandeep Sharma", "BOWL", False),

    # === DC ===
    "Natarajan": ("T Natarajan", "BOWL", False),
    "Miller": ("David Miller", "BAT", True),
    "Stubbs": ("Tristan Stubbs", "WK", True),
    "Mukesh": ("Mukesh Kumar", "BOWL", False),
    "Vipraj": ("Vipraj Nigam", "AR", False),
    "Karun": ("Karun Nair", "BAT", False),
    "Ngidi": ("Lungisani Ngidi", "BOWL", True),
    "Nitish Rana": ("Nitish Rana", "BAT", False),
    "Ashutosh": ("Ashutosh Sharma", "BAT", False),
    "KLR": ("KL Rahul", "WK", False),
    "Aquib": ("Auqib Dar", "BOWL", False),
    "Duckett": ("Ben Duckett", "BAT", True),
    "Kuldeep": ("Kuldeep Yadav", "BOWL", False),
    "Porel": ("Abishek Porel", "WK", False),
    "Chameera": ("Dushmantha Chameera", "BOWL", True),
    "Axar": ("Axar Patel", "AR", False),
    "Starc": ("Mitchell Starc", "BOWL", True),
    "Shaw": ("Prithvi Shaw", "BAT", False),
    "Rizwi": ("Sameer Rizvi", "BAT", False),

    # === KKR ===
    "Ramandeep": ("Ramandeep Singh", "AR", False),
    "Umran": ("Umran Malik", "BOWL", False),
    "Anukul Roy": ("Anukul Roy", "AR", False),
    "Narine": ("Sunil Narine", "AR", True),
    "Varun": ("Varun Chakaravarthy", "BOWL", False),
    "Pathirana": ("Matheesha Pathirana", "BOWL", True),
    "Rinku": ("Rinku Singh", "BAT", False),
    "Blessing": ("Blessing Muzarabani", "BOWL", True),
    "Powell": ("Rovman Powell", "BAT", True),
    "Green": ("Cameron Green", "AR", True),
    "Angkrish": ("Angkrish Raghuvanshi", "BAT", False),
    "Tejaswi": ("Tejasvi Singh", "BAT", False),
    "Seifert": ("Tim Seifert", "WK", True),
    "Tripathi": ("Rahul Tripathi", "BAT", False),
    "Harshit": ("Harshit Rana", "BOWL", False),
    "Finn": ("Finn Allen", "BAT", True),
    "Rahane": ("Ajinkya Rahane", "BAT", False),
    "Kartik Tyagi": ("Kartik Tyagi", "BOWL", False),

    # === LSG ===
    "Pooran": ("Nicholas Pooran", "WK", True),
    "Digvesh Rathi": ("Digvesh Singh", "BOWL", False),
    "Abdul Samad": ("Abdul Samad", "AR", False),
    "Mohsin": ("Mohsin Khan", "BOWL", False),
    "Shahbaz": ("Shahbaz Ahamad", "AR", False),
    "Himmat": ("Himmat Singh", "BAT", False),
    "Inglis": ("Josh Inglis", "WK", True),
    "Prince": ("Prince Yadav", "BOWL", False),
    "Marsh": ("Mitchell Marsh", "AR", True),
    "Hasaranga": ("Wanindu Hasaranga", "AR", True),
    "Akshat Raghu": ("Akshat Raghuwanshi", "BAT", False),
    "Shami": ("Mohammad Shami", "BOWL", False),
    "Mayank": ("Mayank Yadav", "BOWL", False),
    "Avesh": ("Avesh Khan", "BOWL", False),
    "Pant": ("Rishabh Pant", "WK", False),
    "Nortje": ("Anrich Nortje", "BOWL", True),
    "Markram": ("Aiden Markram", "BAT", True),
    "Badoni": ("Ayush Badoni", "BAT", False),
    "Mukul": ("Mukul Choudhary", "BOWL", False),

    # === GT ===
    "Sai Kishore": ("Sai Kishore", "BOWL", False),
    "Arshad Khan": ("Mohd Arshad Khan", "BOWL", False),
    "Sudarshan": ("Sai Sudharsan", "BAT", False),
    "Glenn": ("Glenn Phillips", "AR", True),
    "Ashok": ("Ashok Sharma", "AR", False),
    "Prasidh": ("Prasidh Krishna", "BOWL", False),
    "SRK": ("Shahrukh Khan", "BAT", False),
    "Tewatia": ("Rahul Tewatia", "AR", False),
    "Buttler": ("Jos Buttler", "WK", True),
    "Rashid": ("Rashid Khan", "BOWL", True),
    "Kumar": ("Nishant Sindhu", "AR", False),
    "Gill": ("Shubman Gill", "BAT", False),
    "Siraj": ("Mohammed Siraj", "BOWL", False),
    "Anuj Rawat": ("Anuj Rawat", "WK", False),
    "Rabada": ("Kagiso Rabada", "BOWL", True),
    "Holder": ("Jason Holder", "AR", True),
    "Washington": ("Washington Sundar", "AR", False),
    "Ishant": ("Ishant Sharma", "BOWL", False),
}


TEAM_SCOPED_PLAYER_OVERRIDES = {
    ("PBKS", "Suyansh"): ("Suryansh Shedge", "AR", False),
    ("PBKS", "P Dube"): ("Pravin Dubey", "BOWL", False),
    ("RR", "Burger"): ("Nandre Burger", "BOWL", True),
    ("RR", "Puthur"): ("Vignesh Puthur", "BOWL", False),
    ("RR", "Shanaka"): ("Dasun Shanaka", "AR", True),
    ("DC", "Aquib"): ("Auqib Dar", "BOWL", False),
    ("DC", "Porel"): ("Abishek Porel", "WK", False),
    ("DC", "Rizwi"): ("Sameer Rizvi", "BAT", False),
    ("KKR", "Vaibhav"): ("Vaibhav Arora", "BOWL", False),
    ("LSG", "Mayank"): ("Mayank Yadav", "BOWL", False),
}


def resolve_registry_entry(ipl_team: str, nickname: str) -> tuple[str, str, bool]:
    """Resolve a draft nickname to the accepted player identity for that IPL team."""
    if (ipl_team, nickname) in TEAM_SCOPED_PLAYER_OVERRIDES:
        return TEAM_SCOPED_PLAYER_OVERRIDES[(ipl_team, nickname)]

    return PLAYER_REGISTRY[nickname]


def get_search_queries_for_player(nickname: str) -> dict:
    """
    Given a nickname, returns the search queries needed to collect data for this player.
    """
    if nickname not in PLAYER_REGISTRY:
        return {"error": f"Unknown player: {nickname}"}

    full_name, role, is_overseas = PLAYER_REGISTRY[nickname]

    return {
        "nickname": nickname,
        "full_name": full_name,
        "role": role,
        "is_overseas": is_overseas,
        "queries": {
            "ipl_stats": f"{full_name} IPL career stats runs wickets matches",
            "recent_form": f"{full_name} IPL 2025 stats performance",
            "injury_status": f"{full_name} injury update 2026 availability IPL",
        }
    }
