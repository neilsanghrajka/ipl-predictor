"""
Player Registry: Maps draft nicknames to full names, roles, and overseas status.
This is the master reference that the data collection script uses to search for stats.

We need this because the draft sheet uses short names like "VK", "Sky", "QDK", "MSD" etc.
"""

# Format: (nickname, full_name, role, is_overseas)
# role: BAT = Batter, BOWL = Bowler, AR = All-Rounder, WK = Wicketkeeper-Batter

PLAYER_REGISTRY = {
    # === CSK ===
    "Samson": ("Sanju Samson", "WK", False),
    "R Chahar": ("Rahul Chahar", "BOWL", False),
    "Henry": ("Matt Henry", "BOWL", True),
    "Kartik": ("Kartik Tyagi", "BOWL", False),  # Note: different from KKR's Kartik Tyagi — context says CSK
    "prashant": ("Prashant Solanki", "BOWL", False),
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
    "Mhatre": ("Prathamesh Mhatre", "BAT", False),
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
    "Ashwini": ("Ashwini Kumar", "BOWL", False),

    # === SRH ===
    "Klaasen": ("Heinrich Klaasen", "WK", True),
    "E Malinga": ("Eshan Malinga", "BOWL", False),
    "Abhishek": ("Abhishek Sharma", "AR", False),
    "Jaydev": ("Jaydev Unadkat", "BOWL", False),
    "Fuletra": ("Sachin Fuletra", "BAT", False),
    "Harshal": ("Harshal Patel", "AR", False),
    "Cummins": ("Pat Cummins", "BOWL", True),
    "Aniket": ("Aniket Verma", "BAT", False),
    "NKR": ("Nitish Kumar Reddy", "AR", False),
    "Shivang": ("Shivang Bhatt", "BAT", False),
    "Zeeshan": ("Zeeshan Ansari", "BOWL", False),
    "Head": ("Travis Head", "BAT", True),
    "Livingstone": ("Liam Livingstone", "AR", True),
    "Smaran": ("Smaran Ravichandran", "BAT", False),
    "Kishan": ("Ishan Kishan", "WK", False),
    "Mavi": ("Shivam Mavi", "BOWL", False),
    "Carse": ("Brydon Carse", "AR", True),
    "Salil": ("Salil Arunkumar", "BAT", False),
    "Harsh Dubey": ("Harsh Dubey", "BOWL", False),

    # === RCB ===
    "Krunal": ("Krunal Pandya", "AR", False),
    "Hazelwood": ("Josh Hazlewood", "BOWL", True),
    "Jitesh": ("Jitesh Sharma", "WK", False),
    "Rasikh": ("Rasikh Salam", "BOWL", False),
    "Bethell": ("Jacob Bethell", "AR", True),
    "Salt": ("Phil Salt", "WK", True),
    "Romario": ("Romario Shepherd", "AR", True),
    "Patidar": ("Rajat Patidar", "BAT", False),
    "Dayal": ("Yash Dayal", "BOWL", False),
    "Mangesh": ("Mangesh Kumar", "BOWL", False),
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
    "Suyansh": ("Suyansh Mankad", "BAT", False),
    "P Dube": ("Priyansh Dube", "BAT", False),
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
    "Puthur": ("Akash Madhwal", "BOWL", False),  # Need to verify
    "Jaiswal": ("Yashasvi Jaiswal", "BAT", False),
    "Burger": ("Lizaad Williams", "BOWL", True),  # Need to verify — could be Nandre Burger
    "Yudhvir": ("Yudhvir Singh", "AR", False),
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
    "Ngidi": ("Lungi Ngidi", "BOWL", True),
    "Nitish Rana": ("Nitish Rana", "BAT", False),
    "Ashutosh": ("Ashutosh Sharma", "BAT", False),
    "KLR": ("KL Rahul", "WK", False),
    "Aquib": ("Aquib Nabi", "BOWL", False),
    "Duckett": ("Ben Duckett", "BAT", True),
    "Kuldeep": ("Kuldeep Yadav", "BOWL", False),
    "Porel": ("Ishan Porel", "BOWL", False),
    "Chameera": ("Dushmantha Chameera", "BOWL", True),
    "Axar": ("Axar Patel", "AR", False),
    "Starc": ("Mitchell Starc", "BOWL", True),
    "Shaw": ("Prithvi Shaw", "BAT", False),
    "Rizwi": ("Mohammad Rizwan", "WK", True),  # Need to verify — or could be a domestic player

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
    "Tejaswi": ("Tejaswi Dahiya", "BAT", False),
    "Seifert": ("Tim Seifert", "WK", True),
    "Tripathi": ("Rahul Tripathi", "BAT", False),
    "Harshit": ("Harshit Rana", "BOWL", False),
    "Finn": ("Finn Allen", "BAT", True),
    "Rahane": ("Ajinkya Rahane", "BAT", False),
    "Kartik Tyagi": ("Kartik Tyagi", "BOWL", False),

    # === LSG ===
    "Pooran": ("Nicholas Pooran", "WK", True),
    "Digvesh Rathi": ("Digvesh Rathi", "BOWL", False),
    "Abdul Samad": ("Abdul Samad", "AR", False),
    "Mohsin": ("Mohsin Khan", "BOWL", False),
    "Shahbaz": ("Shahbaz Ahmed", "AR", False),
    "Himmat": ("Himmat Singh", "BAT", False),
    "Inglis": ("Josh Inglis", "WK", True),
    "Prince": ("Prince Yadav", "BOWL", False),
    "Marsh": ("Mitchell Marsh", "AR", True),
    "Hasaranga": ("Wanindu Hasaranga", "AR", True),
    "Akshat Raghu": ("Akshat Raghuwanshi", "BAT", False),
    "Shami": ("Mohammad Shami", "BOWL", False),
    "Mayank": ("Mayank Agarwal", "BAT", False),
    "Avesh": ("Avesh Khan", "BOWL", False),
    "Pant": ("Rishabh Pant", "WK", False),
    "Nortje": ("Anrich Nortje", "BOWL", True),
    "Markram": ("Aiden Markram", "BAT", True),
    "Badoni": ("Ayush Badoni", "BAT", False),
    "Mukul": ("Mukul Choudhary", "BOWL", False),

    # === GT ===
    "Sai Kishore": ("R Sai Kishore", "BOWL", False),
    "Arshad Khan": ("Arshad Khan", "BOWL", False),
    "Sudarshan": ("Sai Sudharsan", "BAT", False),
    "Glenn": ("Glenn Phillips", "AR", True),
    "Ashok": ("Ashok Sharma", "AR", False),
    "Prasidh": ("Prasidh Krishna", "BOWL", False),
    "SRK": ("Shahrukh Khan", "BAT", False),
    "Tewatia": ("Rahul Tewatia", "AR", False),
    "Buttler": ("Jos Buttler", "WK", True),
    "Rashid": ("Rashid Khan", "BOWL", True),
    "Kumar": ("Nishant Sindhu", "AR", False),  # Need to verify
    "Gill": ("Shubman Gill", "BAT", False),
    "Siraj": ("Mohammed Siraj", "BOWL", False),
    "Anuj Rawat": ("Anuj Rawat", "WK", False),
    "Rabada": ("Kagiso Rabada", "BOWL", True),
    "Holder": ("Jason Holder", "AR", True),
    "Washington": ("Washington Sundar", "AR", False),
    "Ishant": ("Ishant Sharma", "BOWL", False),
}


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
