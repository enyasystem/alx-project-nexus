# Project Nexus Documentation

## Overview
This repository documents major learnings from the ProDev Backend Engineering program.  
It serves as a knowledge hub for backend technologies, concepts, challenges, and best practices covered during the program.  

## Objectives
- Consolidate key learnings from the ProDev Backend Engineering program.  
- Document backend technologies, concepts, challenges, and solutions.  
- Provide a reference guide for current and future learners.  
- Support collaboration between frontend and backend learners.  

## Key Technologies
- Python  
- Django  
- REST APIs  
- GraphQL  
- Docker  
- CI/CD Pipelines  

## Backend Concepts
- Database Design  
- Asynchronous Programming  
- Caching Strategies  
- System Design  

## Challenges and Solutions
- Managing long-running tasks → Solved with Celery and RabbitMQ  
- Database performance issues → Solved with query optimization and indexing  
- Deployment difficulties → Solved with Docker and automated CI/CD pipelines  

## Best Practices and Takeaways
- Write clean and modular code  
- Document APIs clearly  
- Use version control effectively  
- Apply security measures consistently  

## Collaboration
This project encourages collaboration with:  
- Backend learners for sharing knowledge and solving problems  
- Frontend learners who will use backend endpoints  

Communication and collaboration are supported through the **#ProDevProjectNexus** Discord channel.  

## Repository
GitHub Repository: **alx-project-nexus**  

## Getting started (local dev)

This repo contains a Django project (`nexus`) and a `catalog` app implementing the product catalog APIs.

- Create and activate a virtual environment (Windows PowerShell):

```powershell
python -m venv venv; .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

- Run migrations and start the dev server (uses SQLite by default; to use PostgreSQL set `POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT` in a `.env` file):

```powershell
python manage.py migrate
python manage.py runserver
```

API docs (Swagger UI) will be available at `http://127.0.0.1:8000/api/docs/`.
