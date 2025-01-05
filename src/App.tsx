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
  const [error, setError] = useState('');
  const [result, setResult] = useState<CalculationResult | null>(null);

  const handleCalculate = async () => {
    if (!symbol) return;
    
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/calculate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ symbol: symbol.toUpperCase() })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to calculate longevity score');
      }

      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'green';
    if (score >= 60) return 'blue';
    if (score >= 40) return '#f0b429';
    return 'red';
  };

  return (
    <div className="app">
      <div className="calculator-card">
        <h1>Company Longevity Index Calculator</h1>
        <p className="description">
          Calculate the long-term sustainability and resilience score for any public company.
        </p>

        <div className="input-group">
          <input
            placeholder="Enter stock symbol (e.g., AAPL)"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            onKeyPress={(e) => e.key === 'Enter' && handleCalculate()}
            disabled={loading}
          />
          <button 
            onClick={handleCalculate}
            disabled={loading || !symbol}
          >
            {loading ? (
              <>
                <Loader2 className="spinner" />
                Calculating
              </>
            ) : (
              'Calculate'
            )}
          </button>
        </div>

        {error && (
          <div className="error-alert">
            {error}
          </div>
        )}

        {result && (
          <div className="results">
            <div className="main-score">
              <h2>Longevity Score:</h2>
              <span style={{ color: getScoreColor(result.score) }}>
                {result.score}
              </span>
              <div 
                className="progress-bar" 
                style={{ 
                  '--progress': `${result.score}%`,
                  '--color': getScoreColor(result.score)
                } as any}
              />
            </div>

            <div className="component-scores">
              <h3>Component Scores</h3>
              {Object.entries(result.components).map(([key, value]) => (
                <div key={key} className="score-item">
                  <div className="score-header">
                    <span>{key.replace(/_/g, ' ')}</span>
                    <span style={{ color: getScoreColor(value) }}>
                      {value}
                    </span>
                  </div>
                  <div 
                    className="progress-bar" 
                    style={{ 
                      '--progress': `${value}%`,
                      '--color': getScoreColor(value)
                    } as any}
                  />
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