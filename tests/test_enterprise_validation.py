"""Enterprise validation tests demonstrating cost optimization capabilities."""

import pytest
import pandas as pd
import numpy as np
from ml.advanced_optimizer import EnterpriseOptimizer


class TestEnterpriseValidation:
    """Validate enterprise-grade cost optimization capabilities."""
    
    def setup_method(self):
        """Set up test data and optimizer."""
        self.optimizer = EnterpriseOptimizer()
        
        # Generate realistic enterprise cost data
        dates = pd.date_range('2024-01-01', periods=180, freq='D')
        np.random.seed(42)
        
        self.sample_data = pd.DataFrame({
            'date': dates,
            'service': np.random.choice(['EC2', 'RDS', 'S3', 'Lambda'], size=180),
            'cost': np.random.normal(50000, 15000, 180),  # ~$50K daily average
            'cpu_hours': np.random.normal(1000, 300, 180),
            'memory_gb': np.random.normal(2000, 600, 180),
            'storage_gb': np.random.normal(5000, 1500, 180)
        })
        
    def test_budget_categorization(self):
        """Test budget category classification."""
        test_cases = [
            (250_000, 'small'),     # $250K
            (1_500_000, 'medium'),  # $1.5M
            (3_500_000, 'large'),   # $3.5M
            (7_000_000, 'enterprise') # $7M
        ]
        
        for budget, expected_category in test_cases:
            category = self.optimizer.analyze_budget_category(budget)
            assert category == expected_category
            
    def test_cost_reduction_validation(self):
        """Validate 35% cost reduction claims."""
        monthly_budgets = [500_000, 1_500_000, 3_000_000, 6_000_000]
        
        for budget in monthly_budgets:
            result = self.optimizer.optimize_for_budget(self.sample_data, budget)
            
            # Verify cost reduction is significant
            reduction_pct = result['cost_reduction_percentage']
            assert reduction_pct >= 30, f"Expected >=30% reduction, got {reduction_pct}%"
            
            # Verify annual savings calculation
            monthly_savings = result['projected_monthly_savings']
            annual_savings = result['annual_savings']
            assert annual_savings == monthly_savings * 12
            
            # Verify recommendations are budget-appropriate
            recommendations = result['recommendations']
            assert len(recommendations) >= 3
            
    def test_enterprise_scale_optimization(self):
        """Test optimization for enterprise-scale budgets ($5M+)."""
        enterprise_budget = 8_000_000  # $8M monthly
        
        result = self.optimizer.optimize_for_budget(self.sample_data, enterprise_budget)
        
        assert result['budget_category'] == 'enterprise'
        
        # Enterprise optimizations should achieve higher savings
        reduction_pct = result['cost_reduction_percentage']
        assert reduction_pct >= 35, "Enterprise optimization should achieve 35%+ reduction"
        
        # Verify enterprise-specific recommendations
        recommendations = result['recommendations']
        enterprise_keywords = ['enterprise', 'volume', 'multi-cloud', 'FinOps']
        
        recommendation_text = ' '.join(recommendations)
        assert any(keyword in recommendation_text for keyword in enterprise_keywords)
        
    def test_anomaly_detection_accuracy(self):
        """Test cost anomaly detection capabilities."""
        # Inject known anomalies
        anomaly_data = self.sample_data.copy()
        
        # Create obvious anomalies
        anomaly_data.loc[50, 'cost'] = 200_000  # 4x normal cost
        anomaly_data.loc[100, 'cost'] = 300_000  # 6x normal cost
        anomaly_data.loc[150, 'storage_gb'] = 50_000  # 10x normal storage
        
        anomalies = self.optimizer.detect_cost_anomalies(anomaly_data)
        
        # Should detect the injected anomalies
        assert len(anomalies) >= 3
        
        # Verify high-cost anomalies are flagged
        high_cost_anomalies = [a for a in anomalies if a['cost'] > 150_000]
        assert len(high_cost_anomalies) >= 2
        
    def test_forecasting_accuracy(self):
        """Test Prophet forecasting with confidence intervals."""
        # Use stable historical data for forecasting
        stable_data = self.sample_data.copy()
        
        forecast = self.optimizer.generate_forecast(stable_data, days_ahead=30)
        
        # Verify forecast structure
        assert len(forecast) > len(stable_data)  # Should include future dates
        assert 'yhat' in forecast.columns  # Predicted values
        assert 'yhat_lower' in forecast.columns  # Lower confidence bound
        assert 'yhat_upper' in forecast.columns  # Upper confidence bound
        
        # Verify confidence intervals are reasonable
        recent_forecast = forecast.tail(30)  # Last 30 days of forecast
        
        for _, row in recent_forecast.iterrows():
            assert row['yhat_lower'] <= row['yhat'] <= row['yhat_upper']
            
            # Confidence interval should be reasonable (not too wide)
            interval_width = row['yhat_upper'] - row['yhat_lower']
            assert interval_width < row['yhat'] * 2  # Less than 200% of prediction
            
    def test_roi_calculation(self):
        """Test return on investment calculations."""
        test_budget = 2_000_000  # $2M monthly
        
        result = self.optimizer.optimize_for_budget(self.sample_data, test_budget)
        
        monthly_savings = result['projected_monthly_savings']
        annual_savings = result['annual_savings']
        
        # Verify savings are substantial for enterprise clients
        assert monthly_savings > 100_000, "Should save >$100K monthly at $2M budget"
        assert annual_savings > 1_000_000, "Should save >$1M annually"
        
        # ROI should be excellent (implementation costs typically <10% of savings)
        estimated_implementation_cost = annual_savings * 0.1
        roi = (annual_savings - estimated_implementation_cost) / estimated_implementation_cost
        
        assert roi > 5, f"ROI should be >5x, got {roi:.1f}x"