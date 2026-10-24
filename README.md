# StudySync -- AI-Driven Study Group & Peer-Tutoring Platform

StudySync is an AI-powered study group matching platform designed for university students. It combines **reciprocal skill matching**, **consensus schedule overlap**, **12-feature machine learning ranking**, **interactive 3D radial wheel navigation**, **real-time cohort chat**, and a **peer review & approval system**.

---

## Key Features

- **Cornell CIS Design System**: Cyberpunk/academic aesthetic with a real-time WebGL Ice Night shader.
- **ML Ranking Engine (12 Features)**: Logistic regression ranker trained on reciprocal skill gain, availability overlap, cohort size, and knowledge transfer families.
- **Explainable AI (Why Matched)**: Transparent breakdown detailing exact weak-spot coverage, peer leader competencies, and shared free meeting hours.
- **Campus Directory & Team Builder**: Search, filter, and create study pods with custom paces (Exam prep, Sprint, Deep dive), modes (Online, In-person, Hybrid), and time slots.
- **5-Star Review System**:
  - Rate study cohorts on a 1–5 star scale with live averages.
  - Review peers with star ratings and written feedback (only between cohort members).
  - Group leader tools to accept, reject, or remove members.
- **Real-Time Group Chat**: Cohort messaging with 3-second polling, message deletion, and membership security.

---

## Tech Stack

- **Frontend**: Vue 3 (Composition API), Vite, Tailwind CSS, Three.js / WebGL shaders.
- **Backend**: FastAPI, SQLAlchemy, SQLite, Pydantic, Python-JOSE (JWT auth).
- **Machine Learning**: Scikit-learn (Logistic Regression, TF-IDF / MiniLM embeddings), NumPy, Joblib.

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Backend Setup
```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
pip install scikit-learn joblib pytest
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Demo Accounts

All demo accounts use password: `password123`

| Name | Email | Role |
| :--- | :--- | :--- |
| **Marcus Vance** | `marcus@univ.edu` | Leader of *AlgoRhythms* |
| **Alex Chen** | `alex@univ.edu` | Member in *AlgoRhythms* |
| **Chloe Kim** | `chloe@univ.edu` | Member in *AlgoRhythms* |
| **Elena Rostova** | `elena@univ.edu` | Member in *Graph Titans* |
| **Devon Zhao** | `devon@univ.edu` | Member in *Neural Nomads* |
