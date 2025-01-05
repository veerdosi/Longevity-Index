from http.server import BaseHTTPRequestHandler
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import os
import requests
from typing import Dict, Any, List
import logging
import asyncio

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompanyData(BaseModel):
    symbol: str

async def fetch_peer_data(peer: str, api_key: str) -> Dict[str, Any]:
    """Fetch financial data for a peer company"""
    try:
        base_url = "https://financialmodelingprep.com/api/v3"
        endpoints = {
            'metrics': f"/key-metrics-ttm/{peer}",
            'ratios': f"/ratios-ttm/{peer}"
        }
        
        peer_data = {}
        for endpoint_name, endpoint in endpoints.items():
            response = requests.get(
                f"{base_url}{endpoint}",
                params={'apikey': api_key},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list) and data:
                peer_data.update(data[0])
                
        return peer_data
    except Exception as e:
        logger.warning(f"Error fetching peer data for {peer}: {str(e)}")
        return {}

async def fetch_industry_averages(peers: List[str], api_key: str) -> Dict[str, float]:
    """Fetch and calculate industry averages from peer companies"""
    industry_data = {
        'industryProfitMargin': [],
        'industryRevenueGrowth': [],
        'industryAssetTurnover': [],
        'industryOperatingMargin': [],
        'industryRDIntensity': []
    }
    
    # Create tasks for all peer data fetches
    tasks = [fetch_peer_data(peer, api_key) for peer in peers[:5]]
    peer_responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    for response in peer_responses:
        if isinstance(response, Dict):  # Skip any failed requests
            for metric in industry_data.keys():
                base_metric = metric.replace('industry', '').lower()
                if base_metric in response:
                    industry_data[metric].append(response[base_metric])

    # Calculate averages
    return {
        metric: sum(values) / len(values) if values else None 
        for metric, values in industry_data.items()
    }

def handle_request(request):
    try:
        if request.get("method", "") == "OPTIONS":
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type",
                },
                "body": ""
            }

        # Get API key from environment variable
        api_key = os.environ.get('FINANCIAL_API_KEY')
        if not api_key:
            return {
                "statusCode": 500,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Content-Type": "application/json"
                },
                "body": json.dumps({"error": "API key not configured"})
            }

        # Get request body
        body = json.loads(request.get("body", "{}"))
        company_data = CompanyData(**body)
        
        # Initialize calculator
        calculator = LongevityIndex()
        
        # Fetch data and calculate
        result = asyncio.run(calculate_longevity(company_data))
        
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps(result)
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({"error": str(e)})
        }

def handler(request, context):
    return handle_request(request)

class CompanyData(BaseModel):
    symbol: str

class LongevityIndex:
    def __init__(self):
        self.weights = {
            'financial_health': 0.30,
            'market_position': 0.20,
            'operational_efficiency': 0.15,
            'corporate_structure': 0.15,
            'innovation_adaptability': 0.10,
            'governance_risk': 0.10
        }

    def calculate_financial_health(self, data: Dict[str, Any]) -> float:
        try:
            factors = {
                'current_ratio': {
                    'weight': 0.20,
                    'value': data.get('currentRatio', 0),
                    'target': 1.5,
                    'excellent': 2.0
                },
                'debt_to_equity': {
                    'weight': 0.20,
                    'value': data.get('debtToEquityRatio', 0),
                    'target': 1.0,
                    'excellent': 0.5,
                    'inverse': True
                },
                'interest_coverage': {
                    'weight': 0.15,
                    'value': data.get('interestCoverage', 0),
                    'target': 2.0,
                    'excellent': 4.0
                },
                'operating_cash_flow_ratio': {
                    'weight': 0.15,
                    'value': data.get('operatingCashFlowRatio', 0),
                    'target': 0.1,
                    'excellent': 0.15
                },
                'profit_margin': {
                    'weight': 0.15,
                    'value': data.get('netProfitMargin', 0),
                    'target': data.get('industryProfitMargin', 0.1)
                },
                'revenue_growth': {
                    'weight': 0.15,
                    'value': data.get('revenueGrowth', 0),
                    'target': data.get('industryRevenueGrowth', 0.05)
                }
            }
            
            score = 0
            for factor, metrics in factors.items():
                normalized_value = self._normalize_metric(
                    metrics['value'],
                    metrics.get('target'),
                    metrics.get('excellent'),
                    metrics.get('inverse', False)
                )
                score += normalized_value * metrics['weight']
            
            return score * 100

        except Exception as e:
            logger.error(f"Error calculating financial health: {str(e)}")
            raise HTTPException(status_code=500, detail="Error calculating financial health")

    def calculate_market_position(self, data: Dict[str, Any]) -> float:
        try:
            factors = {
                'market_share': {
                    'weight': 0.30,
                    'value': data.get('marketShare', 0),
                    'target': data.get('industryAvgMarketShare', 0.1)
                },
                'brand_value': {
                    'weight': 0.25,
                    'value': self._calculate_brand_value(data),
                    'target': 0.7
                },
                'customer_retention': {
                    'weight': 0.25,
                    'value': data.get('customerRetention', 0),
                    'target': 0.85,
                    'excellent': 0.95
                },
                'geographic_diversity': {
                    'weight': 0.20,
                    'value': 1 - (data.get('largestMarketRevenue', 0) / data.get('totalRevenue', 1)),
                    'target': 0.5,
                    'excellent': 0.7
                }
            }

            score = 0
            for factor, metrics in factors.items():
                normalized_value = self._normalize_metric(
                    metrics['value'],
                    metrics['target'],
                    metrics.get('excellent')
                )
                score += normalized_value * metrics['weight']

            return score * 100

        except Exception as e:
            logger.error(f"Error calculating market position: {str(e)}")
            raise HTTPException(status_code=500, detail="Error calculating market position")

    def calculate_operational_efficiency(self, data: Dict[str, Any]) -> float:
        try:
            factors = {
                'asset_turnover': {
                    'weight': 0.25,
                    'value': data.get('assetTurnover', 0),
                    'target': data.get('industryAssetTurnover', 1.0)
                },
                'inventory_turnover': {
                    'weight': 0.25,
                    'value': data.get('inventoryTurnover', 0),
                    'target': data.get('industryInventoryTurnover', 4.0)
                },
                'employee_productivity': {
                    'weight': 0.25,
                    'value': data.get('revenuePerEmployee', 0),
                    'target': data.get('industryRevenuePerEmployee', 250000)
                },
                'operating_margin': {
                    'weight': 0.25,
                    'value': data.get('operatingMargin', 0),
                    'target': data.get('industryOperatingMargin', 0.15)
                }
            }

            score = 0
            for factor, metrics in factors.items():
                normalized_value = self._normalize_metric(
                    metrics['value'],
                    metrics['target']
                )
                score += normalized_value * metrics['weight']

            return score * 100

        except Exception as e:
            logger.error(f"Error calculating operational efficiency: {str(e)}")
            raise HTTPException(status_code=500, detail="Error calculating operational efficiency")

    def calculate_corporate_structure(self, data: Dict[str, Any]) -> float:
        try:
            factors = {
                'subsidiary_health': {
                    'weight': 0.30,
                    'value': data.get('subsidiaryHealthRatio', 0),
                    'target': 0.8,
                    'excellent': 1.0
                },
                'organizational_complexity': {
                    'weight': 0.25,
                    'value': data.get('organizationalComplexity', 0),
                    'target': data.get('industryAvgComplexity', 1.0),
                    'inverse': True
                },
                'parent_company_support': {
                    'weight': 0.25,
                    'value': data.get('parentSupportRatio', 0),
                    'target': 0.1,
                    'excellent': 0.2
                },
                'group_synergy': {
                    'weight': 0.20,
                    'value': data.get('intercompanyRevenue', 0) / data.get('totalRevenue', 1),
                    'target': data.get('industryOptimalSynergy', 0.15)
                }
            }

            score = 0
            for factor, metrics in factors.items():
                normalized_value = self._normalize_metric(
                    metrics['value'],
                    metrics['target'],
                    metrics.get('excellent'),
                    metrics.get('inverse', False)
                )
                score += normalized_value * metrics['weight']

            return score * 100

        except Exception as e:
            logger.error(f"Error calculating corporate structure: {str(e)}")
            raise HTTPException(status_code=500, detail="Error calculating corporate structure")

    def calculate_innovation_adaptability(self, data: Dict[str, Any]) -> float:
        try:
            factors = {
                'r_and_d_intensity': {
                    'weight': 0.30,
                    'value': data.get('rdIntensity', 0),
                    'target': data.get('industryRDIntensity', 0.05)
                },
                'digital_transformation': {
                    'weight': 0.25,
                    'value': self._calculate_digital_transformation(data),
                    'target': data.get('industryDigitalScore', 0.5)
                },
                'patent_portfolio': {
                    'weight': 0.25,
                    'value': self._calculate_patent_score(data),
                    'target': data.get('industryPatentScore', 1.0)
                },
                'new_product_revenue': {
                    'weight': 0.20,
                    'value': data.get('newProductRevenue', 0) / data.get('totalRevenue', 1),
                    'target': 0.15,
                    'excellent': 0.25
                }
            }

            score = 0
            for factor, metrics in factors.items():
                normalized_value = self._normalize_metric(
                    metrics['value'],
                    metrics['target'],
                    metrics.get('excellent')
                )
                score += normalized_value * metrics['weight']

            return score * 100

        except Exception as e:
            logger.error(f"Error calculating innovation adaptability: {str(e)}")
            raise HTTPException(status_code=500, detail="Error calculating innovation adaptability")

    def calculate_governance_risk(self, data: Dict[str, Any]) -> float:
        try:
            factors = {
                'board_independence': {
                    'weight': 0.25,
                    'value': data.get('boardIndependence', 0),
                    'target': 0.5,
                    'excellent': 0.75
                },
                'regulatory_compliance': {
                    'weight': 0.25,
                    'value': 1 - (data.get('regulatoryFines', 0) / data.get('totalRevenue', 1)),
                    'target': 0.95,
                    'excellent': 0.99
                },
                'risk_management': {
                    'weight': 0.25,
                    'value': data.get('riskWeightedCapitalRatio', 0),
                    'target': data.get('industryRiskRatio', 0.12)
                },
                'succession_planning': {
                    'weight': 0.25,
                    'value': self._calculate_succession_score(data),
                    'target': 0.7,
                    'excellent': 0.9
                }
            }

            score = 0
            for factor, metrics in factors.items():
                normalized_value = self._normalize_metric(
                    metrics['value'],
                    metrics['target'],
                    metrics.get('excellent')
                )
                score += normalized_value * metrics['weight']

            return score * 100

        except Exception as e:
            logger.error(f"Error calculating governance risk: {str(e)}")
            raise HTTPException(status_code=500, detail="Error calculating governance risk")

    def _normalize_metric(self, value: float, target: float, excellent: float = None, inverse: bool = False) -> float:
        try:
            if excellent is None:
                excellent = target * 1.5

            if inverse:
                if value <= excellent:
                    return 1.0
                elif value >= target * 2:
                    return 0.0
                else:
                    return (target * 2 - value) / (target * 2 - excellent)
            else:
                if value >= excellent:
                    return 1.0
                elif value <= 0:
                    return 0.0
                else:
                    return min(1.0, value / target)

        except Exception as e:
            logger.error(f"Error normalizing metric: {str(e)}")
            return 0.0

    def _calculate_brand_value(self, data: Dict[str, Any]) -> float:
        try:
            brand_recognition = data.get('brandRecognitionScore', 0)
            price_premium = data.get('pricePremium', 0)
            customer_loyalty = data.get('customerLoyaltyScore', 0)
            
            return (brand_recognition * 0.4 + 
                   price_premium * 0.3 + 
                   customer_loyalty * 0.3)
        except Exception:
            return 0.0

    def _calculate_digital_transformation(self, data: Dict[str, Any]) -> float:
        try:
            digital_revenue_ratio = data.get('digitalRevenue', 0) / data.get('totalRevenue', 1)
            digital_capex_ratio = data.get('digitalCapex', 0) / data.get('totalCapex', 1)
            
            return (digital_revenue_ratio + digital_capex_ratio) / 2
        except Exception:
            return 0.0

    def _calculate_patent_score(self, data: Dict[str, Any]) -> float:
        try:
            active_patents = data.get('activePatents', 0)
            citation_impact = data.get('citationImpact', 1)
            revenue = data.get('totalRevenue', 1)
            
            return (active_patents * citation_impact) / revenue
        except Exception:
            return 0.0

    def _calculate_succession_score(self, data: Dict[str, Any]) -> float:
        try:
            position_coverage = data.get('keyPositionCoverage', 0)
            leadership_development = data.get('leadershipDevelopment', 0)
            succession_documentation = data.get('successionDocumentation', 0)
            
            return (position_coverage * 0.4 + 
                   leadership_development * 0.3 + 
                   succession_documentation * 0.3)
        except Exception:
            return 0.0

@app.post("/calculate-longevity")
async def calculate_longevity(company_data: CompanyData):
    try:
        # Get your API key from environment variable
        api_key = "Aq8GhWWZzHihOcGBMyiy7yiFkvvx7ZEl"
        if not api_key:
            raise HTTPException(status_code=500, detail="API key not configured")

        # Fetch financial data from external API
        base_url = "https://financialmodelingprep.com/api/v3"
        endpoints = {
            'profile': f"/profile/{company_data.symbol}",
            'metrics': f"/key-metrics-ttm/{company_data.symbol}",
            'ratios': f"/ratios-ttm/{company_data.symbol}",
            'growth': f"/financial-growth/{company_data.symbol}",
            'industry': f"/stock-peers/{company_data.symbol}"  # For industry comparisons
        }

        company_info = {}
        for endpoint_name, endpoint in endpoints.items():
            try:
                response = requests.get(
                    f"{base_url}{endpoint}",
                    params={'apikey': api_key},
                    timeout=10  # Add timeout
                )
                
                # Check for rate limiting
                if response.status_code == 429:
                    raise HTTPException(status_code=429, detail="API rate limit exceeded. Please try again later.")
                
                response.raise_for_status()
                data = response.json()
                
                if isinstance(data, list) and data:
                    company_info.update(data[0])
                elif isinstance(data, dict):
                    company_info.update(data)
                    
            except requests.exceptions.Timeout:
                raise HTTPException(status_code=504, detail=f"Timeout while fetching {endpoint_name} data")
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching {endpoint_name} data: {str(e)}")
                if endpoint_name == 'profile':  # Profile data is essential
                    raise HTTPException(status_code=500, detail=f"Error fetching company data: {str(e)}")

        # Calculate industry averages if available
        if 'peers' in company_info:
            try:
                industry_data = await fetch_industry_averages(company_info['peers'], api_key)
                company_info.update(industry_data)
            except Exception as e:
                logger.warning(f"Could not fetch industry averages: {str(e)}")

        # Initialize LongevityIndex calculator
        calculator = LongevityIndex()

        # Calculate individual components
        financial_health = calculator.calculate_financial_health(company_info)
        market_position = calculator.calculate_market_position(company_info)
        operational_efficiency = calculator.calculate_operational_efficiency(company_info)
        corporate_structure = calculator.calculate_corporate_structure(company_info)
        innovation_adaptability = calculator.calculate_innovation_adaptability(company_info)
        governance_risk = calculator.calculate_governance_risk(company_info)

        # Calculate final score
        final_score = (
            financial_health * calculator.weights['financial_health'] +
            market_position * calculator.weights['market_position'] +
            operational_efficiency * calculator.weights['operational_efficiency'] +
            corporate_structure * calculator.weights['corporate_structure'] +
            innovation_adaptability * calculator.weights['innovation_adaptability'] +
            governance_risk * calculator.weights['governance_risk']
        )

        return {
            "score": round(final_score, 2),  # Return just the numerical score
            "components": {
                "financial_health": round(financial_health, 2),
                "market_position": round(market_position, 2),
                "operational_efficiency": round(operational_efficiency, 2),
                "corporate_structure": round(corporate_structure, 2),
                "innovation_adaptability": round(innovation_adaptability, 2),
                "governance_risk": round(governance_risk, 2)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

async def fetch_industry_averages(peers: list, api_key: str) -> Dict[str, float]:
    """Fetch and calculate industry averages from peer companies"""
    industry_data = {
        'industryProfitMargin': [],
        'industryRevenueGrowth': [],
        'industryAssetTurnover': [],
        'industryOperatingMargin': [],
        'industryRDIntensity': []
    }
    
    for peer in peers[:5]:  # Limit to 5 peers to avoid rate limiting
        try:
            response = await fetch_peer_data(peer, api_key)
            for metric in industry_data.keys():
                if metric.replace('industry', '').lower() in response:
                    industry_data[metric].append(response[metric.replace('industry', '').lower()])
        except Exception:
            continue

    # Calculate averages
    return {
        metric: sum(values) / len(values) if values else None 
        for metric, values in industry_data.items()
    }