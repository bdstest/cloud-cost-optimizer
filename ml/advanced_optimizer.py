"""Advanced cost optimization using machine learning and predictive analytics."""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from prophet import Prophet
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)


class EnterpriseOptimizer:
    """Enterprise-grade cost optimizer with ML-driven recommendations."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.budget_thresholds = {
            'small': (100_000, 500_000),    # $100K - $500K
            'medium': (500_000, 2_000_000), # $500K - $2M  
            'large': (2_000_000, 5_000_000), # $2M - $5M
            'enterprise': (5_000_000, float('inf'))  # $5M+
        }
        
    def analyze_budget_category(self, monthly_budget: float) -> str:
        """Categorize budget size for appropriate optimization strategies."""
        for category, (min_budget, max_budget) in self.budget_thresholds.items():
            if min_budget <= monthly_budget < max_budget:
                return category
        return 'enterprise'
        
    def optimize_for_budget(self, 
                           costs_df: pd.DataFrame, 
                           monthly_budget: float) -> Dict[str, any]:
        """Generate optimization recommendations based on budget category."""
        
        category = self.analyze_budget_category(monthly_budget)
        current_monthly = costs_df['cost'].sum()
        
        # Calculate potential savings
        recommendations = []
        projected_savings = 0
        
        if category in ['small', 'medium']:
            # Focus on right-sizing and reserved instances
            rightsizing_savings = current_monthly * 0.15  # 15% from rightsizing
            reserved_savings = current_monthly * 0.20      # 20% from RIs
            projected_savings = rightsizing_savings + reserved_savings
            
            recommendations.extend([
                "Implement auto-scaling for development environments",
                "Purchase reserved instances for stable workloads",
                "Right-size oversized instances based on utilization"
            ])
            
        elif category == 'large':
            # Advanced optimization strategies
            rightsizing_savings = current_monthly * 0.20  # 20% from advanced rightsizing
            spot_savings = current_monthly * 0.15         # 15% from spot instances
            storage_savings = current_monthly * 0.10      # 10% from storage optimization
            projected_savings = rightsizing_savings + spot_savings + storage_savings
            
            recommendations.extend([
                "Implement spot instance strategies for non-critical workloads",
                "Optimize data lifecycle and storage tiers",
                "Deploy advanced monitoring and automated scaling",
                "Implement cost allocation tags for chargeback"
            ])
            
        else:  # enterprise
            # Comprehensive enterprise optimization
            compute_savings = current_monthly * 0.25      # 25% from compute optimization
            network_savings = current_monthly * 0.08      # 8% from network optimization
            storage_savings = current_monthly * 0.12      # 12% from storage optimization
            projected_savings = compute_savings + network_savings + storage_savings
            
            recommendations.extend([
                "Deploy enterprise discount programs and volume commitments",
                "Implement multi-cloud cost arbitrage strategies",
                "Advanced workload placement optimization",
                "Enterprise-grade FinOps governance framework",
                "Automated cost anomaly detection and remediation"
            ])
            
        # Calculate ROI
        potential_reduction = projected_savings / current_monthly
        annual_savings = projected_savings * 12
        
        return {
            'budget_category': category,
            'current_monthly_cost': current_monthly,
            'projected_monthly_savings': projected_savings,
            'cost_reduction_percentage': potential_reduction * 100,
            'annual_savings': annual_savings,
            'recommendations': recommendations,
            'implementation_timeline': self._get_implementation_timeline(category)
        }
        
    def _get_implementation_timeline(self, category: str) -> Dict[str, str]:
        """Get implementation timeline based on organization size."""
        timelines = {
            'small': {
                'quick_wins': '1-2 weeks',
                'rightsizing': '1 month', 
                'reserved_instances': '2-3 months'
            },
            'medium': {
                'quick_wins': '2-3 weeks',
                'automation': '2 months',
                'governance': '3-4 months'
            },
            'large': {
                'assessment': '1 month',
                'pilot_implementation': '2-3 months',
                'full_rollout': '6-9 months'
            },
            'enterprise': {
                'strategy_development': '2 months',
                'pilot_programs': '3-6 months', 
                'enterprise_rollout': '12-18 months'
            }
        }
        return timelines.get(category, timelines['medium'])
        
    def detect_cost_anomalies(self, costs_df: pd.DataFrame) -> List[Dict]:
        """Detect unusual spending patterns using Isolation Forest."""
        features = ['cost', 'cpu_hours', 'memory_gb', 'storage_gb']
        
        # Prepare features for anomaly detection
        feature_data = costs_df[features].fillna(0)
        normalized_data = self.scaler.fit_transform(feature_data)
        
        # Detect anomalies
        anomalies = self.anomaly_detector.fit_predict(normalized_data)
        
        anomaly_details = []
        for idx, is_anomaly in enumerate(anomalies):
            if is_anomaly == -1:  # Anomaly detected
                row = costs_df.iloc[idx]
                anomaly_details.append({
                    'date': row['date'],
                    'service': row['service'],
                    'cost': row['cost'],
                    'anomaly_score': self.anomaly_detector.score_samples([normalized_data[idx]])[0],
                    'potential_cause': self._analyze_anomaly_cause(row)
                })
                
        return sorted(anomaly_details, key=lambda x: x['anomaly_score'])
        
    def _analyze_anomaly_cause(self, row: pd.Series) -> str:
        """Analyze potential causes of cost anomalies."""
        cost = row['cost']
        
        if cost > 10000:
            return "High-cost spike - check for resource provisioning errors"
        elif row.get('cpu_hours', 0) > row.get('memory_gb', 0) * 10:
            return "CPU-intensive workload - consider compute-optimized instances"
        elif row.get('storage_gb', 0) > 1000:
            return "High storage usage - review data lifecycle policies"
        else:
            return "Unusual resource pattern - manual investigation recommended"
            
    def generate_forecast(self, 
                         costs_df: pd.DataFrame, 
                         days_ahead: int = 90) -> pd.DataFrame:
        """Generate cost forecasts using Prophet with confidence intervals."""
        
        # Prepare data for Prophet
        prophet_df = costs_df.groupby('date')['cost'].sum().reset_index()
        prophet_df.columns = ['ds', 'y']
        
        # Create and fit Prophet model
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            interval_width=0.95
        )
        
        model.fit(prophet_df)
        
        # Generate forecast
        future = model.make_future_dataframe(periods=days_ahead)
        forecast = model.predict(future)
        
        # Add business context
        forecast['budget_status'] = forecast['yhat'].apply(
            lambda x: 'over_budget' if x > monthly_budget else 'within_budget'
        )
        
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper', 'budget_status']]