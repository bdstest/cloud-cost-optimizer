"""
Unit tests for the cost prediction module.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the ML module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ml'))

from cost_predictor import CostPredictor

class TestCostPredictor:
    
    def setup_method(self):
        """Setup test fixtures"""
        self.predictor = CostPredictor()
        
        # Create sample data
        dates = pd.date_range(start='2024-04-01', end='2024-07-31', freq='D')
        self.sample_data = pd.DataFrame({
            'date': dates,
            'cost': np.random.normal(1000, 100, len(dates))
        })
    
    def test_predictor_initialization(self):
        """Test that predictor initializes correctly"""
        assert self.predictor.model is None
        assert not self.predictor.is_trained
        assert self.predictor.model_accuracy is None
    
    def test_prepare_data(self):
        """Test data preparation for Prophet"""
        prepared_data = self.predictor.prepare_data(self.sample_data)
        
        assert 'ds' in prepared_data.columns
        assert 'y' in prepared_data.columns
        assert len(prepared_data) == len(self.sample_data)
        assert prepared_data['ds'].dtype == 'datetime64[ns]'
    
    def test_train_model(self):
        """Test model training"""
        self.predictor.train_model(self.sample_data)
        
        assert self.predictor.is_trained
        assert self.predictor.model is not None
        assert self.predictor.model_accuracy is not None
        assert 0 <= self.predictor.model_accuracy <= 1
    
    def test_predict_requires_training(self):
        """Test that prediction requires training"""
        with pytest.raises(ValueError, match="Model must be trained"):
            self.predictor.predict(30)
    
    def test_predict_with_trained_model(self):
        """Test prediction with trained model"""
        self.predictor.train_model(self.sample_data)
        predictions = self.predictor.predict(7)
        
        assert len(predictions) == 7
        assert 'date' in predictions.columns
        assert 'predicted_cost' in predictions.columns
        assert 'confidence_lower' in predictions.columns
        assert 'confidence_upper' in predictions.columns
        
        # Check that predictions are positive
        assert all(predictions['predicted_cost'] >= 0)
        assert all(predictions['confidence_lower'] >= 0)
    
    def test_trend_analysis(self):
        """Test trend analysis functionality"""
        self.predictor.train_model(self.sample_data)
        trend_analysis = self.predictor.get_trend_analysis()
        
        assert 'trend_direction' in trend_analysis
        assert 'trend_change_percent' in trend_analysis
        assert 'model_accuracy' in trend_analysis
        assert trend_analysis['trend_direction'] in ['increasing', 'decreasing', 'stable', 'unknown']
    
    def test_insufficient_data_handling(self):
        """Test handling of insufficient training data"""
        small_data = self.sample_data.head(5)
        
        with pytest.raises(ValueError, match="Need at least 14 days"):
            self.predictor.train_model(small_data)
    
    def test_missing_data_handling(self):
        """Test handling of missing values"""
        data_with_nulls = self.sample_data.copy()
        data_with_nulls.loc[10:15, 'cost'] = np.nan
        
        # Should handle nulls gracefully
        prepared = self.predictor.prepare_data(data_with_nulls)
        assert len(prepared) < len(data_with_nulls)  # NaN rows should be dropped

if __name__ == "__main__":
    pytest.main([__file__])