import React, { useState } from 'react';
import { Loader2, Info } from 'lucide-react';
import './App.css';

interface ComponentScores {
  financial_health: number;
  market_position: number;
  operational_efficiency: number;
  corporate_structure: number;
  innovation_adaptability: number;
  governance_risk: number;
}

interface CalculationResult {
  score: number;
  components: ComponentScores;
}

function App() {
  const [symbol, setSymbol] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scores, setScores] = useState<CalculationResult | null>(null);

  const calculateScore = async () => {
    if (!symbol) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/calculate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ symbol: symbol.toUpperCase() }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to calculate score');
      }

      setScores(data);
    } catch (err) {
      console.error('Error details:', err);
      setError(err instanceof Error ? err.message : 'An error occurred while calculating the score');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#22c55e';
    if (score >= 60) return '#eab308';
    return '#ef4444';
  };

  return (
    <div className="app">
      <div className="calculator-card">
        <h1>Company Longevity Index</h1>
        <p className="description">
          Calculate a company's long-term sustainability score based on multiple financial
          and operational metrics.
        </p>

        <div className="info-box" style={{ 
          backgroundColor: '#f0f9ff', 
          borderLeft: '4px solid #3b82f6',
          padding: '1rem',
          marginBottom: '1.5rem',
          display: 'flex',
          gap: '12px',
          alignItems: 'flex-start'
        }}>
          <Info className="h-5 w-5" style={{ color: '#3b82f6', flexShrink: 0, marginTop: '2px' }} />
          <p style={{ fontSize: '0.875rem', color: '#1e40af', margin: 0 }}>
            The Longevity Index evaluates companies across six key dimensions: Financial Health (30%), 
            Market Position (20%), Operational Efficiency (15%), Corporate Structure (15%), 
            Innovation & Adaptability (10%), and Governance & Risk (10%). Each component is calculated 
            using real-time market data and industry benchmarks to provide a comprehensive assessment 
            of a company's long-term sustainability.
          </p>
        </div>

        <div className="input-group">
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            placeholder="Enter stock symbol (e.g., AAPL)"
          />
          <button
            onClick={calculateScore}
            disabled={loading || !symbol}
          >
            {loading ? (
              <>
                <Loader2 className="spinner" />
                Calculating...
              </>
            ) : (
              'Calculate Score'
            )}
          </button>
        </div>

        {error && (
          <div className="error-alert">
            {error}
          </div>
        )}

        {scores && (
          <div className="results">
            <div className="main-score">
              <h2>Overall Score</h2>
              <span style={{ color: getScoreColor(scores.score) }}>
                {scores.score}
              </span>
            </div>

            <div className="component-scores">
              {Object.entries(scores.components).map(([key, value]) => (
                <div key={key} className="score-item">
                  <div className="score-header">
                    <span>{key.replace(/_/g, ' ')}</span>
                    <span>{value}</span>
                  </div>
                  <div className="progress-bar" style={{
                    '--progress': `${value}%`,
                    '--color': getScoreColor(value)
                  } as React.CSSProperties} />
                </div>
              ))}
            </div>
          </div>
        )}

        <div style={{ 
          textAlign: 'center', 
          marginTop: '2rem',
          color: '#666'
        }}>
          Made with ❤️ by Veer Dosi © {new Date().getFullYear()}
        </div>
      </div>
    </div>
  );
}

export default App;