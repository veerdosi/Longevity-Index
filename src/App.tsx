import React, { useState } from 'react';
import { Loader2 } from 'lucide-react';
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
                <Loader2 className="animate-spin" />
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
                  <div className="progress-bar">
                    <div
                      style={{
                        '--progress': `${value}%`,
                        '--color': getScoreColor(value),
                      } as React.CSSProperties}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;