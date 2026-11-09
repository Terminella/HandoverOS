# HandoverOS
HandoverOS is an AI-powered knowledge continuity platform that reconstructs project history, decisions, responsibilities, risks, dependencies, and unresolved tasks from GitHub, documents, and team communications to create evidence-backed, verifiable handovers and prevent critical knowledge loss.

# 📁Project Structure
```text
HandoverOS/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── auth.py
│   ├── routes.py
│   └── requirements.txt
│
├── ingestion/
│   ├── github.py
│   └── documents.py
│
├── ai_engine/
│   ├── ai.py
│   └── verification.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   └── package.json
│
├── tests/
│   └── test_main.py
│   └── data_engineering/
├── .env
├── .gitignore
├── docker-compose.yml
└── README.md
```
