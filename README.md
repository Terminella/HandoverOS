# HandoverOS
HandoverOS is an AI-powered knowledge continuity platform that reconstructs project history, decisions, responsibilities, risks, dependencies, and unresolved tasks from GitHub, documents, and team communications to create evidence-backed, verifiable handovers and prevent critical knowledge loss.

# 📁Project Structure
```text
HandoverOS/
│
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── projects.py
│   │   │   └── users.py
│   │   │
│   │   └── core/
│   │       └── config.py
│   │
│   └── data_engineering/
│       ├── __init__.py
│       ├── config.py
│       │
│       ├── extractors/
│       │   ├── __init__.py
│       │   └── document_extractor.py
│       │
│       ├── preprocessing/
│       │   ├── normalizer.py
│       │   └── validator.py
│       │
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── source_schema.py
│       │
│       ├── services/
│       │   └── __init__.py
│       │
│       ├── storage/
│       │   └── __init__.py
│       │
│       └── tests/
│           ├── __init__.py
│           ├── test_document_extractor.py
│           ├── test_normalizer.py
│           ├── test_source_schema.py
│           └── test_validator.py
│
├── frontend/
│   ├── next.config.ts
│   ├── package.json
│   ├── tsconfig.json
│   │
│   └── src/
│       └── app/
│           ├── layout.tsx
│           └── page.tsx
│
├── docs/
│   ├── api_documentation.md
│   ├── architecture.md
│   ├── data_flow.md
│   ├── database_design.md
│   └── user_workflow.md
│
└── tests/
    ├── __init__.py
    └── test_workflow.py
```
