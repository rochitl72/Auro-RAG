"""
Multi-Agent RAG Text-to-SQL System
Implements 4-phase agentic workflow using LangGraph:
1. Receptionist (Router/Planner)
2. Librarian (Schema Linking)
3. Engineer (SQL Generation)
4. Inspector (Self-Correction)
"""

import json
import re
from typing import Dict, List, TypedDict, Annotated, Literal
try:
    from langchain_community.chat_models import ChatOllama
except ImportError:
    ChatOllama = None
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
import pandas as pd
from pandasql import sqldf
import sqlite3
from io import StringIO

from schema_store import SchemaStore
from ingest import load_and_clean_data


class AgentState(TypedDict):
    """State structure for the agent workflow"""
    user_query: str
    plan: Dict
    relevant_columns: List[Dict]
    sql_query: str
    execution_result: pd.DataFrame
    error_message: str
    execution_count: int
    explanation: str
    current_phase: str


class AgentGraph:
    """
    Multi-agent system for Text-to-SQL conversion using LangGraph.
    """
    
    def __init__(self, schema_store: SchemaStore, df: pd.DataFrame, model_name: str = "llama3.1:8b"):
        """
        Initialize the agent graph.
        
        Args:
            schema_store: SchemaStore instance for column retrieval
            df: DataFrame with patient data
            model_name: Ollama model name
        """
        self.schema_store = schema_store
        self.df = df
        # Use ChatOllama for better compatibility
        try:
            if ChatOllama is not None:
                self.llm = ChatOllama(
                    model=model_name, 
                    base_url="http://localhost:11434", 
                    temperature=0.1,
                    timeout=120.0  # 2 minute timeout for LLM calls
                )
            else:
                raise ImportError("ChatOllama not available")
        except Exception as e:
            print(f"Warning: Could not initialize ChatOllama: {e}")
            print("Falling back to basic Ollama interface...")
            from langchain_community.llms import Ollama
            self.llm = Ollama(
                model=model_name, 
                base_url="http://localhost:11434", 
                temperature=0.1,
                timeout=120.0  # 2 minute timeout
            )
        
        # Create SQLite in-memory database from DataFrame
        self.conn = sqlite3.connect(':memory:')
        self.df.to_sql('patient_data', self.conn, index=False, if_exists='replace')
        
        # Build the graph
        self.graph = self._build_graph()
        self.app = self.graph.compile()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("receptionist", self.receptionist_node)
        workflow.add_node("librarian", self.librarian_node)
        workflow.add_node("engineer", self.engineer_node)
        workflow.add_node("inspector", self.inspector_node)
        
        # Define edges
        workflow.set_entry_point("receptionist")
        workflow.add_edge("receptionist", "librarian")
        workflow.add_edge("librarian", "engineer")
        workflow.add_edge("engineer", "inspector")
        
        # Inspector can loop back to engineer or end
        workflow.add_conditional_edges(
            "inspector",
            self.should_retry,
            {
                "retry": "engineer",
                "end": END
            }
        )
        
        return workflow
    
    def receptionist_node(self, state: AgentState) -> AgentState:
        """
        Phase 1: Receptionist - Decompose complex queries into steps.
        """
        state["current_phase"] = "receptionist"
        
        prompt = """You are a Receptionist agent that breaks down complex medical data queries into simple, executable steps.

User Query: {user_query}

Your task is to analyze this query and create a JSON plan with the following structure:
{{
    "steps": [
        {{
            "step_number": 1,
            "action": "filter|count|aggregate|join",
            "description": "Clear description of what this step does",
            "filters": {{"column": "column_name", "condition": "value or condition"}},
            "target": "what we're looking for"
        }}
    ],
    "final_action": "what the final result should be"
}}

Important:
- Break complex queries into simple steps
- Identify what columns might be needed
- Specify filter conditions clearly
- For diagnosis queries, remember that DiagnosisName contains semicolon-separated values

Return ONLY valid JSON, no additional text."""

        try:
            # Handle both ChatOllama and regular Ollama
            prompt_text = prompt.format(user_query=state["user_query"])
            is_chat_model = ChatOllama is not None and isinstance(self.llm, ChatOllama)
            
            print(f"📋 Receptionist: Processing query plan...")
            
            if is_chat_model or (hasattr(self.llm, 'invoke') and 'Chat' in type(self.llm).__name__):
                messages = [HumanMessage(content=prompt_text)]
                response_obj = self.llm.invoke(messages)
                response = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)
            else:
                response = self.llm.invoke(prompt_text)
            
            print(f"✅ Receptionist: Received response ({len(response)} chars)")
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
            else:
                # Fallback: create a simple plan
                plan = {
                    "steps": [{
                        "step_number": 1,
                        "action": "filter",
                        "description": f"Process query: {state['user_query']}",
                        "filters": {},
                        "target": state["user_query"]
                    }],
                    "final_action": "Return results"
                }
            
            state["plan"] = plan
            state["execution_count"] = 0
            
        except Exception as e:
            print(f"❌ Receptionist error: {e}")
            import traceback
            traceback.print_exc()
            # Create a minimal plan
            state["plan"] = {
                "steps": [{"step_number": 1, "action": "query", "description": state["user_query"]}],
                "final_action": "Execute query"
            }
        
        return state
    
    def librarian_node(self, state: AgentState) -> AgentState:
        """
        Phase 2: Librarian - Use LLM to find relevant columns based on query and plan.
        """
        state["current_phase"] = "librarian"
        
        # Build schema context for LLM (limit to avoid token limits)
        schema_info = []
        for col_name, col_info in self.schema_store.column_info.items():
            desc = col_info.get('description', '')
            # Truncate description to keep prompt manageable
            desc_short = desc[:150] if len(desc) > 150 else desc
            schema_info.append(f"- {col_name}: {desc_short}")
        
        schema_text = "\n".join(schema_info)
        
        # If schema is too long, truncate to first 40 columns
        if len(schema_text) > 8000:
            schema_info = schema_info[:40]
            schema_text = "\n".join(schema_info) + "\n... (and more columns)"
        
        # Build query context
        query_context = state["user_query"]
        if "plan" in state and "steps" in state["plan"]:
            plan_steps = "\n".join([f"Step {s.get('step_number', '?')}: {s.get('description', '')}" 
                                   for s in state["plan"].get("steps", [])])
            query_context += f"\n\nPlan:\n{plan_steps}"
        
        prompt = f"""You are a Schema Librarian. Given a user query and execution plan, identify the most relevant database columns.

User Query and Plan:
{query_context}

Available Database Columns:
{schema_text}

Based on the query and plan, identify the top 8-10 most relevant columns needed to answer this query.
Return ONLY a JSON array of column names in order of relevance, like: ["Column1", "Column2", "Column3", ...]

Do not include explanations, just the JSON array. Example: ["Anonymous_Uid", "Drugname", "DiagnosisName"]"""

        try:
            is_chat_model = ChatOllama is not None and isinstance(self.llm, ChatOllama)
            
            print(f"📚 Librarian: Selecting relevant columns...")
            
            if is_chat_model or (hasattr(self.llm, 'invoke') and 'Chat' in type(self.llm).__name__):
                messages = [HumanMessage(content=prompt)]
                response_obj = self.llm.invoke(messages)
                response = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)
            else:
                response = self.llm.invoke(prompt)
            
            print(f"✅ Librarian: Selected columns from response")
            
            # Extract JSON array from response
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                selected_columns = json.loads(json_match.group())
            else:
                # Try to extract column names from text
                selected_columns = []
                for col_name in self.schema_store.column_info.keys():
                    if col_name.lower() in response.lower():
                        selected_columns.append(col_name)
                        if len(selected_columns) >= 10:
                            break
            
            # Build relevant_columns with full info
            relevant_cols = []
            for col_name in selected_columns[:10]:
                if col_name in self.schema_store.column_info:
                    col_info = self.schema_store.column_info[col_name]
                    relevant_cols.append({
                        'column_name': col_name,
                        'description': col_info.get('description', ''),
                        'example': col_info.get('example', ''),
                        'similarity': 1.0 - (selected_columns.index(col_name) * 0.1)  # Decreasing relevance
                    })
            
            # If no columns found, use a default set
            if not relevant_cols:
                default_cols = ['Anonymous_Uid', 'Drugname', 'DiagnosisName']
                for col_name in default_cols:
                    if col_name in self.schema_store.column_info:
                        relevant_cols.append({
                            'column_name': col_name,
                            'description': self.schema_store.column_info[col_name].get('description', ''),
                            'similarity': 0.9
                        })
            
            state["relevant_columns"] = relevant_cols
            
        except Exception as e:
            print(f"Librarian error: {e}")
            # Fallback to schema store method if LLM fails
            query_text = state["user_query"]
            if "plan" in state and "steps" in state["plan"]:
                for step in state["plan"]["steps"]:
                    query_text += " " + step.get("description", "")
            relevant_cols = self.schema_store.find_relevant_columns(query_text, top_k=10)
            state["relevant_columns"] = relevant_cols
        
        return state
    
    def engineer_node(self, state: AgentState) -> AgentState:
        """
        Phase 3: Engineer - Generate SQL query from plan and relevant columns.
        Uses LLM to generate SQL, with error feedback for retries.
        """
        state["current_phase"] = "engineer"
        state["execution_count"] = state.get("execution_count", 0) + 1
        
        # If there's an error from previous attempt, include it in the prompt
        error_context = ""
        if state.get("error_message") and state.get("execution_count", 0) > 1:
            error_context = f"\n\nPREVIOUS ATTEMPT FAILED:\nError: {state.get('error_message')}\nFailed SQL: {state.get('sql_query', 'N/A')}\n\nPlease fix the SQL query based on this error."
        
        # Build column context from relevant columns
        column_context = "\n".join([
            f"- {col['column_name']}: {col['description']}"
            for col in state["relevant_columns"][:10]  # Use top 10 columns
        ])
        
        # Also include all available columns for reference
        all_columns = list(self.schema_store.column_info.keys())
        all_columns_text = ", ".join(all_columns)
        
        # Get few-shot examples
        few_shot_examples = self._get_few_shot_examples()
        
        prompt = """You are a SQL Engineer agent. Generate a SQLite query based on the user's request.

Relevant Columns (most likely needed):
{column_context}

All Available Columns: {all_columns}

User Query: {user_query}

Plan: {plan}
{error_context}

Few-Shot Examples:
{few_shot_examples}

IMPORTANT INFORMATION:
- Table name: 'patient_data'
- Patient ID column: 'Anonymous_Uid' (NOT PatientID, NOT patient_id, NOT patientId)
- DiagnosisName contains semicolon-separated values, so use LIKE '%value%' for searching
- Handle NULL values with: IS NOT NULL or IS NULL
- Column names use underscores (e.g., Anonymous_Uid, DiagnosisName, Revalue, Levalue, Drugname)
- When filtering by patient ID like 'E5F99', use: WHERE Anonymous_Uid = 'E5F99'
- Always use exact column names from the Available Columns list above

CRITICAL: Return ONLY the SQL query, nothing else. No explanations, no markdown, just the SQL statement.
Start with SELECT and end properly. Use 'Anonymous_Uid' for patient ID filtering.

Generate the SQL query:"""

        try:
            prompt_text = prompt.format(
                column_context=column_context,
                all_columns=all_columns_text,
                user_query=state["user_query"],
                plan=json.dumps(state.get("plan", {}), indent=2),
                error_context=error_context,
                few_shot_examples=few_shot_examples
            )
            
            # Handle both ChatOllama and regular Ollama
            is_chat_model = ChatOllama is not None and isinstance(self.llm, ChatOllama)
            
            print(f"🔧 Engineer: Generating SQL query (attempt {state.get('execution_count', 1)})...")
            
            if is_chat_model or (hasattr(self.llm, 'invoke') and 'Chat' in type(self.llm).__name__):
                messages = [HumanMessage(content=prompt_text)]
                response_obj = self.llm.invoke(messages)
                response = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)
            else:
                response = self.llm.invoke(prompt_text)
            
            print(f"✅ Engineer: Received SQL response ({len(response)} chars)")
            
            # Extract SQL query - try multiple patterns
            sql_query = None
            response_clean = response.strip()
            
            # Pattern 1: SQL in code blocks (```sql ... ```)
            code_block = re.search(r'```(?:sql)?\s*\n(.*?)\n```', response_clean, re.DOTALL | re.IGNORECASE)
            if code_block:
                sql_query = code_block.group(1).strip()
            
            # Pattern 2: SQL ending with semicolon
            if not sql_query:
                sql_match = re.search(r'(SELECT\s+.*?);', response_clean, re.DOTALL | re.IGNORECASE)
                if sql_match:
                    sql_query = sql_match.group(1).strip()
            
            # Pattern 3: SQL without semicolon (until double newline or end)
            if not sql_query:
                sql_match = re.search(r'(SELECT\s+.*?)(?:\n\n|\n[A-Z][a-z]+:|$)', response_clean, re.DOTALL | re.IGNORECASE)
                if sql_match:
                    sql_query = sql_match.group(1).strip()
            
            # Pattern 4: Extract SQL-like lines (more robust)
            if not sql_query:
                lines = response_clean.split('\n')
                sql_lines = []
                in_sql = False
                for line in lines:
                    line_clean = line.strip()
                    if not line_clean:
                        if in_sql:
                            break
                        continue
                    line_upper = line_clean.upper()
                    if line_upper.startswith('SELECT'):
                        in_sql = True
                        sql_lines = [line_clean]
                    elif in_sql:
                        if any(line_upper.startswith(kw) for kw in ['SELECT', 'FROM', 'WHERE', 'GROUP', 'ORDER', 'LIMIT', 'HAVING']):
                            sql_lines.append(line_clean)
                        elif ';' in line_clean:
                            sql_lines.append(line_clean.split(';')[0])
                            break
                        elif line_upper.startswith(('THE', 'HERE', 'NOTE', 'IMPORTANT', 'REMEMBER')):
                            break
                        else:
                            sql_lines.append(line_clean)
                
                if sql_lines:
                    sql_query = ' '.join(sql_lines).strip()
                    # Remove trailing semicolon if present
                    sql_query = sql_query.rstrip(';').strip()
            
            # If still no SQL found, ask LLM to retry with clearer instructions
            if not sql_query or len(sql_query) < 10 or not sql_query.upper().startswith('SELECT'):
                print(f"⚠️  Could not extract valid SQL from LLM response")
                print(f"   Response: {response[:300]}...")
                
                # Retry with clearer prompt
                retry_prompt = f"""The previous response was not a valid SQL query. Please generate ONLY a SQLite query for this request:

User Query: {state["user_query"]}
Plan: {json.dumps(state.get("plan", {}), indent=2)}

Available Columns: {all_columns_text}

Return ONLY the SQL query, no other text. Start with SELECT."""
                
                try:
                    if is_chat_model:
                        retry_response_obj = self.llm.invoke([HumanMessage(content=retry_prompt)])
                        retry_response = retry_response_obj.content if hasattr(retry_response_obj, 'content') else str(retry_response_obj)
                    else:
                        retry_response = self.llm.invoke(retry_prompt)
                    
                    # Try to extract SQL from retry response
                    retry_sql = re.search(r'(SELECT\s+.*?)(?:;|\n\n|$)', retry_response, re.DOTALL | re.IGNORECASE)
                    if retry_sql:
                        sql_query = retry_sql.group(1).strip().rstrip(';')
                except:
                    pass
            
            # Final validation - if still no valid SQL, set error for retry mechanism
            if not sql_query or len(sql_query) < 10 or not sql_query.upper().startswith('SELECT'):
                state["error_message"] = f"Could not generate valid SQL query. LLM response: {response[:200]}"
                state["sql_query"] = ""
                return state
            
            # Clean up the SQL (remove markdown formatting)
            sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
            sql_query = re.sub(r'\s+', ' ', sql_query)  # Normalize whitespace
            
            state["sql_query"] = sql_query
            
        except Exception as e:
            print(f"❌ Engineer error: {e}")
            import traceback
            traceback.print_exc()
            state["sql_query"] = ""
            state["error_message"] = f"SQL generation failed: {str(e)}"
        
        return state
    
    def inspector_node(self, state: AgentState) -> AgentState:
        """
        Phase 4: Inspector - Execute SQL and validate results.
        """
        state["current_phase"] = "inspector"
        
        sql_query = state.get("sql_query", "")
        max_retries = 3
        
        if state.get("execution_count", 0) > max_retries:
            state["error_message"] = "Maximum retry attempts reached"
            state["execution_result"] = pd.DataFrame()
            state["explanation"] = "Failed to generate valid SQL after multiple attempts."
            return state
        
        try:
            # Execute SQL
            result_df = pd.read_sql_query(sql_query, self.conn)
            
            # Success!
            state["execution_result"] = result_df
            state["error_message"] = ""
            
            # Generate explanation
            explanation = self._generate_explanation(state)
            state["explanation"] = explanation
            
        except Exception as e:
            error_msg = str(e)
            state["error_message"] = error_msg
            state["execution_result"] = pd.DataFrame()
            
            # If this is the first attempt, we'll retry - let LLM fix the error
            if state.get("execution_count", 0) < max_retries:
                print(f"⚠️  SQL execution error: {error_msg}")
                print(f"   Failed SQL: {sql_query[:150]}")
                # Error will be fed back to Engineer node for retry
        
        return state
    
    def should_retry(self, state: AgentState) -> Literal["retry", "end"]:
        """
        Determine if we should retry SQL generation or end.
        """
        if state.get("error_message") and state.get("execution_count", 0) < 3:
            # Check if error is recoverable
            error = state["error_message"].lower()
            if any(keyword in error for keyword in ["no such column", "syntax error", "no such table"]):
                return "retry"
        
        return "end"
    
    def _get_few_shot_examples(self) -> str:
        """Return few-shot examples for SQL generation"""
        return """
Example 1:
Query: "Count patients with Diabetic Retinopathy"
SQL: SELECT COUNT(*) as patient_count FROM patient_data WHERE DiagnosisName LIKE '%Diabetic Retinopathy%'

Example 2:
Query: "Show patients with vision problems in right eye"
SQL: SELECT Anonymous_Uid, Revalue, DiagnosisName FROM patient_data WHERE Revalue IS NOT NULL AND Revalue != 'NULL' LIMIT 20

Example 3:
Query: "Count patients with both Glaucoma and Hypertension"
SQL: SELECT COUNT(*) as patient_count FROM patient_data WHERE DiagnosisName LIKE '%Glaucoma%' AND DiagnosisName LIKE '%Hypertension%'

Example 4:
Query: "Show patients from Retina Clinic"
SQL: SELECT * FROM patient_data WHERE deptname LIKE '%RETINA CLINIC%' LIMIT 20

Example 5:
Query: "what drug is the patient E5F99 taking?"
SQL: SELECT Drugname FROM patient_data WHERE Anonymous_Uid = 'E5F99' AND Drugname IS NOT NULL AND Drugname != 'NULL'

Example 6:
Query: "Show patient E5F86 diagnosis"
SQL: SELECT DiagnosisName FROM patient_data WHERE Anonymous_Uid = 'E5F86' AND DiagnosisName IS NOT NULL
"""
    
    def _generate_explanation(self, state: AgentState) -> str:
        """Use LLM to generate natural, concise explanation of results"""
        result_df = state.get("execution_result")
        user_query = state.get("user_query", "")
        
        if result_df is None:
            return "No results found - query execution returned no data."
        
        try:
            if hasattr(result_df, 'empty') and result_df.empty:
                return "No matching records found for your query."
        except:
            return "No results found - unable to process query results."
        
        num_rows = len(result_df)
        
        # Convert results to readable format
        if num_rows == 0:
            return "No matching records found for your query."
        
        # For small results, show the data; for large results, show summary
        if num_rows <= 5:
            results_text = result_df.to_string(index=False)
        else:
            results_text = f"Found {num_rows} rows. First 3 rows:\n" + result_df.head(3).to_string(index=False)
        
        # Build prompt for LLM to generate explanation
        prompt = f"""Given the user's query and the SQL query results, provide a concise, direct answer in natural language.

User Query: {user_query}

Query Results ({num_rows} row{'s' if num_rows != 1 else ''}):
{results_text}

Provide a direct, concise answer to the user's question. 
- If the query asks for a specific value (like a drug name or count), give that value directly
- If the query asks for a list, summarize the key findings
- Do not explain the SQL or the process, just answer the question
- Use **bold** for important values
- Keep it brief and natural

Answer:"""

        try:
            is_chat_model = ChatOllama is not None and isinstance(self.llm, ChatOllama)
            
            if is_chat_model or (hasattr(self.llm, 'invoke') and 'Chat' in type(self.llm).__name__):
                messages = [HumanMessage(content=prompt)]
                response_obj = self.llm.invoke(messages)
                explanation = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)
            else:
                explanation = self.llm.invoke(prompt)
            
            return explanation.strip()
            
        except Exception as e:
            print(f"Explanation generation error: {e}")
            # Fallback to simple response
            if num_rows == 1 and len(result_df.columns) == 1:
                val = result_df.iloc[0, 0]
                return f"**{val}**"
            else:
                return f"Found {num_rows} record(s). See results below."
    
    def query(self, user_query: str) -> Dict:
        """
        Execute a query through the agent workflow.
        
        Args:
            user_query: Natural language query
            
        Returns:
            Dictionary with results and metadata
        """
        initial_state = {
            "user_query": user_query,
            "plan": {},
            "relevant_columns": [],
            "sql_query": "",
            "execution_result": pd.DataFrame(),
            "error_message": "",
            "execution_count": 0,
            "explanation": "",
            "current_phase": ""
        }
        
        # Run the workflow
        final_state = self.app.invoke(initial_state)
        
        return {
            "query": user_query,
            "plan": final_state.get("plan", {}),
            "relevant_columns": final_state.get("relevant_columns", []),
            "sql_query": final_state.get("sql_query", ""),
            "result_df": final_state.get("execution_result", pd.DataFrame()),
            "explanation": final_state.get("explanation", ""),
            "error": final_state.get("error_message", ""),
            "phases_completed": final_state.get("current_phase", "")
        }
    
    def __del__(self):
        """Clean up database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()


if __name__ == "__main__":
    # Test the agents
    from ingest import load_and_clean_data, load_schema_description
    from schema_store import SchemaStore
    
    print("Loading data...")
    df = load_and_clean_data()
    schema_df = load_schema_description()
    
    print("Building schema store...")
    store = SchemaStore(schema_df)
    
    print("Initializing agent graph...")
    agent = AgentGraph(store, df)
    
    # Test query
    test_query = "Count patients with Diabetic Retinopathy"
    print(f"\nTesting query: '{test_query}'")
    result = agent.query(test_query)
    
    print(f"\nSQL: {result['sql_query']}")
    print(f"\nResult:\n{result['result_df']}")
    print(f"\nExplanation:\n{result['explanation']}")
