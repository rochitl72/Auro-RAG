"""
FastAPI Backend Server for React Frontend
Provides REST API endpoints for the Agentic RAG Text-to-SQL System
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from ingest import load_and_clean_data, load_schema_description
from schema_store import SchemaStore
from agents import AgentGraph

app = FastAPI(title="AuroRag API", version="1.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174", 
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
agent_graph: Optional[AgentGraph] = None
schema_store: Optional[SchemaStore] = None
df = None


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    query: str
    plan: Dict[str, Any]
    relevant_columns: List[Dict[str, Any]]
    sql_query: str
    result_df: List[Dict[str, Any]]  # Converted to list of dicts
    explanation: str
    error: Optional[str] = None
    phases_completed: str


@app.on_event("startup")
async def startup_event():
    """Initialize the agent system on startup"""
    global agent_graph, schema_store, df
    
    print("Initializing AuroRag system...")
    try:
        # Load data
        df = load_and_clean_data()
        schema_df = load_schema_description()
        
        # Build schema store
        print("Building schema store...")
        schema_store = SchemaStore(schema_df)
        
        # Initialize agent graph
        print("Initializing agent graph...")
        agent_graph = AgentGraph(schema_store, df)
        
        print("✅ System initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing system: {e}")
        raise


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "AuroRag API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check with system status"""
    # Check if Ollama is actually running
    ollama_available = False
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            ollama_available = True
    except:
        pass
    
    return {
        "status": "ok",
        "system_initialized": agent_graph is not None,
        "ollama_available": ollama_available
    }


@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a natural language query through the agent system
    """
    if agent_graph is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        print(f"\n🔍 Processing query: '{request.query}'")
        # Process query through agent system
        result = agent_graph.query(request.query)
        print(f"✅ Query processed successfully\n")
        
        # Convert DataFrame to list of dicts for JSON serialization
        result_df_list = []
        result_df = result.get("result_df")
        if result_df is not None:
            try:
                if hasattr(result_df, 'empty') and not result_df.empty:
                    result_df_list = result_df.to_dict(orient="records")
                elif isinstance(result_df, list):
                    result_df_list = result_df
            except Exception as e:
                print(f"Warning: Error converting result_df: {e}")
                result_df_list = []
        
        return QueryResponse(
            query=result.get("query", request.query),
            plan=result.get("plan", {}),
            relevant_columns=result.get("relevant_columns", []),
            sql_query=result.get("sql_query", ""),
            result_df=result_df_list,
            explanation=result.get("explanation", ""),
            error=result.get("error", ""),
            phases_completed=result.get("phases_completed", "")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.get("/api/schema/columns")
async def get_schema_columns():
    """Get all available schema columns"""
    if schema_store is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        columns = []
        for col_name, col_info in schema_store.column_info.items():
            columns.append({
                "name": col_name,
                "description": col_info.get("description", ""),
                "example": col_info.get("example", "")
            })
        return {"columns": columns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting schema: {str(e)}")


@app.get("/api/stats")
async def get_data_stats():
    """Get data statistics"""
    if df is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        return {
            "rows": len(df),
            "columns": len(df.columns),
            "tables": 1  # We only have one table: patient_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
