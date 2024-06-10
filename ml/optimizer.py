"""
Resource optimization engine using machine learning algorithms.
Provides right-sizing recommendations, reserved instance analysis, and storage optimization.
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from datetime import datetime, timedelta
import json

class ResourceOptimizer:
    """
    ML-powered resource optimization engine for multi-cloud environments.
    Uses clustering and anomaly detection to identify optimization opportunities.
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.kmeans = None
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.optimization_rules = self._load_optimization_rules()
    
    def _load_optimization_rules(self):
        """Load optimization rules and thresholds"""
        return {
            'cpu_utilization': {
                'underutilized': 30,  # Below 30% CPU
                'optimal': (30, 80),  # 30-80% CPU
                'overutilized': 80    # Above 80% CPU
            },
            'memory_utilization': {
                'underutilized': 40,  # Below 40% memory
                'optimal': (40, 85),  # 40-85% memory
                'overutilized': 85    # Above 85% memory
            },
            'storage_access': {
                'frequent': 30,       # Accessed within 30 days
                'infrequent': 90,     # 30-90 days
                'archive': 365        # Over 90 days
            },
            'cost_thresholds': {
                'small_instance': 100,    # < $100/month
                'medium_instance': 500,   # $100-500/month
                'large_instance': 1000    # > $500/month
            }
        }
    
    def analyze_resource_utilization(self, resource_data):
        """
        Analyze resource utilization patterns using clustering.
        
        Args:
            resource_data: DataFrame with resource metrics
            
        Returns:
            DataFrame with utilization analysis and recommendations
        """
        try:
            df = resource_data.copy()
            
            # Prepare features for clustering
            features = ['cpu_utilization', 'memory_utilization', 'network_io', 'disk_io']
            available_features = [f for f in features if f in df.columns]
            
            if not available_features:
                raise ValueError("No utilization metrics found in data")
            
            # Scale features
            feature_data = df[available_features].fillna(0)
            scaled_features = self.scaler.fit_transform(feature_data)
            
            # Perform K-means clustering
            n_clusters = min(5, len(df))  # Limit clusters for small datasets
            self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = self.kmeans.fit_predict(scaled_features)
            
            df['utilization_cluster'] = clusters
            
            # Analyze each cluster
            cluster_analysis = self._analyze_clusters(df, available_features)
            
            # Generate recommendations
            recommendations = self._generate_utilization_recommendations(df, cluster_analysis)
            
            return {
                'resource_analysis': df.to_dict('records'),
                'cluster_analysis': cluster_analysis,
                'recommendations': recommendations
            }
            
        except Exception as e:
            print(f"❌ Error analyzing utilization: {str(e)}")
            return self._fallback_utilization_analysis(resource_data)
    
    def _analyze_clusters(self, df, features):
        """Analyze utilization clusters to identify patterns"""
        cluster_analysis = {}
        
        for cluster_id in df['utilization_cluster'].unique():
            cluster_data = df[df['utilization_cluster'] == cluster_id]
            
            # Calculate cluster statistics
            cluster_stats = {
                'size': len(cluster_data),
                'avg_cpu': cluster_data['cpu_utilization'].mean() if 'cpu_utilization' in features else 0,
                'avg_memory': cluster_data['memory_utilization'].mean() if 'memory_utilization' in features else 0,
                'avg_cost': cluster_data['monthly_cost'].mean() if 'monthly_cost' in cluster_data.columns else 0
            }
            
            # Classify cluster
            if cluster_stats['avg_cpu'] < self.optimization_rules['cpu_utilization']['underutilized']:
                cluster_type = 'underutilized'
            elif cluster_stats['avg_cpu'] > self.optimization_rules['cpu_utilization']['overutilized']:
                cluster_type = 'overutilized'
            else:
                cluster_type = 'optimal'
            
            cluster_analysis[cluster_id] = {
                'type': cluster_type,
                'stats': cluster_stats,
                'optimization_potential': self._calculate_optimization_potential(cluster_stats, cluster_type)
            }
        
        return cluster_analysis
    
    def _calculate_optimization_potential(self, stats, cluster_type):
        """Calculate optimization potential for a cluster"""
        if cluster_type == 'underutilized':
            # Right-sizing potential based on utilization
            cpu_utilization = stats['avg_cpu']
            if cpu_utilization < 20:
                return {'type': 'rightsizing', 'potential_savings': 0.70}  # 70% savings
            elif cpu_utilization < 30:
                return {'type': 'rightsizing', 'potential_savings': 0.50}  # 50% savings
            else:
                return {'type': 'rightsizing', 'potential_savings': 0.25}  # 25% savings
        
        elif cluster_type == 'overutilized':
            return {'type': 'scaling_up', 'performance_improvement': 0.30}
        
        else:
            return {'type': 'reserved_instance', 'potential_savings': 0.30}
    
    def generate_rightsizing_recommendations(self, instances):
        """
        Generate right-sizing recommendations for compute instances.
        
        Args:
            instances: List of instance data with utilization metrics
            
        Returns:
            List of right-sizing recommendations
        """
        recommendations = []
        
        # Instance type mappings (simplified for demo)
        instance_hierarchy = {
            'aws': {
                't3.nano': {'cpu': 2, 'memory': 0.5, 'cost': 3.50},
                't3.micro': {'cpu': 2, 'memory': 1, 'cost': 7.00},
                't3.small': {'cpu': 2, 'memory': 2, 'cost': 14.00},
                't3.medium': {'cpu': 2, 'memory': 4, 'cost': 28.00},
                't3.large': {'cpu': 2, 'memory': 8, 'cost': 56.00},
                'm5.large': {'cpu': 2, 'memory': 8, 'cost': 70.02},
                'm5.xlarge': {'cpu': 4, 'memory': 16, 'cost': 140.16},
                'm5.2xlarge': {'cpu': 8, 'memory': 32, 'cost': 280.32},
                'm5.4xlarge': {'cpu': 16, 'memory': 64, 'cost': 560.16}
            },
            'azure': {
                'Standard_B1s': {'cpu': 1, 'memory': 1, 'cost': 7.52},
                'Standard_B2s': {'cpu': 2, 'memory': 4, 'cost': 30.08},
                'Standard_D2s_v4': {'cpu': 2, 'memory': 8, 'cost': 70.08},
                'Standard_D4s_v4': {'cpu': 4, 'memory': 16, 'cost': 140.16},
                'Standard_D8s_v4': {'cpu': 8, 'memory': 32, 'cost': 280.32}
            }
        }
        
        for instance in instances:
            try:
                provider = instance.get('provider', 'aws')
                current_type = instance.get('instance_type', 'm5.large')
                cpu_util = instance.get('cpu_utilization', 50)
                memory_util = instance.get('memory_utilization', 50)
                current_cost = instance.get('monthly_cost', 100)
                
                if provider not in instance_hierarchy:
                    continue
                
                # Find optimal instance type
                optimal_type = self._find_optimal_instance_type(
                    provider, current_type, cpu_util, memory_util, instance_hierarchy
                )
                
                if optimal_type != current_type:
                    optimal_cost = instance_hierarchy[provider][optimal_type]['cost']
                    savings = current_cost - optimal_cost
                    
                    if savings > 10:  # Only recommend if savings > $10/month
                        confidence = self._calculate_recommendation_confidence(
                            cpu_util, memory_util, savings/current_cost
                        )
                        
                        recommendations.append({
                            'resource_id': instance.get('resource_id', 'unknown'),
                            'provider': provider,
                            'service': instance.get('service', 'compute'),
                            'current_instance': current_type,
                            'recommended_instance': optimal_type,
                            'current_cost': round(current_cost, 2),
                            'projected_cost': round(optimal_cost, 2),
                            'monthly_savings': round(savings, 2),
                            'savings_percentage': round((savings/current_cost) * 100, 1),
                            'cpu_utilization': cpu_util,
                            'memory_utilization': memory_util,
                            'confidence': confidence,
                            'reasoning': self._generate_reasoning(cpu_util, memory_util, savings/current_cost)
                        })
                        
            except Exception as e:
                print(f"Warning: Error processing instance {instance.get('resource_id', 'unknown')}: {str(e)}")
                continue
        
        # Sort by potential savings
        recommendations.sort(key=lambda x: x['monthly_savings'], reverse=True)
        
        return recommendations
    
    def _find_optimal_instance_type(self, provider, current_type, cpu_util, memory_util, hierarchy):
        """Find optimal instance type based on utilization"""
        available_types = hierarchy.get(provider, {})
        
        if current_type not in available_types:
            return current_type
        
        current_spec = available_types[current_type]
        
        # Calculate required resources with buffer
        required_cpu = max(1, int(current_spec['cpu'] * cpu_util / 100 * 1.2))  # 20% buffer
        required_memory = max(0.5, current_spec['memory'] * memory_util / 100 * 1.2)
        
        # Find smallest instance that meets requirements
        best_type = current_type
        best_cost = current_spec['cost']
        
        for instance_type, spec in available_types.items():
            if (spec['cpu'] >= required_cpu and 
                spec['memory'] >= required_memory and 
                spec['cost'] < best_cost):
                best_type = instance_type
                best_cost = spec['cost']
        
        return best_type
    
    def _calculate_recommendation_confidence(self, cpu_util, memory_util, savings_ratio):
        """Calculate confidence score for recommendation"""
        confidence = 0.5  # Base confidence
        
        # Higher confidence for clearly underutilized resources
        if cpu_util < 20:
            confidence += 0.3
        elif cpu_util < 40:
            confidence += 0.2
        
        if memory_util < 30:
            confidence += 0.2
        elif memory_util < 50:
            confidence += 0.1
        
        # Higher confidence for larger savings
        if savings_ratio > 0.5:
            confidence += 0.2
        elif savings_ratio > 0.3:
            confidence += 0.1
        
        return min(0.95, confidence)  # Cap at 95%
    
    def _generate_reasoning(self, cpu_util, memory_util, savings_ratio):
        """Generate human-readable reasoning for recommendation"""
        reasons = []
        
        if cpu_util < 25:
            reasons.append(f"CPU utilization is low at {cpu_util:.1f}%")
        
        if memory_util < 40:
            reasons.append(f"Memory utilization is low at {memory_util:.1f}%")
        
        if savings_ratio > 0.4:
            reasons.append(f"Significant cost savings potential ({savings_ratio*100:.1f}%)")
        
        return ". ".join(reasons) + "."
    
    def analyze_storage_optimization(self, storage_data):
        """
        Analyze storage usage patterns for optimization opportunities.
        
        Args:
            storage_data: DataFrame with storage metrics
            
        Returns:
            List of storage optimization recommendations
        """
        recommendations = []
        
        for _, storage in storage_data.iterrows():
            try:
                provider = storage.get('provider', 'aws')
                service = storage.get('service', 'storage')
                last_accessed = storage.get('last_accessed_days', 0)
                current_storage_class = storage.get('storage_class', 'standard')
                monthly_cost = storage.get('monthly_cost', 0)
                size_gb = storage.get('size_gb', 0)
                
                # Determine optimal storage class
                optimal_class, projected_cost = self._get_optimal_storage_class(
                    provider, last_accessed, monthly_cost, size_gb
                )
                
                if optimal_class != current_storage_class:
                    savings = monthly_cost - projected_cost
                    
                    if savings > 5:  # Only recommend if savings > $5/month
                        recommendations.append({
                            'resource_id': storage.get('resource_id', 'unknown'),
                            'provider': provider,
                            'service': service,
                            'current_storage_class': current_storage_class,
                            'recommended_storage_class': optimal_class,
                            'current_cost': round(monthly_cost, 2),
                            'projected_cost': round(projected_cost, 2),
                            'monthly_savings': round(savings, 2),
                            'last_accessed_days': last_accessed,
                            'size_gb': size_gb,
                            'confidence': 0.85,
                            'reasoning': self._generate_storage_reasoning(last_accessed, optimal_class)
                        })
                        
            except Exception as e:
                print(f"Warning: Error processing storage {storage.get('resource_id', 'unknown')}: {str(e)}")
                continue
        
        return recommendations
    
    def _get_optimal_storage_class(self, provider, last_accessed_days, current_cost, size_gb):
        """Determine optimal storage class based on access patterns"""
        
        # Storage class pricing (simplified)
        pricing = {
            'aws': {
                'standard': 0.023,      # per GB/month
                'standard_ia': 0.0125,  # per GB/month
                'glacier': 0.004,       # per GB/month
                'glacier_deep': 0.00099 # per GB/month
            },
            'azure': {
                'hot': 0.0184,          # per GB/month
                'cool': 0.01,           # per GB/month
                'archive': 0.00099      # per GB/month
            }
        }
        
        if provider == 'aws':
            if last_accessed_days <= 30:
                optimal_class = 'standard'
            elif last_accessed_days <= 90:
                optimal_class = 'standard_ia'
            elif last_accessed_days <= 365:
                optimal_class = 'glacier'
            else:
                optimal_class = 'glacier_deep'
            
            projected_cost = size_gb * pricing['aws'][optimal_class]
            
        elif provider == 'azure':
            if last_accessed_days <= 30:
                optimal_class = 'hot'
            elif last_accessed_days <= 90:
                optimal_class = 'cool'
            else:
                optimal_class = 'archive'
            
            projected_cost = size_gb * pricing['azure'][optimal_class]
        
        else:
            optimal_class = 'standard'
            projected_cost = current_cost
        
        return optimal_class, projected_cost
    
    def _generate_storage_reasoning(self, last_accessed_days, optimal_class):
        """Generate reasoning for storage optimization"""
        if last_accessed_days > 365:
            return f"Data not accessed for {last_accessed_days} days. Archive storage recommended."
        elif last_accessed_days > 90:
            return f"Infrequent access pattern ({last_accessed_days} days). Cold storage suitable."
        elif last_accessed_days > 30:
            return f"Access pattern suggests infrequent tier ({last_accessed_days} days)."
        else:
            return "Current storage class appears optimal for access pattern."
    
    def _fallback_utilization_analysis(self, resource_data):
        """Fallback analysis when ML clustering fails"""
        try:
            df = resource_data.copy()
            
            # Simple rule-based analysis
            recommendations = []
            
            for _, resource in df.iterrows():
                cpu_util = resource.get('cpu_utilization', 50)
                memory_util = resource.get('memory_utilization', 50)
                
                if cpu_util < 30 and memory_util < 40:
                    recommendations.append({
                        'resource_id': resource.get('resource_id', 'unknown'),
                        'type': 'rightsizing',
                        'reason': 'Low CPU and memory utilization',
                        'potential_savings': 0.4
                    })
            
            return {
                'resource_analysis': df.to_dict('records'),
                'cluster_analysis': {},
                'recommendations': recommendations
            }
            
        except Exception as e:
            print(f"❌ Fallback analysis failed: {str(e)}")
            return {
                'resource_analysis': [],
                'cluster_analysis': {},
                'recommendations': []
            }
    
    def _generate_utilization_recommendations(self, df, cluster_analysis):
        """Generate recommendations based on cluster analysis"""
        recommendations = []
        
        for cluster_id, analysis in cluster_analysis.items():
            cluster_data = df[df['utilization_cluster'] == cluster_id]
            
            for _, resource in cluster_data.iterrows():
                if analysis['type'] == 'underutilized':
                    recommendations.append({
                        'resource_id': resource.get('resource_id', f'resource-{cluster_id}'),
                        'type': 'rightsizing',
                        'current_utilization': analysis['stats']['avg_cpu'],
                        'potential_savings': analysis['optimization_potential']['potential_savings'],
                        'confidence': 0.8,
                        'cluster': cluster_id
                    })
        
        return recommendations

def generate_sample_optimization_data():
    """Generate sample optimization data for demo"""
    
    # Sample instance data
    instances = [
        {
            'resource_id': 'i-0123456789abcdef0',
            'provider': 'aws',
            'service': 'ec2',
            'instance_type': 'm5.4xlarge',
            'cpu_utilization': 25,
            'memory_utilization': 30,
            'monthly_cost': 560.16
        },
        {
            'resource_id': 'vm-standard-d4s-v4',
            'provider': 'azure',
            'service': 'compute',
            'instance_type': 'Standard_D4s_v4',
            'cpu_utilization': 45,
            'memory_utilization': 55,
            'monthly_cost': 175.20
        }
    ]
    
    # Sample storage data
    storage = [
        {
            'resource_id': 'bucket-analytics-logs',
            'provider': 'aws',
            'service': 's3',
            'storage_class': 'standard',
            'last_accessed_days': 45,
            'monthly_cost': 245.80,
            'size_gb': 10691  # ~$0.023/GB for standard
        }
    ]
    
    optimizer = ResourceOptimizer()
    
    # Generate rightsizing recommendations
    rightsizing_recs = optimizer.generate_rightsizing_recommendations(instances)
    
    # Generate storage recommendations
    storage_df = pd.DataFrame(storage)
    storage_recs = optimizer.analyze_storage_optimization(storage_df)
    
    return {
        'rightsizing_recommendations': rightsizing_recs,
        'storage_recommendations': storage_recs,
        'total_potential_savings': sum(rec['monthly_savings'] for rec in rightsizing_recs + storage_recs)
    }

if __name__ == "__main__":
    # Demo the optimizer
    print("🔧 Resource Optimization Engine Demo")
    print("=" * 50)
    
    results = generate_sample_optimization_data()
    
    print(f"💰 Total Potential Monthly Savings: ${results['total_potential_savings']:,.2f}")
    print(f"📊 Right-sizing Recommendations: {len(results['rightsizing_recommendations'])}")
    print(f"💾 Storage Recommendations: {len(results['storage_recommendations'])}")
    
    print("\n🎯 Top Recommendations:")
    all_recs = results['rightsizing_recommendations'] + results['storage_recommendations']
    for rec in sorted(all_recs, key=lambda x: x['monthly_savings'], reverse=True)[:3]:
        print(f"  • {rec['resource_id']}: ${rec['monthly_savings']:,.0f}/month savings")
    
    print("\n✅ Optimization engine ready for deployment!")