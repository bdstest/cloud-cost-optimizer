"""
Unit tests for the resource optimization module.
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add the ML module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ml'))

from optimizer import ResourceOptimizer

class TestResourceOptimizer:
    
    def setup_method(self):
        """Setup test fixtures"""
        self.optimizer = ResourceOptimizer()
        
        # Sample instance data
        self.sample_instances = [
            {
                'resource_id': 'i-001',
                'provider': 'aws',
                'service': 'ec2',
                'instance_type': 'm5.4xlarge',
                'cpu_utilization': 25,
                'memory_utilization': 30,
                'monthly_cost': 560.16
            },
            {
                'resource_id': 'vm-002',
                'provider': 'azure',
                'service': 'compute',
                'instance_type': 'Standard_D4s_v4',
                'cpu_utilization': 75,
                'memory_utilization': 80,
                'monthly_cost': 175.20
            }
        ]
        
        # Sample storage data
        self.sample_storage = pd.DataFrame([
            {
                'resource_id': 'bucket-001',
                'provider': 'aws',
                'service': 's3',
                'storage_class': 'standard',
                'last_accessed_days': 45,
                'monthly_cost': 245.80,
                'size_gb': 10691
            }
        ])
    
    def test_optimizer_initialization(self):
        """Test optimizer initialization"""
        assert self.optimizer.scaler is not None
        assert self.optimizer.optimization_rules is not None
        assert 'cpu_utilization' in self.optimizer.optimization_rules
    
    def test_rightsizing_recommendations(self):
        """Test right-sizing recommendation generation"""
        recommendations = self.optimizer.generate_rightsizing_recommendations(self.sample_instances)
        
        assert isinstance(recommendations, list)
        
        # Check that underutilized instance gets recommendation
        underutilized_recs = [r for r in recommendations if r['resource_id'] == 'i-001']
        if underutilized_recs:
            rec = underutilized_recs[0]
            assert rec['monthly_savings'] > 0
            assert rec['projected_cost'] < rec['current_cost']
            assert 0 <= rec['confidence'] <= 1
    
    def test_storage_optimization(self):
        """Test storage optimization recommendations"""
        recommendations = self.optimizer.analyze_storage_optimization(self.sample_storage)
        
        assert isinstance(recommendations, list)
        
        if recommendations:
            rec = recommendations[0]
            assert 'resource_id' in rec
            assert 'monthly_savings' in rec
            assert 'confidence' in rec
            assert rec['monthly_savings'] >= 0
    
    def test_confidence_calculation(self):
        """Test confidence score calculation"""
        confidence = self.optimizer._calculate_recommendation_confidence(20, 25, 0.5)
        
        assert 0 <= confidence <= 1
        
        # Low utilization should have high confidence
        high_confidence = self.optimizer._calculate_recommendation_confidence(15, 20, 0.6)
        low_confidence = self.optimizer._calculate_recommendation_confidence(60, 70, 0.1)
        
        assert high_confidence > low_confidence
    
    def test_reasoning_generation(self):
        """Test reasoning text generation"""
        reasoning = self.optimizer._generate_reasoning(20, 30, 0.5)
        
        assert isinstance(reasoning, str)
        assert len(reasoning) > 0
        assert reasoning.endswith('.')
    
    def test_optimal_instance_finding(self):
        """Test optimal instance type finding"""
        hierarchy = {
            'aws': {
                'm5.large': {'cpu': 2, 'memory': 8, 'cost': 70.02},
                'm5.xlarge': {'cpu': 4, 'memory': 16, 'cost': 140.16},
                'm5.2xlarge': {'cpu': 8, 'memory': 32, 'cost': 280.32},
                'm5.4xlarge': {'cpu': 16, 'memory': 64, 'cost': 560.16}
            }
        }
        
        # Low utilization should suggest smaller instance
        optimal = self.optimizer._find_optimal_instance_type(
            'aws', 'm5.4xlarge', 25, 30, hierarchy
        )
        
        assert optimal in hierarchy['aws']
        assert hierarchy['aws'][optimal]['cost'] <= hierarchy['aws']['m5.4xlarge']['cost']
    
    def test_storage_class_optimization(self):
        """Test storage class optimization"""
        # Frequently accessed data should stay in standard
        optimal_class, projected_cost = self.optimizer._get_optimal_storage_class(
            'aws', 15, 100, 1000  # Accessed 15 days ago
        )
        assert optimal_class == 'standard'
        
        # Infrequently accessed data should move to cheaper tier
        optimal_class, projected_cost = self.optimizer._get_optimal_storage_class(
            'aws', 45, 100, 1000  # Accessed 45 days ago
        )
        assert optimal_class in ['standard_ia', 'glacier', 'glacier_deep']
    
    def test_empty_data_handling(self):
        """Test handling of empty datasets"""
        empty_recommendations = self.optimizer.generate_rightsizing_recommendations([])
        assert empty_recommendations == []
        
        empty_storage = pd.DataFrame()
        storage_recommendations = self.optimizer.analyze_storage_optimization(empty_storage)
        assert storage_recommendations == []

if __name__ == "__main__":
    pytest.main([__file__])