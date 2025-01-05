import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { Loader2 } from "lucide-react";

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

const LongevityCalculator = () => {
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
        if (response.status === 429) {
          throw new Error('Rate limit exceeded. Please try again in a few minutes.');
        }
        throw new Error(data.detail || data.error || 'Failed to calculate longevity score');
      }

      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && symbol && !loading) {
      handleCalculate();
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-blue-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-4">
      <Card>
        <CardHeader>
          <CardTitle>Company Longevity Index Calculator</CardTitle>
          <CardDescription>
            Calculate the long-term sustainability and resilience score for any public company.
            Enter a stock symbol to begin.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 mb-4">
            <Input
              placeholder="Enter stock symbol (e.g., AAPL)"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              onKeyPress={handleKeyPress}
              className="flex-1"
              disabled={loading}
            />
            <Button 
              onClick={handleCalculate}
              disabled={loading || !symbol}
              className="min-w-[120px]"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Calculating
                </>
              ) : (
                'Calculate'
              )}
            </Button>
          </div>

          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {result && (
            <div className="space-y-6 mt-6">
              <div>
                <div className="flex items-baseline gap-2 mb-2">
                  <h3 className="text-2xl font-semibold">Longevity Score:</h3>
                  <span className={`text-2xl font-bold ${getScoreColor(result.score)}`}>
                    {result.score}
                  </span>
                </div>
                <Progress 
                  value={result.score} 
                  className="h-4"
                />
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Component Scores</h3>
                <div className="grid gap-4">
                  {Object.entries(result.components).map(([key, value]) => (
                    <div key={key} className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="capitalize font-medium">
                          {key.replace(/_/g, ' ')}
                        </span>
                        <span className={`font-semibold ${getScoreColor(value)}`}>
                          {value}
                        </span>
                      </div>
                      <Progress 
                        value={value} 
                        className="h-2"
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default LongevityCalculator;