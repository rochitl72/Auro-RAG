# AuroRag - Agentic RAG Text-to-SQL System

<div align="center">

![AuroRag](https://img.shields.io/badge/AuroRag-Agentic%20RAG-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![React](https://img.shields.io/badge/React-18.3-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

**A Multi-Agent RAG Text-to-SQL System for Aravind Eye Hospital**

Transform natural language queries into SQL using local LLM (Llama 3.1 8B) with a 4-phase agentic workflow powered by LangGraph.

[Features](#-key-features) • [Architecture](#-system-architecture) • [Quick Start](#-quick-start) • [Documentation](#-detailed-process-flow)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Detailed Process Flow](#-detailed-process-flow)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Linux](#linux)
- [Running the Application](#-running-the-application)
- [API Endpoints](#-api-endpoints)
- [Example Queries](#-example-queries)
- [Technology Stack](#-technology-stack)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

AuroRag is an **Agentic RAG (Retrieval-Augmented Generation) Text-to-SQL System** designed for Aravind Eye Hospital to enable natural language querying of patient data. The system uses a **4-phase multi-agent state machine** built with LangGraph, where each agent specializes in a specific task:

1. **Receptionist**: Query decomposition and planning
2. **Librarian**: Intelligent schema linking and column selection
3. **Engineer**: SQL query generation with self-correction
4. **Inspector**: Query execution and result validation

The entire system runs **locally** using Ollama and Llama 3.1 8B, ensuring data privacy and eliminating the need for external API keys.

---

## ✨ Key Features

- 🤖 **Fully LLM-Driven**: No hardcoded rules or regex post-processing
- 🏠 **Local Processing**: Uses Ollama with Llama 3.1 8B (no API keys needed)
- 🧠 **Intelligent Schema Linking**: LLM selects relevant columns based on query context
- 🔄 **Self-Correction**: Automatically retries SQL generation on errors (max 3 attempts)
- 💬 **Natural Explanations**: LLM generates context-aware, human-readable responses
- 🔍 **Semicolon Handling**: Properly handles semicolon-separated values in DiagnosisName
- ⚡ **Real-time Pipeline Visualization**: See each agent phase in action
- 📊 **Dynamic Data Statistics**: Live stats from the actual dataset

---

## 🏗️ System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                    (React + TypeScript + Vite)                   │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Chat UI    │  │  Pipeline    │  │   Sidebar    │       │
│  │              │  │  Visualizer  │  │   (Stats)    │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
└─────────┼─────────────────┼─────────────────┼───────────────┘
           │                 │                 │
           └─────────────────┴─────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   FastAPI REST  │
                    │      API        │
                    │  (Port 8000)    │
                    └────────┬─────────┘
                             │
                             ▼
        ┌──────────────────────────────────────────┐
        │      LangGraph Agent Workflow             │
        │                                            │
        │  ┌──────────────┐                        │
        │  │ Receptionist │ ──► Query Planning     │
        │  └──────┬───────┘                        │
        │         │                                 │
        │         ▼                                 │
        │  ┌──────────────┐                        │
        │  │  Librarian   │ ──► Schema Linking    │
        │  └──────┬───────┘                        │
        │         │                                 │
        │         ▼                                 │
        │  ┌──────────────┐                        │
        │  │   Engineer    │ ──► SQL Generation    │
        │  └──────┬───────┘                        │
        │         │                                 │
        │         ▼                                 │
        │  ┌──────────────┐                        │
        │  │  Inspector   │ ──► Execution & Check │
        │  └──────┬───────┘                        │
        │         │                                 │
        │         └───► Retry on Error (max 3x)    │
        └──────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Ollama     │    │  Schema      │    │  SQLite      │
│  (Llama 3.1) │    │   Store      │    │  (In-Memory) │
│  Port 11434  │    │ (Embeddings) │    │   Database   │
└──────────────┘    └──────────────┘    └──────────────┘
```

### Component Interaction Flow

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Frontend (React)                                        │
│  - Captures user input                                   │
│  - Sends POST /api/query                                 │
│  - Displays pipeline progress                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Backend (FastAPI)                                       │
│  - Receives query                                        │
│  - Initializes AgentGraph                                │
│  - Executes LangGraph workflow                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 1: Receptionist Agent                            │
│  - LLM analyzes query                                   │
│  - Generates JSON execution plan                         │
│  - Output: {steps: [...], final_action: "..."}          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 2: Librarian Agent                               │
│  - LLM receives query + plan                            │
│  - Analyzes all 31 columns                              │
│  - Selects top 8-10 relevant columns                    │
│  - Output: [{column_name, description, similarity}]     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 3: Engineer Agent                                │
│  - LLM receives: query, plan, relevant columns          │
│  - Uses few-shot examples                                │
│  - Generates SQLite query                                │
│  - Output: "SELECT ... FROM patient_data WHERE ..."     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 4: Inspector Agent                               │
│  - Executes SQL on SQLite database                      │
│  - If error: feeds back to Engineer (retry)             │
│  - If success: generates natural language explanation    │
│  - Output: {result_df, explanation}                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Response to Frontend                                    │
│  - JSON with plan, columns, SQL, results, explanation   │
│  - Frontend updates UI with all phases                   │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Detailed Process Flow

### Step-by-Step Execution

#### **Step 1: Receptionist Agent (Query Planning)**

**Input**: User's natural language query  
**Process**:
1. LLM receives the query: `"bring up all cataract patients"`
2. LLM analyzes the intent and breaks it down into executable steps
3. Generates a structured JSON plan:
   ```json
   {
     "steps": [
       {
         "step_number": 1,
         "action": "filter",
         "description": "Filter patients with cataract diagnosis",
         "filters": {"column": "DiagnosisName", "condition": "cataract"},
         "target": "cataract patients"
       }
     ],
     "final_action": "Return all matching patient records"
   }
   ```
4. Sets `execution_count = 0` for retry tracking

**Output**: Structured plan with steps and actions

---

#### **Step 2: Librarian Agent (Schema Linking)**

**Input**: User query + execution plan  
**Process**:
1. LLM receives query context and plan
2. LLM analyzes all 31 available columns from schema description
3. For each column, considers:
   - Column name (e.g., `DiagnosisName`)
   - Description (e.g., "The diagnosis or medical condition...")
   - Example values
4. LLM selects top 8-10 most relevant columns based on:
   - Query keywords matching column descriptions
   - Plan requirements
   - Semantic relevance
5. Returns ordered list: `["DiagnosisName", "Anonymous_Uid", "Drugname", ...]`
6. Builds `relevant_columns` array with full metadata

**Output**: Array of relevant columns with descriptions and similarity scores

**Example Output**:
```json
[
  {
    "column_name": "DiagnosisName",
    "description": "The diagnosis or medical condition...",
    "similarity": 1.0
  },
  {
    "column_name": "Anonymous_Uid",
    "description": "A unique identifier...",
    "similarity": 0.9
  }
]
```

---

#### **Step 3: Engineer Agent (SQL Generation)**

**Input**: Query + Plan + Relevant Columns + Error Context (if retry)  
**Process**:
1. LLM receives comprehensive context:
   - User query
   - Execution plan
   - Top 10 relevant columns with descriptions
   - All available column names (for reference)
   - Few-shot examples (6 examples of similar queries)
   - Error message (if this is a retry)
2. LLM generates SQL query following these rules:
   - Table name: `patient_data`
   - Patient ID column: `Anonymous_Uid` (NOT PatientID)
   - DiagnosisName uses `LIKE '%value%'` for semicolon-separated values
   - NULL handling: `IS NOT NULL` or `IS NULL`
   - Column names use underscores
3. SQL extraction from LLM response:
   - Tries multiple regex patterns
   - Handles markdown code blocks
   - Removes explanations, keeps only SQL
4. If extraction fails, retries with clearer prompt
5. Validates SQL starts with `SELECT`

**Output**: Valid SQLite query string

**Example Output**:
```sql
SELECT * FROM patient_data 
WHERE DiagnosisName LIKE '%cataract%'
```

**Error Handling**:
- If SQL generation fails, sets `error_message`
- Inspector will trigger retry (max 3 attempts)

---

#### **Step 4: Inspector Agent (Execution & Validation)**

**Input**: Generated SQL query  
**Process**:
1. **Execution**:
   - Executes SQL on in-memory SQLite database
   - Uses `pd.read_sql_query(sql_query, self.conn)`
2. **Success Path**:
   - Stores results in `execution_result` DataFrame
   - Calls `_generate_explanation()`:
     - LLM receives query + results
     - Generates natural, concise answer
     - Returns human-readable explanation
   - Sets `error_message = ""`
3. **Error Path**:
   - Catches SQL execution errors
   - Stores error in `error_message`
   - If `execution_count < 3`: triggers retry
   - If `execution_count >= 3`: returns error explanation

**Output**: 
- Success: `{execution_result: DataFrame, explanation: str, error_message: ""}`
- Error: `{execution_result: empty, explanation: str, error_message: "..."}`

**Retry Logic**:
```
Inspector detects error
    │
    ▼
should_retry() checks:
  - execution_count < 3?
  - Error is recoverable? (column not found, syntax error)
    │
    ├─ YES ──► Routes back to Engineer (with error context)
    │
    └─ NO ──► Returns error to user
```

---

### Self-Correction Loop

```
┌─────────────────────────────────────────────────────┐
│  Engineer generates SQL                             │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  Inspector executes SQL                              │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
    SUCCESS              ERROR
        │                     │
        │                     ▼
        │         ┌───────────────────────┐
        │         │ execution_count < 3?   │
        │         └───────┬───────────────┘
        │                 │
        │         ┌────────┴────────┐
        │         │                  │
        │         YES                NO
        │         │                  │
        │         ▼                  ▼
        │    ┌─────────┐      ┌──────────┐
        │    │ Retry    │      │ Return   │
        │    │ Engineer │      │ Error    │
        │    │ (with    │      │          │
        │    │  error)  │      │          │
        │    └────┬─────┘      └──────────┘
        │         │
        │         └──► Loop back to Engineer
        │
        ▼
┌─────────────────────────────────────────────────────┐
│  Generate explanation                                │
│  Return results to user                              │
└─────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
AuroRag/
├── backend/                      # Python backend
│   ├── __pycache__/             # Python cache (gitignored)
│   ├── agents.py                 # 4-phase LangGraph agent system
│   ├── api_server.py             # FastAPI REST API server
│   ├── schema_store.py           # Schema management & embeddings
│   ├── ingest.py                 # Data loading and cleaning
│   ├── start.py                  # Python start script
│   └── requirements.txt          # Python dependencies
│
├── frontend/                     # React frontend
│   ├── node_modules/             # Node dependencies (gitignored)
│   ├── src/
│   │   ├── app/
│   │   │   ├── App.tsx           # Main React component
│   │   │   └── components/
│   │   │       ├── ChatSection.tsx      # Chat UI
│   │   │       ├── ProcessPanel.tsx     # Pipeline visualizer
│   │   │       ├── Sidebar.tsx           # Stats sidebar
│   │   │       ├── Header.tsx            # App header
│   │   │       └── ui/                   # shadcn/ui components
│   │   ├── main.tsx              # React entry point
│   │   └── styles/               # CSS files
│   ├── index.html                # HTML template
│   ├── package.json              # Node dependencies
│   ├── vite.config.ts            # Vite configuration
│   └── postcss.config.mjs        # PostCSS config
│
├── dataset/                       # Data files
│   ├── Patient_data - Data.csv           # Patient records (492 rows, 31 columns)
│   └── Patient_data - Description.csv   # Schema descriptions
│
├── .gitignore                    # Git ignore rules
├── README.md                      # This file
└── start.sh                       # Bash start script
```

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

### Required Software

1. **Python 3.8+**
   - Check: `python3 --version`
   - Download: [python.org](https://www.python.org/downloads/)

2. **Node.js 18+ and npm**
   - Check: `node --version` and `npm --version`
   - Download: [nodejs.org](https://nodejs.org/)

3. **Ollama**
   - Download: [ollama.ai](https://ollama.ai/download)
   - **Important**: Must be installed and running before starting the application

4. **Git** (for cloning)
   - Check: `git --version`
   - Download: [git-scm.com](https://git-scm.com/downloads)

### Required Model

- **Llama 3.1 8B** model (downloaded via Ollama)
  ```bash
  ollama pull llama3.1:8b
  ```

---

## 🚀 Installation & Setup

### Windows

#### Step 1: Install Prerequisites

1. **Install Python 3.8+**
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"
   - Verify: Open PowerShell and run `python --version`

2. **Install Node.js**
   - Download from [nodejs.org](https://nodejs.org/)
   - Choose LTS version
   - Verify: `node --version` and `npm --version`

3. **Install Ollama**
   - Download from [ollama.ai/download/windows](https://ollama.ai/download/windows)
   - Run the installer
   - Ollama will start automatically

4. **Download Llama Model**
   - Open PowerShell or Command Prompt
   - Run: `ollama pull llama3.1:8b`
   - Wait for download to complete (~4.9 GB)

#### Step 2: Clone Repository

```powershell
# Open PowerShell or Git Bash
cd C:\Users\YourUsername\Documents
git clone https://github.com/rochitl72/Auro-RAG.git
cd Auro-RAG
```

#### Step 3: Install Dependencies

```powershell
# Install Python dependencies
cd backend
python -m pip install -r requirements.txt

# Install Node dependencies
cd ..\frontend
npm install
```

#### Step 4: Verify Ollama is Running

```powershell
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it:
# Open Ollama from Start Menu, or run:
ollama serve
```

---

### macOS

#### Step 1: Install Prerequisites

1. **Install Python 3.8+**
   ```bash
   # Using Homebrew (recommended)
   brew install python3
   
   # Or download from python.org
   # Verify: python3 --version
   ```

2. **Install Node.js**
   ```bash
   # Using Homebrew
   brew install node
   
   # Or download from nodejs.org
   # Verify: node --version
   ```

3. **Install Ollama**
   ```bash
   # Using Homebrew
   brew install ollama
   
   # Or download from ollama.ai/download/mac
   # Start Ollama:
   ollama serve
   ```

4. **Download Llama Model**
   ```bash
   ollama pull llama3.1:8b
   ```

#### Step 2: Clone Repository

```bash
cd ~/Downloads  # or your preferred directory
git clone https://github.com/rochitl72/Auro-RAG.git
cd Auro-RAG
```

#### Step 3: Install Dependencies

```bash
# Install Python dependencies
cd backend
python3 -m pip install -r requirements.txt

# Install Node dependencies
cd ../frontend
npm install
```

#### Step 4: Verify Ollama is Running

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it:
ollama serve
```

---

### Linux

#### Step 1: Install Prerequisites

1. **Install Python 3.8+**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip
   
   # Fedora/RHEL
   sudo dnf install python3 python3-pip
   ```

2. **Install Node.js**
   ```bash
   # Using NodeSource (recommended)
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   
   # Or use your distribution's package manager
   ```

3. **Install Ollama**
   ```bash
   # Download and install
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Start Ollama service
   ollama serve
   ```

4. **Download Llama Model**
   ```bash
   ollama pull llama3.1:8b
   ```

#### Step 2: Clone Repository

```bash
cd ~/Downloads  # or your preferred directory
git clone https://github.com/rochitl72/Auro-RAG.git
cd Auro-RAG
```

#### Step 3: Install Dependencies

```bash
# Install Python dependencies
cd backend
python3 -m pip install -r requirements.txt

# Install Node dependencies
cd ../frontend
npm install
```

---

## 🏃 Running the Application

### Option 1: Using Start Script (Recommended)

**Windows (PowerShell)**:
```powershell
# Make script executable (if needed)
# Then run:
.\start.sh

# Or use Python script:
python backend\start.py
```

**macOS/Linux**:
```bash
# Make script executable
chmod +x start.sh

# Run the script
./start.sh

# Or use Python script:
python3 backend/start.py
```

This will start both:
- **Backend (FastAPI)**: http://localhost:8000
- **Frontend (React)**: http://localhost:5173

### Option 2: Manual Start

**Terminal 1 - Backend**:
```bash
cd backend
python3 -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

### Access the Application

1. Open your browser
2. Navigate to: **http://localhost:5173**
3. You should see the AuroRag interface

---

## 🔌 API Endpoints

### Health Check
```http
GET /health
```
**Response**:
```json
{
  "status": "ok",
  "system_initialized": true,
  "ollama_available": true
}
```

### Process Query
```http
POST /api/query
Content-Type: application/json

{
  "query": "count patients with Diabetic Retinopathy"
}
```

**Response**:
```json
{
  "query": "count patients with Diabetic Retinopathy",
  "plan": {
    "steps": [...],
    "final_action": "..."
  },
  "relevant_columns": [...],
  "sql_query": "SELECT COUNT(*) as patient_count FROM patient_data WHERE DiagnosisName LIKE '%Diabetic Retinopathy%'",
  "result_df": [{"patient_count": 42}],
  "explanation": "There are **42** patients with Diabetic Retinopathy.",
  "error": "",
  "phases_completed": "inspector"
}
```

### Get Schema Columns
```http
GET /api/schema/columns
```

### Get Data Statistics
```http
GET /api/stats
```
**Response**:
```json
{
  "rows": 492,
  "columns": 31,
  "tables": 1
}
```

---

## 💡 Example Queries

Try these example queries to test the system:

1. **Count queries**:
   - `"Count patients with Diabetic Retinopathy"`
   - `"How many patients have Glaucoma?"`
   - `"Count patients from Retina Clinic"`

2. **Patient-specific queries**:
   - `"what drug is the patient E5F99 taking?"`
   - `"What is the diagnosis for patient E5F86?"`
   - `"Show patient E5F99 details"`

3. **Condition-based queries**:
   - `"Show me patients with Glaucoma and Hypertension"`
   - `"bring up all cataract patients"`
   - `"Find patients with vision problems in right eye"`

4. **Department queries**:
   - `"How many patients visited the Retina Clinic?"`
   - `"Show patients from Glaucoma Clinic"`

5. **Complex queries**:
   - `"Show patients with both Glaucoma and Hypertension"`
   - `"Count patients with Diabetic Retinopathy in right eye"`

---

## 🛠️ Technology Stack

### Backend
- **FastAPI** (0.104.0+): Modern, fast web framework for building APIs
- **LangGraph** (0.2.0+): Multi-agent workflow orchestration
- **LangChain** (0.3.0+): LLM application framework
- **Ollama** (0.1.0+): Local LLM inference server
- **Pandas** (2.0.0+): Data manipulation and analysis
- **SQLite**: In-memory database for query execution
- **SentenceTransformer** (2.2.0+): Schema embedding (fallback)
- **Uvicorn**: ASGI server for FastAPI

### Frontend
- **React** (18.3.1): UI framework
- **TypeScript**: Type safety
- **Vite** (6.3.5): Build tool and dev server
- **Tailwind CSS** (4.1.12): Utility-first CSS framework
- **shadcn/ui**: High-quality React components
- **Lucide React**: Icon library

### LLM
- **Llama 3.1 8B**: Local large language model via Ollama

---

## 🔧 Troubleshooting

### Issue: "Ollama service not detected"

**Solution**:
```bash
# Start Ollama service
ollama serve

# In another terminal, verify it's running:
curl http://localhost:11434/api/tags
```

### Issue: "llama3.1:8b model not found"

**Solution**:
```bash
# Download the model
ollama pull llama3.1:8b

# Verify it's downloaded:
ollama list
```

### Issue: "ModuleNotFoundError" in Python

**Solution**:
```bash
cd backend
python3 -m pip install -r requirements.txt
```

### Issue: Frontend shows "Failed to fetch"

**Solutions**:
1. Check if backend is running: `curl http://localhost:8000/health`
2. Check CORS settings in `backend/api_server.py`
3. Verify frontend is using correct API URL: `http://localhost:8000`

### Issue: "Port already in use"

**Solution**:
```bash
# Find process using port 8000
# Windows:
netstat -ano | findstr :8000

# macOS/Linux:
lsof -i :8000

# Kill the process and restart
```

### Issue: SQL query errors

**Solutions**:
1. Check backend logs for detailed error messages
2. Verify column names match exactly (case-sensitive)
3. Check if DiagnosisName uses `LIKE '%value%'` for semicolon-separated values
4. Ensure `Anonymous_Uid` is used (not `PatientID`)

### Issue: Slow query processing

**Solutions**:
1. Ensure Ollama is running locally (not remote)
2. Check system resources (CPU, RAM)
3. First query may be slower (schema embeddings generation)
4. Subsequent queries should be faster

---

## 📊 System Requirements

### Minimum Requirements
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Storage**: 10 GB free space
- **OS**: Windows 10+, macOS 10.15+, or Linux

### Recommended Requirements
- **CPU**: 8+ cores
- **RAM**: 16 GB
- **Storage**: 20 GB free space (for model + dependencies)

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **Aravind Eye Hospital** for providing the dataset
- **Ollama** for local LLM inference
- **LangGraph** for multi-agent orchestration
- **shadcn/ui** for beautiful React components

---

## 📞 Support

For issues, questions, or contributions:
- **GitHub Issues**: [Create an issue](https://github.com/rochitl72/Auro-RAG/issues)
- **Repository**: [Auro-RAG on GitHub](https://github.com/rochitl72/Auro-RAG)

---

<div align="center">

**Built with ❤️ for Aravind Eye Hospital**

[⬆ Back to Top](#aurorag---agentic-rag-text-to-sql-system)

</div>
  