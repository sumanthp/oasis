# Oasis: The AI-Engine Screening Sandbox 🏝️

[![License: Apache 2.0 with Commons Clause](https://img.shields.io/badge/License-Apache%202.0%20%2B%20Commons%20Clause-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-compose-green.svg)](https://www.docker.com/)

**Oasis** is an open-source, enterprise-grade candidate assessment platform tailored for AI engineering roles. 
Instead of testing candidates on generic LeetCode problems, Oasis drops them into a real, sandboxed "broken production" environment. They must use advanced tooling (LangGraph, MCP, RAG) to debug systems and pass an automated LLM Judge.

---

## 🌟 Key Features

*   **Real-World Scenarios**: Candidates are dropped into a fully containerized VS Code (`code-server`) workspace with broken AI implementations (e.g., recursive tool-calling loops in LangGraph).
*   **LLM-as-a-Judge**: Candidates receive real-time, iterative feedback from an automated judge powered by `Ollama` running locally or within your private cloud.
*   **Recruiter Intelligence**: A command center for recruiters to visualize pass/fail ratios, average test times, and inspect the raw code / trace logs submitted by the candidate.
*   **Invite-Only Sessions**: Securely generate single-use JWT registration links for candidates to take assessments.
*   **Crash Resilience**: If a candidate accidentally closes their tab during a 3-hour test, the system automatically preserves their IDE state and provides a "Resume Session" button.

---

## 🏗️ Architecture

Oasis consists of the following components running securely via Docker Compose:
1. **Orchestrator (`platform/api`)**: A FastAPI backend that handles RBAC, JWT authentication, and session provisioning. Uses SQLite for metadata tracking.
2. **Frontend UI (`platform/ui`)**: A glassmorphism-themed, modern web interface.
3. **IDE Container**: A dynamically spawned `codercom/code-server` workspace injected directly into the frontend via iframe.
4. **AI Judge (`evaluator/grader.py`)**: A Python subprocess running LangChain to analyze the candidate's code outputs and output trace logs.

---

## 🚀 Quick Start Guide

### Prerequisites
*   Docker and Docker Compose
*   (Optional but recommended) At least 8GB of RAM for running the Ollama container locally.

### 1. Clone & Setup
```bash
git clone https://github.com/your-username/oasis-ai-screening.git
cd oasis-ai-screening

# Generate a secure secret key for JWT authentication
export SECRET_KEY=$(openssl rand -hex 32)
```

### 2. Start the Platform
```bash
docker-compose up -d --build
```
This will spin up the `orchestrator` and `ollama` services.

### 3. Log In
Navigate to `http://localhost:8000`.
- **Default Admin Credentials**:
  - Username: `admin`
  - Password: `admin`
*(Note: Be sure to change the admin password in `database.py` before exposing to the internet!)*

### 4. Create an Invite
- Log in as the Admin and go to **Recruiter Admin**.
- Click **+ Generate Invite Link**.
- Open the copied URL in an incognito window to simulate a candidate registration and experience the sandbox!

---

## 🛠️ Adding Custom Challenges

Challenges are defined via a metadata-driven approach. To create a new challenge, create a folder under `challenges/` with a `manifest.yaml`:

```yaml
name: "System Design: RAG Hallucination"
domain: "Retrieval Augmented Generation"
description: "The company's internal wiki bot is hallucinating facts. Fix the embedding chunk overlap and the retrieval threshold."
difficulty: "Hard"
stack:
  - "LangChain"
  - "ChromaDB"
```
Next, add an `evaluator/grader.py` script to test their logic. The orchestrator handles the rest automatically!

---

## 🛡️ License

Oasis is released under the **Apache 2.0 License** with the **Commons Clause** condition.
This means the platform is free to use, modify, and host for your own internal hiring needs. However, you are strictly prohibited from **Selling** the software or offering it as a paid hosted service (SaaS) to third parties. 
See the [LICENSE](LICENSE) file for complete details.

*Can the creator commercialize this in the future?*
Yes. The original copyright holder retains the right to offer Oasis under alternative commercial licenses in the future, but the open-source version will remain protected under this Commons Clause.