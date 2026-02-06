import { Check, ListTodo, Database, Code, Play } from 'lucide-react';

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

interface ProcessPanelProps {
  hasQuery: boolean;
  currentStep: number; // 0 = none, 1-4 = active step
  queryResult?: QueryResult | null;
}

export function ProcessPanel({ hasQuery, currentStep, queryResult }: ProcessPanelProps) {
  if (!hasQuery) {
    return (
      <div className="flex h-full items-center justify-center rounded-xl bg-white border border-[#E0E0E0] shadow-lg p-8">
        <div className="text-center">
          <div className="mx-auto mb-4 h-16 w-16 rounded-full bg-[#E3F2FD] flex items-center justify-center">
            <Code className="h-8 w-8 text-[#1565C0]" />
          </div>
          <h3 className="mb-2 text-[#0D47A1]">Pipeline Process</h3>
          <p className="text-sm text-[#546E7A]">
            Ask a question to see how your query is processed step by step
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-white border border-[#E0E0E0] shadow-lg flex flex-col h-full">
      <div className="border-b border-[#E0E0E0] px-6 py-4 flex-shrink-0">
        <h2 className="text-[#0D47A1]">Pipeline</h2>
        <p className="mt-1 text-sm text-[#546E7A]">How this answer was built</p>
      </div>

      <div className="p-6 space-y-6 overflow-y-auto flex-1">
        {/* Step 1: Plan */}
        <div className={`rounded-lg border-2 transition-all ${
          currentStep === 1 
            ? 'border-[#1565C0] bg-[#E8F4FC]' 
            : currentStep > 1 && queryResult?.plan?.steps
            ? 'border-[#90CAF9] bg-white' 
            : 'border-[#E0E0E0] bg-[#FAFBFC]'
        }`}>
          <div className="p-4">
            <div className="flex items-start gap-3">
              <div className={`flex h-8 w-8 items-center justify-center rounded-full ${
                currentStep > 1 && queryResult?.plan?.steps ? 'bg-[#1565C0]' : 
                currentStep === 1 ? 'bg-[#90CAF9]' : 'bg-[#E0E0E0]'
              }`}>
                {currentStep > 1 && queryResult?.plan?.steps ? (
                  <Check className="h-5 w-5 text-white" />
                ) : (
                  <span className="text-sm text-white">1</span>
                )}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-[#0D47A1]">Question Decomposition</h3>
                  <span className="rounded-full bg-[#BBDEFB] px-2 py-0.5 text-xs text-[#0D47A1]">
                    Receptionist
                  </span>
                </div>
                {currentStep >= 1 && (
                  <div className="mt-3 rounded-lg bg-[#E3F2FD] p-3 space-y-2">
                    {queryResult?.plan?.steps ? (
                      queryResult.plan.steps.map((step: any, idx: number) => (
                        <div key={idx} className="flex items-start gap-2">
                          <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-[#1565C0]" />
                          <p className="text-sm text-[#0D47A1]">
                            {step.description || `Step ${step.step_number || idx + 1}`}
                          </p>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-[#546E7A]">Processing query plan...</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Step 2: Schema Search */}
        <div className={`rounded-lg border-2 transition-all ${
          currentStep === 2 
            ? 'border-[#1565C0] bg-[#E8F4FC]' 
            : currentStep > 2 && queryResult?.relevant_columns?.length > 0
            ? 'border-[#90CAF9] bg-white' 
            : 'border-[#E0E0E0] bg-[#FAFBFC]'
        }`}>
          <div className="p-4">
            <div className="flex items-start gap-3">
              <div className={`flex h-8 w-8 items-center justify-center rounded-full ${
                currentStep > 2 && queryResult?.relevant_columns?.length > 0 ? 'bg-[#1565C0]' : 
                currentStep === 2 ? 'bg-[#90CAF9]' : 'bg-[#E0E0E0]'
              }`}>
                {currentStep > 2 && queryResult?.relevant_columns?.length > 0 ? (
                  <Check className="h-5 w-5 text-white" />
                ) : (
                  <span className="text-sm text-white">2</span>
                )}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-[#0D47A1]">Schema Search & Columns</h3>
                  <span className="rounded-full bg-[#BBDEFB] px-2 py-0.5 text-xs text-[#0D47A1]">
                    Librarian
                  </span>
                </div>
                {currentStep >= 2 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {queryResult?.relevant_columns && queryResult.relevant_columns.length > 0 ? (
                      queryResult.relevant_columns.slice(0, 6).map((col) => (
                        <span key={col.column_name} className="inline-flex items-center gap-1.5 rounded-md border border-[#1565C0] bg-white px-3 py-1.5 text-sm text-[#0D47A1]">
                          <Database className="h-3.5 w-3.5" />
                          {col.column_name}
                        </span>
                      ))
                    ) : (
                      <p className="text-sm text-[#546E7A]">Searching for relevant columns...</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Step 3: Query Generation */}
        <div className={`rounded-lg border-2 transition-all ${
          currentStep === 3 
            ? 'border-[#1565C0] bg-[#E8F4FC]' 
            : currentStep > 3 && queryResult?.sql_query
            ? 'border-[#90CAF9] bg-white' 
            : 'border-[#E0E0E0] bg-[#FAFBFC]'
        }`}>
          <div className="p-4">
            <div className="flex items-start gap-3">
              <div className={`flex h-8 w-8 items-center justify-center rounded-full ${
                currentStep > 3 && queryResult?.sql_query ? 'bg-[#1565C0]' : 
                currentStep === 3 ? 'bg-[#90CAF9]' : 'bg-[#E0E0E0]'
              }`}>
                {currentStep > 3 && queryResult?.sql_query ? (
                  <Check className="h-5 w-5 text-white" />
                ) : (
                  <span className="text-sm text-white">3</span>
                )}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-[#0D47A1]">Query Generation</h3>
                  <span className="rounded-full bg-[#BBDEFB] px-2 py-0.5 text-xs text-[#0D47A1]">
                    Engineer
                  </span>
                </div>
                {currentStep >= 3 && (
                  <div className="mt-3 rounded-lg bg-[#0D2B4A] p-4">
                    <pre className="text-sm text-[#E3F2FD] overflow-x-auto whitespace-pre-wrap">
                      {queryResult?.sql_query || 'Generating SQL query...'}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Step 4: Execution & Result */}
        <div className={`rounded-lg border-2 transition-all ${
          currentStep === 4 
            ? 'border-[#1565C0] bg-[#E8F4FC]' 
            : currentStep >= 4 && (queryResult?.result_df || queryResult?.error)
            ? 'border-[#90CAF9] bg-white' 
            : 'border-[#E0E0E0] bg-[#FAFBFC]'
        }`}>
          <div className="p-4">
            <div className="flex items-start gap-3">
              <div className={`flex h-8 w-8 items-center justify-center rounded-full ${
                currentStep >= 4 && (queryResult?.result_df || queryResult?.error) ? 'bg-[#1565C0]' : 
                currentStep === 4 ? 'bg-[#90CAF9]' : 'bg-[#E0E0E0]'
              }`}>
                {currentStep >= 4 && (queryResult?.result_df || queryResult?.error) ? (
                  <Check className="h-5 w-5 text-white" />
                ) : (
                  <span className="text-sm text-white">4</span>
                )}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-[#0D47A1]">Execution & Result</h3>
                  <span className="rounded-full bg-[#BBDEFB] px-2 py-0.5 text-xs text-[#0D47A1]">
                    Inspector
                  </span>
                </div>
                {currentStep >= 4 && (
                  <div className="mt-3 space-y-3">
                    {queryResult?.error ? (
                      <div className="flex items-center gap-2 text-sm text-red-600">
                        <span>❌ Query execution failed</span>
                      </div>
                    ) : queryResult?.result_df && queryResult.result_df.length > 0 ? (
                      <>
                        <div className="flex items-center gap-2 text-sm text-[#1565C0]">
                          <Check className="h-4 w-4" />
                          <span>Query executed successfully • {queryResult.result_df.length} row(s) returned</span>
                        </div>
                        <div className="rounded-lg border border-[#90CAF9] overflow-hidden max-h-[400px] overflow-y-auto">
                          <table className="w-full">
                            <thead className="bg-[#E3F2FD] sticky top-0">
                              <tr>
                                {Object.keys(queryResult.result_df[0]).map((key) => (
                                  <th key={key} className="px-4 py-2 text-left text-sm text-[#0D47A1] font-semibold">
                                    {key}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody className="bg-white">
                              {queryResult.result_df.map((row, idx) => (
                                <tr key={idx} className="border-t border-[#E0E0E0] hover:bg-[#F5F7FA]">
                                  {Object.values(row).map((value, colIdx) => (
                                    <td key={colIdx} className="px-4 py-2 text-sm text-[#1E3A5F]">
                                      {value === null || value === undefined ? (
                                        <span className="text-[#90CAF9] italic">null</span>
                                      ) : (
                                        String(value).length > 50 ? (
                                          <span title={String(value)}>{String(value).substring(0, 50)}...</span>
                                        ) : (
                                          String(value)
                                        )
                                      )}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </>
                    ) : (
                      <div className="flex items-center gap-2 text-sm text-[#546E7A]">
                        <span>No results returned</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
