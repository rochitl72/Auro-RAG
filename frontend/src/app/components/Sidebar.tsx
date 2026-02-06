import { Database, Activity } from 'lucide-react';
import { useState, useEffect } from 'react';

const API_URL = 'http://localhost:8000';

interface DataStats {
  rows: number;
  columns: number;
  tables: number;
}

export function Sidebar() {
  const [stats, setStats] = useState<DataStats | null>(null);
  const [ollamaStatus, setOllamaStatus] = useState<boolean>(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    // Fetch data statistics with timeout
    const fetchStats = async () => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
      
      try {
        const response = await fetch(`${API_URL}/api/stats`, {
          signal: controller.signal
        });
        if (response.ok && mounted) {
          const data = await response.json();
          setStats(data);
        }
      } catch (error) {
        if (error instanceof Error && error.name !== 'AbortError') {
          console.error('Error fetching stats:', error);
        }
        // Set default values on error
        if (mounted) {
          setStats({ rows: 0, columns: 0, tables: 0 });
        }
      } finally {
        clearTimeout(timeoutId);
      }
    };

    // Check Ollama status with timeout
    const checkOllama = async () => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
      
      try {
        const response = await fetch(`${API_URL}/health`, {
          signal: controller.signal
        });
        if (response.ok && mounted) {
          const data = await response.json();
          setOllamaStatus(data.ollama_available || false);
        }
      } catch (error) {
        if (error instanceof Error && error.name !== 'AbortError') {
          console.error('Error checking Ollama:', error);
        }
        if (mounted) {
          setOllamaStatus(false);
        }
      } finally {
        clearTimeout(timeoutId);
        if (mounted) {
          setLoading(false);
        }
      }
    };

    // Run both fetches in parallel
    Promise.all([fetchStats(), checkOllama()]).catch(() => {
      if (mounted) {
        setLoading(false);
      }
    });

    // Refresh stats every 30 seconds
    const interval = setInterval(() => {
      if (mounted) {
        fetchStats();
        checkOllama();
      }
    }, 30000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="w-64 border-r border-[#E0E0E0] bg-[#FAFBFC] p-4">
      <div className="space-y-4">
        <div className="rounded-lg border border-[#90CAF9] bg-white p-4">
          <div className="flex items-center gap-2 mb-2">
            <Database className="h-5 w-5 text-[#1565C0]" />
            <h3 className="text-sm text-[#0D47A1]">Data Status</h3>
          </div>
          <div className="space-y-1 text-sm text-[#546E7A]">
            {loading ? (
              <>
                <p>Loading...</p>
              </>
            ) : stats ? (
              <>
                <p>Rows: {stats.rows.toLocaleString()}</p>
                <p>Columns: {stats.columns}</p>
                <p>Tables: {stats.tables}</p>
              </>
            ) : (
              <>
                <p>Rows: -</p>
                <p>Columns: -</p>
                <p>Tables: -</p>
              </>
            )}
          </div>
        </div>
        
        <div className="rounded-lg border border-[#90CAF9] bg-white p-4">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="h-5 w-5 text-[#1565C0]" />
            <h3 className="text-sm text-[#0D47A1]">System</h3>
          </div>
          <div className="flex items-center gap-2">
            <div className={`h-2 w-2 rounded-full ${ollamaStatus ? 'bg-[#4CAF50]' : 'bg-[#F44336]'}`} />
            <p className="text-sm text-[#546E7A]">
              {loading ? 'Checking...' : ollamaStatus ? 'Ollama running' : 'Ollama offline'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
