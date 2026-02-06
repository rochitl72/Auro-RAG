import { RotateCcw } from 'lucide-react';
import React, { useState } from 'react';
import { ChatSection } from './components/ChatSection';
import { Header } from './components/Header';
import { ProcessPanel } from './components/ProcessPanel';
import { Sidebar } from './components/Sidebar';

const API_URL = 'http://localhost:8000';

interface QueryResult {
  query: string;
  plan: any;
  relevant_columns: Array<{ column_name: string; description: string; similarity: number }>;
  sql_query: string;
  result_df: Array<Record<string, any>>;
  explanation: string;
  error?: string;
  phases_completed: string;
}

export default function App() {
  const [hasQuery, setHasQuery] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [userQuery, setUserQuery] = useState('');

  const processQuery = async (query: string) => {
    if (!query.trim()) return;

    setIsLoading(true);
    setHasQuery(true);
    setCurrentStep(0);
    setUserQuery(query);
    setQueryResult(null);

    try {
      // Step 1: Receptionist - Show as processing
      setCurrentStep(1);

      // Make API call - this processes all phases internally
      // Add timeout controller
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 180000); // 3 minute timeout
      
      const response = await fetch(`${API_URL}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
        signal: controller.signal,
      }).catch((fetchError) => {
        clearTimeout(timeoutId);
        if (fetchError.name === 'AbortError') {
          throw new Error('Request timed out. The query is taking too long. Please try a simpler query or check if Ollama is running properly.');
        }
        throw new Error(`Failed to connect to API: ${fetchError.message}. Make sure the backend is running on ${API_URL}`);
      });
      
      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text().catch(() => response.statusText);
        throw new Error(`API error (${response.status}): ${errorText}`);
      }

      const result: QueryResult = await response.json();

      // Now we have the result, show steps sequentially based on what we have
      // Step 1: Receptionist (we have plan)
      if (result.plan && Object.keys(result.plan).length > 0) {
        setCurrentStep(1);
        setQueryResult({ ...result, plan: result.plan });
        await new Promise(resolve => setTimeout(resolve, 400));
      }

      // Step 2: Librarian (we have relevant columns)
      if (result.relevant_columns && result.relevant_columns.length > 0) {
        setCurrentStep(2);
        setQueryResult({ ...result, relevant_columns: result.relevant_columns });
        await new Promise(resolve => setTimeout(resolve, 400));
      }

      // Step 3: Engineer (we have SQL)
      if (result.sql_query) {
        setCurrentStep(3);
        setQueryResult({ ...result, sql_query: result.sql_query });
        await new Promise(resolve => setTimeout(resolve, 400));
      }

      // Step 4: Inspector (we have results or error)
      setCurrentStep(4);
      setQueryResult(result);

    } catch (error) {
      console.error('Error processing query:', error);
      setQueryResult({
        query,
        plan: {},
        relevant_columns: [],
        sql_query: '',
        result_df: [],
        explanation: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error: error instanceof Error ? error.message : 'Unknown error',
        phases_completed: 'error'
      });
      setCurrentStep(4);
    } finally {
      setIsLoading(false);
    }
  };

  const reset = () => {
    setHasQuery(false);
    setCurrentStep(0);
    setIsLoading(false);
    setQueryResult(null);
    setUserQuery('');
  };

  return (
    <div className="flex h-screen flex-col bg-[#F5F7FA]">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-hidden">
          <div className="h-full p-6">
            {/* Control buttons */}
            <div className="mb-4 flex gap-3">
              <button
                onClick={reset}
                className="flex items-center gap-2 rounded-lg border border-[#90CAF9] bg-white px-4 py-2 text-sm text-[#1565C0] hover:bg-[#E3F2FD] transition-colors"
              >
                <RotateCcw className="h-4 w-4" />
                Reset
              </button>
            </div>

            {/* Main content grid */}
            <div className="grid h-[calc(100%-3.5rem)] grid-cols-2 gap-6">
              {/* Left: Chat section */}
              <ChatSection
                hasQuery={hasQuery}
                userQuery={userQuery}
                queryResult={queryResult}
                isLoading={isLoading}
                onQuerySubmit={processQuery}
              />

              {/* Right: Process panel */}
              <ProcessPanel
                hasQuery={hasQuery}
                currentStep={currentStep}
                queryResult={queryResult}
              />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
