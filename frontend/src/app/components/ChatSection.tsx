import { Send } from 'lucide-react';
import { useState } from 'react';

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

interface ChatSectionProps {
  hasQuery: boolean;
  userQuery: string;
  queryResult: QueryResult | null;
  isLoading: boolean;
  onQuerySubmit: (query: string) => void;
}

export function ChatSection({ hasQuery, userQuery, queryResult, isLoading, onQuerySubmit }: ChatSectionProps) {
  const [inputValue, setInputValue] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      onQuerySubmit(inputValue.trim());
      setInputValue('');
    }
  };
  return (
    <div className="flex h-full flex-col rounded-xl bg-white shadow-lg border border-[#E0E0E0]">
      {/* Chat messages area */}
      <div className="flex-1 overflow-y-auto p-6">
        {hasQuery ? (
          <div className="space-y-4">
            {/* User message */}
            {userQuery && (
              <div className="flex justify-end">
                <div className="max-w-[80%] rounded-lg bg-[#E3F2FD] px-4 py-3 shadow-sm">
                  <p className="text-[#0D47A1]">{userQuery}</p>
                </div>
              </div>
            )}
            
            {/* Loading state */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="rounded-lg bg-[#FAFBFC] border border-[#E0E0E0] px-4 py-3">
                  <p className="text-[#546E7A]">Processing your query...</p>
                </div>
              </div>
            )}

            {/* Assistant response */}
            {queryResult && !isLoading && (
              <div className="space-y-3">
                {queryResult.error ? (
                  <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3">
                    <p className="mb-2 text-sm text-red-600">Error:</p>
                    <p className="text-red-800">{queryResult.error}</p>
                  </div>
                ) : (
                  <>
                    <div className="rounded-lg bg-[#FAFBFC] border border-[#E0E0E0] px-4 py-3">
                      <p className="mb-2 text-sm font-semibold text-[#546E7A]">Answer:</p>
                      <p className="text-[#0D47A1] text-base leading-relaxed" dangerouslySetInnerHTML={{ 
                        __html: queryResult.explanation
                          .replace(/\*\*(.*?)\*\*/g, '<strong class="text-[#1565C0]">$1</strong>')
                          .replace(/\n/g, '<br/>') 
                      }} />
                    </div>
                    
                    {/* Result table - only show if explanation suggests it */}
                    {queryResult.result_df && queryResult.result_df.length > 0 && 
                     (queryResult.explanation.toLowerCase().includes("below") || queryResult.result_df.length > 1) && (
                      <div className="rounded-lg border border-[#90CAF9] bg-white overflow-hidden max-h-[400px] overflow-y-auto">
                        <div className="sticky top-0 bg-[#E3F2FD] px-4 py-2 border-b border-[#90CAF9]">
                          <p className="text-xs text-[#546E7A]">Results ({queryResult.result_df.length} row{queryResult.result_df.length !== 1 ? 's' : ''})</p>
                        </div>
                        <table className="w-full">
                          <thead className="bg-[#E3F2FD] sticky top-[40px]">
                            <tr>
                              {Object.keys(queryResult.result_df[0]).map((key) => (
                                <th key={key} className="px-4 py-2 text-left text-xs font-semibold text-[#0D47A1]">
                                  {key}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {queryResult.result_df.slice(0, 20).map((row, idx) => (
                              <tr key={idx} className="border-t border-[#E0E0E0] hover:bg-[#F5F7FA]">
                                {Object.values(row).map((value, colIdx) => (
                                  <td key={colIdx} className="px-4 py-2 text-xs text-[#1E3A5F]">
                                    {value === null || value === undefined ? (
                                      <span className="text-[#90CAF9] italic">null</span>
                                    ) : String(value).length > 100 ? (
                                      <span title={String(value)} className="block max-w-xs truncate">{String(value)}</span>
                                    ) : (
                                      String(value)
                                    )}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {queryResult.result_df.length > 20 && (
                          <div className="px-4 py-2 bg-[#FAFBFC] border-t border-[#E0E0E0] text-xs text-[#546E7A] text-center">
                            Showing first 20 of {queryResult.result_df.length} rows
                          </div>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="flex h-full items-center justify-center text-[#90CAF9]">
            <p className="text-center">
              Ask a question to see the pipeline in action
            </p>
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="border-t border-[#E0E0E0] bg-[#FAFBFC] p-4">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask a question about patient data…"
            disabled={isLoading}
            className="flex-1 rounded-lg border border-[#90CAF9] bg-white px-4 py-3 text-[#0D47A1] placeholder:text-[#90CAF9] focus:outline-none focus:ring-2 focus:ring-[#1565C0] disabled:opacity-50"
          />
          <button 
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="rounded-lg bg-[#1565C0] px-6 py-3 text-white shadow-md hover:bg-[#0D47A1] transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span>{isLoading ? 'Processing...' : 'Ask'}</span>
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
