# **🧘 Stage 1: Title & Introduction**

# 🧘 MindfullyMosaic

MindfullyMosaic is a personal finance, productivity, and mindfulness suite built in Python.  
It was my original inspiration before creating the Flutter-based Humble Time Tracker.

This desktop app blends budgeting, bill tracking, journaling, guided meditation, and even a mini-game — all designed to support emotional pacing and intentional living.

---
# **🧩 Stage 2: Features Summary**

## ✨ Features

- **Budget Planner** – Track income, expenses, and monthly variance
- **Bill Manager** – Forecast upcoming bills and manage due dates
- **Task Tracker** – Create, complete, and reflect on tasks
- **Journal & Mood Log** – Record reflections and emotional states
- **Guided Meditation** – Ambient soundscapes with start/end bells
- **Mini-Game: Apple Shooter** – A playful break to reset focus
- **User Login System** – Secure access with encrypted credentials

---
# **🛠️ Stage 3: Tech Stack & Rationale**

## 🛠️ Tech Stack

| Technology     | Purpose                                                                 |
|----------------|-------------------------------------------------------------------------|
| Python 3       | Core language for rapid prototyping and rich desktop support            |
| Tkinter        | GUI framework for native-feeling desktop interfaces                     |
| SQLite         | Lightweight, file-based database for user data and journaling           |
| dotenv         | Secure environment variable management for email credentials            |
| bcrypt         | Password hashing for secure login                                       |
| pyttsx3        | Offline text-to-speech for voice prompts                                |
| pygame         | Sound playback and mini-game engine                                     |
| matplotlib     | Visualisation of budget and task data                                   |
| pandas         | Data manipulation and reporting                                         |

This stack was chosen to keep the app fully offline, lightweight, and easy to run on any Windows machine without external dependencies.

---
# 📦 Stage 4: Installation Instructions

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ChamindaR/MindfullyMosaic.git
   cd MindfullyMosaic

2. Install dependencies:
```
   pip install -r requirements.txt
```
   \MindfullyMosaic\requirements.txt 

4. Create a .env file in the root directory with the following format:

   EMAIL_ADDRESS=your_email@example.com
   
   EMAIL_PASSWORD=your_app_specific_password [???? ???? ???? ????]

   **Note:** Example **.env** file is included in the folder **\\MindfullyMosaic-release\dist\.env**

6. Run the app:
```
   python launcher.py
```
   **Note:** All personal data has been removed from the included .db files. You may start fresh or import your own.

---
# **📷 Stage 5: Screenshots & UI Overview**

## 📷 Screenshots & UI Overview

```markdown
System Flow chart: https://github.com/user-attachments/assets/f43f715a-92c9-4cd3-9ab7-19199bda6967
Database ER Diagram: https://github.com/user-attachments/assets/800a0f2a-50f9-4d21-a5bc-3c173b14fec4
Launcher: https://github.com/user-attachments/assets/56d35809-86ff-4a86-9d8d-21fd032dbde7
Home Page/Actuals Entry: https://github.com/user-attachments/assets/57f1a60b-6131-4706-bcbe-ae6d03f23a2a
Settings: https://github.com/user-attachments/assets/e220bfb8-0526-4994-97a8-056ff128c154
Dashboard: https://github.com/user-attachments/assets/800a0f2a-50f9-4d21-a5bc-3c173b14fec4
Budget Planner: https://github.com/user-attachments/assets/bcc8eb29-1418-4d93-b268-6bd3c051d91a
Variance Report: https://github.com/user-attachments/assets/d4643819-9ef8-495e-b2aa-f685e37f9e04
Time Manager: https://github.com/user-attachments/assets/f011623c-f3a7-4769-bd3c-9e3d77f3f62d
Calendar View: https://github.com/user-attachments/assets/332c2610-53dc-443e-b406-223b8aebbf54
Bill Manager: https://github.com/user-attachments/assets/df9b237d-84b8-4dae-8228-657f9c465aa8
Mindful Meditation: https://github.com/user-attachments/assets/746152ee-6d1e-4ffe-83dd-5c8a4406343d
Reflection Journal: https://github.com/user-attachments/assets/5deab8a3-f332-4d38-9e19-527d4e1f329d
Mood Trends: https://github.com/user-attachments/assets/1d276d13-14a7-4f86-abb0-bc902fa0934f
Apple Shoorter: https://github.com/user-attachments/assets/d2daed0e-32a7-4d74-8817-7f67c3190bb8
Profile Settings: https://github.com/user-attachments/assets/f3a3cfd5-0a62-46b2-8838-b08001de46e0
```

## 📷 Screenshots

**System Flow chart**
<img width="944" height="443" alt="image" src="https://github.com/user-attachments/assets/f43f715a-92c9-4cd3-9ab7-19199bda6967" />

**Database ER Diagram**
<img width="839" height="1458" alt="image" src="https://github.com/user-attachments/assets/800a0f2a-50f9-4d21-a5bc-3c173b14fec4" />

**Launcher**

<img width="663" height="571" alt="image" src="https://github.com/user-attachments/assets/56d35809-86ff-4a86-9d8d-21fd032dbde7" />

**Home Page / Actuals Entry**
<img width="942" height="520" alt="image" src="https://github.com/user-attachments/assets/57f1a60b-6131-4706-bcbe-ae6d03f23a2a" />

**Settings**
<img width="944" height="453" alt="image" src="https://github.com/user-attachments/assets/e220bfb8-0526-4994-97a8-056ff128c154" />

**Dashboard**
<img width="1390" height="793" alt="image" src="https://github.com/user-attachments/assets/4205ad5e-9f6e-43a7-a254-d51313f3638e" />

**Budget Planner**
<img width="1321" height="631" alt="image" src="https://github.com/user-attachments/assets/bcc8eb29-1418-4d93-b268-6bd3c051d91a" />

**Variance Report**
<img width="1323" height="634" alt="image" src="https://github.com/user-attachments/assets/d4643819-9ef8-495e-b2aa-f685e37f9e04" />

**Time Manager**
<img width="1388" height="793" alt="image" src="https://github.com/user-attachments/assets/f011623c-f3a7-4769-bd3c-9e3d77f3f62d" />

**Calendar View**
<img width="1324" height="633" alt="image" src="https://github.com/user-attachments/assets/332c2610-53dc-443e-b406-223b8aebbf54" />

**Bill Manager**
<img width="1390" height="790" alt="image" src="https://github.com/user-attachments/assets/df9b237d-84b8-4dae-8228-657f9c465aa8" />

**Mindful Meditation**
<img width="1388" height="795" alt="image" src="https://github.com/user-attachments/assets/746152ee-6d1e-4ffe-83dd-5c8a4406343d" />

**Reflection Journal**
<img width="1388" height="796" alt="image" src="https://github.com/user-attachments/assets/5deab8a3-f332-4d38-9e19-527d4e1f329d" />

**Mood Trends**
<img width="1390" height="795" alt="image" src="https://github.com/user-attachments/assets/1d276d13-14a7-4f86-abb0-bc902fa0934f" />

**Apple Shoorter**
<img width="1390" height="795" alt="image" src="https://github.com/user-attachments/assets/d2daed0e-32a7-4d74-8817-7f67c3190bb8" />

**Profile Settings**
<img width="1389" height="796" alt="image" src="https://github.com/user-attachments/assets/f3a3cfd5-0a62-46b2-8838-b08001de46e0" />

The interface is designed to be calming, intuitive, and neurodivergent-friendly — with clear icons, soft colours, and
minimal distractions.

---
# **📜 Stage 6: Backstory & Legacy**

## 💡 Backstory

MindfullyMosaic was developed as a personal tool to support mindful living, financial clarity, and emotional pacing.  
It laid the foundation for my later Flutter app, Humble Time Tracker, which builds on these ideas with cross-platform support and voice synthesis.

This project remains a testament to the power of intentional software — blending utility with emotional support.

## 🧠 Neurodiversity & Emotional Design

MindfullyMosaic was designed with neurodivergent users in mind — including those with ADHD, autism, anxiety, and sensory sensitivities.

The interface and features aim to support:

- **Emotional pacing** – Gentle transitions, ambient sounds, and voice cues help users stay present without overwhelm
- **Visual clarity** – Clean layouts, semantic icons, and consistent colour palettes reduce cognitive load
- **Routine anchoring** – Start/end bells, journaling prompts, and task reflection create rhythm and closure
- **Offline privacy** – No cloud sync or external APIs; users retain full control of their data
- **Low-friction interaction** – Minimal typing, clear buttons, and predictable flows reduce decision fatigue

This project is part of a broader commitment to inclusive software — where emotional wellbeing and accessibility are treated as core features, not afterthoughts.

---
# **🧪 Stage 7: Development Notes**

## 🧪 Development Notes

- `.vs/` and `.env` are excluded via `.gitignore` for privacy and security
- All sound and image assets are included in the repo
- The code is modular, with each feature encapsulated in its own function or class
- No external APIs are required — the app runs fully offline

---
# **🪪 Stage 8: Licence & Contribution**

## 🪪 Licence

This project is released under the MIT Licence.  
Feel free to fork, adapt, and build upon it.

## 🤝 Contributions

While this project is no longer actively developed, I welcome feedback, and ideas.  
If you’d like to help port features to Humble Time Tracker or contribute to its evolution, please reach out.
