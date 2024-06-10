"""
Anomaly detection for cloud cost monitoring using Isolation Forest.
Identifies unusual spending patterns and potential cost optimization opportunities.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import logging

class CostAnomalyDetector:
    """
    ML-powered anomaly detection for cloud cost monitoring.
    Uses Isolation Forest to identify unusual spending patterns.
    """
    
    def __init__(self, contamination=0.1):
        """
        Initialize the anomaly detector.
        
        Args:
            contamination: Expected proportion of anomalies (0.1 = 10%)
        """
        self.contamination = contamination
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []
        self.baseline_stats = {}
    
    def prepare_features(self, cost_data):
        """
        Prepare features for anomaly detection.
        
        Args:
            cost_data: DataFrame with cost and metadata
            
        Returns:
            DataFrame with engineered features
        """
        df = cost_data.copy()
        
        # Ensure timestamp is datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['day_of_month'] = df['timestamp'].dt.day
        df['month'] = df['timestamp'].dt.month
        
        # Create cost-based features
        df['log_cost'] = np.log1p(df['cost'])  # Log transform for skewed data
        
        # Provider and service encoding (simple for demo)
        provider_mapping = {'aws': 0, 'azure': 1, 'onpremises': 2}
        df['provider_encoded'] = df['provider'].map(provider_mapping).fillna(3)
        
        # Calculate rolling statistics (if enough data)
        if len(df) > 7:
            df = df.sort_values('timestamp')
            df['cost_rolling_mean_7d'] = df['cost'].rolling(window=7, min_periods=1).mean()
            df['cost_rolling_std_7d'] = df['cost'].rolling(window=7, min_periods=1).std()
            df['cost_rolling_median_7d'] = df['cost'].rolling(window=7, min_periods=1).median()
            
            # Z-score from rolling statistics
            df['cost_zscore'] = (df['cost'] - df['cost_rolling_mean_7d']) / (df['cost_rolling_std_7d'] + 1e-8)
        else:
            # Fallback for small datasets
            df['cost_rolling_mean_7d'] = df['cost'].mean()
            df['cost_rolling_std_7d'] = df['cost'].std()
            df['cost_rolling_median_7d'] = df['cost'].median()
            df['cost_zscore'] = (df['cost'] - df['cost'].mean()) / (df['cost'].std() + 1e-8)
        
        # Resource utilization features (if available)
        if 'usage_hours' in df.columns:
            df['usage_hours_normalized'] = df['usage_hours'] / 744  # Normalize to monthly max
        
        if 'resource_count' in df.columns:
            df['cost_per_resource'] = df['cost'] / (df['resource_count'] + 1)
        
        return df
    
    def train(self, cost_data):
        """
        Train the anomaly detection model.
        
        Args:
            cost_data: Historical cost data for training
        """
        try:
            # Prepare features
            df_features = self.prepare_features(cost_data)
            
            # Select numeric features for model
            numeric_features = [
                'log_cost', 'hour', 'day_of_week', 'day_of_month', 'month',
                'provider_encoded', 'cost_zscore', 'usage_hours_normalized'
            ]
            
            # Only use features that exist in the data
            available_features = [f for f in numeric_features if f in df_features.columns]
            
            if len(available_features) < 3:
                raise ValueError("Not enough features available for training")
            
            self.feature_names = available_features
            feature_matrix = df_features[available_features].fillna(0)
            
            # Scale features
            scaled_features = self.scaler.fit_transform(feature_matrix)
            
            # Train the model
            self.model.fit(scaled_features)
            
            # Calculate baseline statistics
            self.baseline_stats = {
                'mean_cost': df_features['cost'].mean(),
                'std_cost': df_features['cost'].std(),
                'median_cost': df_features['cost'].median(),
                'p95_cost': df_features['cost'].quantile(0.95),
                'training_samples': len(df_features)
            }
            
            self.is_trained = True
            print(f"✅ Anomaly detector trained on {len(df_features)} samples")
            print(f"📊 Features used: {', '.join(self.feature_names)}")
            print(f"💰 Baseline cost stats: mean=${self.baseline_stats['mean_cost']:.2f}, "
                  f"std=${self.baseline_stats['std_cost']:.2f}")
            
        except Exception as e:
            print(f"❌ Error training anomaly detector: {str(e)}")
            raise
    
    def detect_anomalies(self, cost_data):
        """
        Detect anomalies in cost data.
        
        Args:
            cost_data: New cost data to analyze
            
        Returns:
            DataFrame with anomaly scores and classifications
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before detecting anomalies")
        
        try:
            # Prepare features
            df_features = self.prepare_features(cost_data)
            
            # Use same features as training
            feature_matrix = df_features[self.feature_names].fillna(0)
            
            # Scale features
            scaled_features = self.scaler.transform(feature_matrix)
            
            # Predict anomalies
            anomaly_labels = self.model.predict(scaled_features)
            anomaly_scores = self.model.score_samples(scaled_features)
            
            # Add results to dataframe
            df_results = df_features.copy()
            df_results['anomaly_score'] = anomaly_scores
            df_results['is_anomaly'] = anomaly_labels == -1
            df_results['anomaly_severity'] = self._calculate_severity(anomaly_scores, df_features['cost'])
            df_results['anomaly_reason'] = self._generate_anomaly_reasons(df_results)
            
            return df_results
            
        except Exception as e:
            print(f"❌ Error detecting anomalies: {str(e)}")
            raise
    
    def _calculate_severity(self, anomaly_scores, costs):
        """Calculate severity levels for anomalies"""
        severities = []
        
        for score, cost in zip(anomaly_scores, costs):
            if score < -0.5:  # Very low anomaly score
                severity = 'high'
            elif score < -0.2:
                severity = 'medium'
            elif score < 0:
                severity = 'low'
            else:
                severity = 'normal'
            
            # Adjust based on cost magnitude
            if cost > self.baseline_stats['p95_cost'] * 2:
                if severity == 'medium':
                    severity = 'high'
                elif severity == 'low':
                    severity = 'medium'
            
            severities.append(severity)
        
        return severities
    
    def _generate_anomaly_reasons(self, df_results):
        """Generate human-readable reasons for anomalies"""
        reasons = []
        
        for _, row in df_results.iterrows():
            if not row['is_anomaly']:
                reasons.append('Normal spending pattern')
                continue
            
            reason_parts = []
            
            # Check cost magnitude
            if row['cost'] > self.baseline_stats['p95_cost']:
                reason_parts.append(f"Cost ({row['cost']:.2f}) exceeds 95th percentile")
            
            # Check time patterns
            if row['hour'] < 6 or row['hour'] > 22:
                reason_parts.append("Unusual time of day")
            
            if row['day_of_week'] >= 5:  # Weekend
                reason_parts.append("Weekend activity")
            
            # Check provider patterns
            if 'provider' in row and row['provider'] != 'aws':  # Assuming AWS is most common
                reason_parts.append(f"Unusual provider ({row['provider']})")
            
            # Check z-score
            if abs(row['cost_zscore']) > 2:
                reason_parts.append(f"Cost deviates significantly from trend (z-score: {row['cost_zscore']:.2f})")
            
            if not reason_parts:
                reason_parts.append("Multiple factors indicate anomalous pattern")
            
            reasons.append("; ".join(reason_parts))
        
        return reasons
    
    def get_anomaly_summary(self, df_results):
        """Generate summary of anomaly detection results"""
        if df_results.empty:
            return {
                'total_records': 0,
                'anomalies_detected': 0,
                'anomaly_rate': 0,
                'severity_breakdown': {},
                'total_anomaly_cost': 0,
                'avg_anomaly_cost': 0
            }
        
        anomalies = df_results[df_results['is_anomaly']]
        
        severity_breakdown = anomalies['anomaly_severity'].value_counts().to_dict()
        
        return {
            'total_records': len(df_results),
            'anomalies_detected': len(anomalies),
            'anomaly_rate': round(len(anomalies) / len(df_results) * 100, 2),
            'severity_breakdown': severity_breakdown,
            'total_anomaly_cost': round(anomalies['cost'].sum(), 2),
            'avg_anomaly_cost': round(anomalies['cost'].mean(), 2) if len(anomalies) > 0 else 0,
            'date_range': {
                'start': df_results['timestamp'].min().strftime('%Y-%m-%d'),
                'end': df_results['timestamp'].max().strftime('%Y-%m-%d')
            }
        }
    
    def generate_alerts(self, df_results, alert_thresholds=None):
        """
        Generate alerts for significant anomalies.
        
        Args:
            df_results: Results from anomaly detection
            alert_thresholds: Dict with alert configuration
            
        Returns:
            List of alert objects
        """
        if alert_thresholds is None:
            alert_thresholds = {
                'high_severity_cost': 1000,  # Alert if high severity anomaly > $1000
                'medium_severity_cost': 5000,  # Alert if medium severity anomaly > $5000
                'anomaly_rate': 20  # Alert if anomaly rate > 20%
            }
        
        alerts = []
        
        # High severity cost anomalies
        high_severity = df_results[
            (df_results['is_anomaly']) & 
            (df_results['anomaly_severity'] == 'high') &
            (df_results['cost'] > alert_thresholds['high_severity_cost'])
        ]
        
        for _, anomaly in high_severity.iterrows():
            alerts.append({
                'type': 'high_cost_anomaly',
                'severity': 'critical',
                'resource_id': anomaly.get('resource_id', 'unknown'),
                'provider': anomaly.get('provider', 'unknown'),
                'cost': anomaly['cost'],
                'timestamp': anomaly['timestamp'],
                'message': f"High-cost anomaly detected: ${anomaly['cost']:.2f}",
                'reason': anomaly['anomaly_reason'],
                'recommended_action': 'Investigate immediately and verify legitimacy'
            })
        
        # Medium severity anomalies above threshold
        medium_severity = df_results[
            (df_results['is_anomaly']) & 
            (df_results['anomaly_severity'] == 'medium') &
            (df_results['cost'] > alert_thresholds['medium_severity_cost'])
        ]
        
        for _, anomaly in medium_severity.iterrows():
            alerts.append({
                'type': 'medium_cost_anomaly',
                'severity': 'warning',
                'resource_id': anomaly.get('resource_id', 'unknown'),
                'provider': anomaly.get('provider', 'unknown'),
                'cost': anomaly['cost'],
                'timestamp': anomaly['timestamp'],
                'message': f"Medium-cost anomaly detected: ${anomaly['cost']:.2f}",
                'reason': anomaly['anomaly_reason'],
                'recommended_action': 'Review and validate spending pattern'
            })
        
        # High anomaly rate alert
        summary = self.get_anomaly_summary(df_results)
        if summary['anomaly_rate'] > alert_thresholds['anomaly_rate']:
            alerts.append({
                'type': 'high_anomaly_rate',
                'severity': 'warning',
                'message': f"High anomaly rate detected: {summary['anomaly_rate']:.1f}%",
                'anomaly_count': summary['anomalies_detected'],
                'total_records': summary['total_records'],
                'recommended_action': 'Review spending patterns and optimization opportunities'
            })
        
        return alerts

def generate_sample_anomaly_data():
    """Generate sample data with anomalies for demo"""
    
    # Generate normal cost data
    dates = pd.date_range(start='2024-06-01', end='2024-08-31', freq='D')
    normal_data = []
    
    for date in dates:
        # Normal daily pattern
        base_cost = 1000 + np.random.normal(0, 100)
        
        # Add some normal variations
        if date.weekday() >= 5:  # Weekend
            base_cost *= 0.7
        
        if date.hour >= 18 or date.hour <= 6:  # Off-hours
            base_cost *= 0.8
        
        normal_data.append({
            'timestamp': date,
            'provider': np.random.choice(['aws', 'azure', 'onpremises'], p=[0.6, 0.3, 0.1]),
            'service': np.random.choice(['ec2', 'rds', 's3', 'compute', 'storage']),
            'resource_id': f"resource-{np.random.randint(1, 100):03d}",
            'cost': max(0, base_cost),
            'usage_hours': np.random.randint(1, 24),
            'resource_count': np.random.randint(1, 10)
        })
    
    # Add some anomalies
    anomaly_dates = np.random.choice(dates, size=8, replace=False)
    
    for date in anomaly_dates:
        anomaly_type = np.random.choice(['high_cost', 'unusual_time', 'new_service'])
        
        if anomaly_type == 'high_cost':
            cost = 5000 + np.random.normal(0, 1000)  # Much higher than normal
        elif anomaly_type == 'unusual_time':
            cost = 800 + np.random.normal(0, 200)
            date = date.replace(hour=3)  # 3 AM
        else:  # new_service
            cost = 1200 + np.random.normal(0, 300)
        
        normal_data.append({
            'timestamp': date,
            'provider': 'aws',
            'service': 'lambda' if anomaly_type == 'new_service' else 'ec2',
            'resource_id': f"anomaly-{np.random.randint(1, 100):03d}",
            'cost': max(0, cost),
            'usage_hours': np.random.randint(1, 24),
            'resource_count': np.random.randint(1, 10)
        })
    
    return pd.DataFrame(normal_data)

if __name__ == "__main__":
    # Demo the anomaly detector
    print("🚨 Cost Anomaly Detection Demo")
    print("=" * 50)
    
    # Generate sample data
    sample_data = generate_sample_anomaly_data()
    print(f"📊 Generated {len(sample_data)} cost records")
    
    # Split data for training and testing
    train_size = int(len(sample_data) * 0.8)
    train_data = sample_data.iloc[:train_size]
    test_data = sample_data.iloc[train_size:]
    
    # Train detector
    detector = CostAnomalyDetector(contamination=0.1)
    detector.train(train_data)
    
    # Detect anomalies
    results = detector.detect_anomalies(test_data)
    
    # Generate summary
    summary = detector.get_anomaly_summary(results)
    
    print(f"\n🔍 Anomaly Detection Results:")
    print(f"  • Total records analyzed: {summary['total_records']}")
    print(f"  • Anomalies detected: {summary['anomalies_detected']}")
    print(f"  • Anomaly rate: {summary['anomaly_rate']:.1f}%")
    print(f"  • Total anomaly cost: ${summary['total_anomaly_cost']:,.2f}")
    
    if summary['severity_breakdown']:
        print(f"  • Severity breakdown: {summary['severity_breakdown']}")
    
    # Generate alerts
    alerts = detector.generate_alerts(results)
    
    if alerts:
        print(f"\n🚨 {len(alerts)} Alert(s) Generated:")
        for alert in alerts[:3]:  # Show first 3 alerts
            print(f"  • {alert['type']}: {alert['message']}")
            if 'resource_id' in alert:
                print(f"    Resource: {alert['resource_id']} (${alert['cost']:,.2f})")
    
    print("\n✅ Anomaly detection system ready for deployment!")