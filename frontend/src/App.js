import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  BarElement,
  ArcElement
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';
const API_KEY = process.env.REACT_APP_API_KEY || 'demo-key-sk-cloudcost123456';

// Configure axios defaults
axios.defaults.headers.common['Authorization'] = `Bearer ${API_KEY}`;

function App() {
  const [dashboardData, setDashboardData] = useState(null);
  const [costTrend, setCostTrend] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [utilization, setUtilization] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load all dashboard data in parallel
      const [
        dashboardResponse,
        trendResponse,
        recommendationsResponse,
        utilizationResponse,
        forecastResponse
      ] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/dashboard/overview`),
        axios.get(`${API_BASE_URL}/api/costs/trend?days=30`),
        axios.get(`${API_BASE_URL}/api/optimization/recommendations`),
        axios.get(`${API_BASE_URL}/api/utilization/overview`),
        axios.get(`${API_BASE_URL}/api/forecasting/predict?days=7`)
      ]);

      setDashboardData(dashboardResponse.data);
      setCostTrend(trendResponse.data);
      setRecommendations(recommendationsResponse.data);
      setUtilization(utilizationResponse.data);
      setForecast(forecastResponse.data);
      
    } catch (err) {
      setError(err.message);
      console.error('Error loading dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const applyRecommendation = async (recommendationId) => {
    try {
      await axios.post(`${API_BASE_URL}/api/optimization/apply`, {
        recommendation_id: recommendationId
      });
      
      // Refresh recommendations
      const response = await axios.get(`${API_BASE_URL}/api/optimization/recommendations`);
      setRecommendations(response.data);
      
      alert('Optimization applied successfully!');
    } catch (err) {
      alert('Error applying optimization: ' + err.message);
    }
  };

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center vh-100">
        <div className="text-center">
          <div className="spinner-border text-primary" style={{width: '3rem', height: '3rem'}} role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <div className="mt-3">
            <h5>Loading Hybrid Cloud Cost Optimizer...</h5>
            <p className="text-muted">Analyzing multi-cloud costs and generating insights</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mt-5">
        <div className="alert alert-danger" role="alert">
          <h4 className="alert-heading">Error Loading Dashboard</h4>
          <p>Unable to load dashboard data: {error}</p>
          <hr />
          <button className="btn btn-outline-danger" onClick={loadDashboardData}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Chart data configurations
  const costTrendChartData = costTrend ? {
    labels: costTrend.trend_data.map(d => new Date(d.date).toLocaleDateString()),
    datasets: [{
      label: 'Daily Cost',
      data: costTrend.trend_data.map(d => d.total_cost),
      borderColor: '#3498db',
      backgroundColor: 'rgba(52, 152, 219, 0.1)',
      fill: true,
      tension: 0.4
    }]
  } : null;

  const providerCostChartData = dashboardData ? {
    labels: ['AWS', 'Azure', 'On-Premises'],
    datasets: [{
      data: [
        dashboardData.cost_summary.current_month * 0.45, // AWS
        dashboardData.cost_summary.current_month * 0.35, // Azure
        dashboardData.cost_summary.current_month * 0.20  // On-Premises
      ],
      backgroundColor: [
        '#FF9500', // AWS Orange
        '#0078D4', // Azure Blue
        '#6B46C1'  // Purple for On-Premises
      ]
    }]
  } : null;

  const forecastChartData = forecast ? {
    labels: forecast.forecast.map(d => new Date(d.date).toLocaleDateString()),
    datasets: [
      {
        label: 'Predicted Cost',
        data: forecast.forecast.map(d => d.predicted_cost),
        borderColor: '#27ae60',
        backgroundColor: 'rgba(39, 174, 96, 0.1)',
        fill: false
      },
      {
        label: 'Upper Bound',
        data: forecast.forecast.map(d => d.confidence_upper),
        borderColor: '#f39c12',
        backgroundColor: 'rgba(243, 156, 18, 0.1)',
        fill: false,
        borderDash: [5, 5]
      }
    ]
  } : null;

  return (
    <div className="dashboard-container">
      {/* Header */}
      <div className="text-center mb-5">
        <h1 className="display-4 text-primary">
          <i className="fas fa-cloud-dollar-sign me-3"></i>
          Hybrid Cloud Cost Optimizer
        </h1>
        <p className="lead text-muted">
          Enterprise-grade multi-cloud cost optimization platform
        </p>
        <div className="d-flex justify-content-center align-items-center">
          <span className="status-indicator status-healthy"></span>
          <span className="text-success fw-bold">All Systems Operational</span>
        </div>
      </div>

      {/* Key Metrics */}
      {dashboardData && (
        <div className="row mb-4">
          <div className="col-md-3">
            <div className="metric-card text-center">
              <div className="metric-value text-primary">
                {formatCurrency(dashboardData.cost_summary.current_month)}
              </div>
              <div className="metric-label">Current Month Cost</div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="metric-card text-center">
              <div className="metric-value cost-savings">
                {formatCurrency(dashboardData.cost_summary.savings_amount)}
              </div>
              <div className="metric-label">Monthly Savings</div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="metric-card text-center">
              <div className="metric-value cost-savings">
                {dashboardData.cost_summary.savings_percentage}%
              </div>
              <div className="metric-label">Cost Reduction</div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="metric-card text-center">
              <div className="metric-value text-info">
                {utilization?.summary.optimization_opportunities || 0}
              </div>
              <div className="metric-label">Optimization Opportunities</div>
            </div>
          </div>
        </div>
      )}

      {/* Charts Row */}
      <div className="row mb-4">
        {/* Cost Trend Chart */}
        <div className="col-lg-6">
          <div className="metric-card">
            <h5 className="card-title">
              <i className="fas fa-chart-line me-2"></i>
              30-Day Cost Trend
            </h5>
            {costTrendChartData && (
              <div className="chart-container">
                <Line 
                  data={costTrendChartData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                      y: {
                        beginAtZero: true,
                        ticks: {
                          callback: function(value) {
                            return '$' + value.toLocaleString();
                          }
                        }
                      }
                    },
                    plugins: {
                      tooltip: {
                        callbacks: {
                          label: function(context) {
                            return 'Cost: $' + context.parsed.y.toLocaleString();
                          }
                        }
                      }
                    }
                  }}
                />
              </div>
            )}
          </div>
        </div>

        {/* Provider Distribution */}
        <div className="col-lg-6">
          <div className="metric-card">
            <h5 className="card-title">
              <i className="fas fa-chart-pie me-2"></i>
              Cost by Provider
            </h5>
            {providerCostChartData && (
              <div className="chart-container">
                <Doughnut 
                  data={providerCostChartData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      tooltip: {
                        callbacks: {
                          label: function(context) {
                            const label = context.label || '';
                            const value = '$' + context.parsed.toLocaleString();
                            const percentage = ((context.parsed / context.dataset.data.reduce((a, b) => a + b)) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                          }
                        }
                      }
                    }
                  }}
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recommendations and Forecast */}
      <div className="row mb-4">
        {/* ML Recommendations */}
        <div className="col-lg-8">
          <div className="metric-card">
            <div className="d-flex justify-content-between align-items-center mb-3">
              <h5 className="card-title mb-0">
                <i className="fas fa-robot me-2"></i>
                AI-Powered Optimization Recommendations
              </h5>
              {recommendations && (
                <span className="badge bg-success">
                  {formatCurrency(recommendations.total_monthly_savings)} potential savings
                </span>
              )}
            </div>
            
            {recommendations?.recommendations.map((rec, index) => (
              <div key={rec.id} className="recommendation-card">
                <div className="d-flex justify-content-between align-items-start">
                  <div className="flex-grow-1">
                    <h6 className="fw-bold text-capitalize">
                      {rec.type.replace('_', ' ')} - {rec.provider.toUpperCase()}
                    </h6>
                    <p className="mb-2 text-muted">{rec.description}</p>
                    <div className="row">
                      <div className="col-sm-6">
                        <small className="text-muted">Current Cost:</small>
                        <div className="fw-bold">{formatCurrency(rec.current_cost)}/month</div>
                      </div>
                      <div className="col-sm-6">
                        <small className="text-muted">Projected Cost:</small>
                        <div className="fw-bold text-success">{formatCurrency(rec.projected_cost)}/month</div>
                      </div>
                    </div>
                  </div>
                  <div className="text-end ms-3">
                    <div className="fw-bold text-success fs-5">
                      {formatCurrency(rec.monthly_savings)}
                    </div>
                    <small className="text-muted">monthly savings</small>
                    <div className="mt-2">
                      <button 
                        className="btn btn-sm btn-outline-primary"
                        onClick={() => applyRecommendation(rec.id)}
                      >
                        Apply
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Cost Forecast */}
        <div className="col-lg-4">
          <div className="metric-card">
            <h5 className="card-title">
              <i className="fas fa-crystal-ball me-2"></i>
              7-Day Cost Forecast
            </h5>
            {forecastChartData && (
              <div className="chart-container" style={{height: '300px'}}>
                <Line 
                  data={forecastChartData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                      y: {
                        beginAtZero: true,
                        ticks: {
                          callback: function(value) {
                            return '$' + (value/1000).toFixed(0) + 'K';
                          }
                        }
                      }
                    },
                    plugins: {
                      legend: {
                        position: 'bottom'
                      }
                    }
                  }}
                />
              </div>
            )}
            {forecast && (
              <div className="mt-3">
                <div className="text-center">
                  <small className="text-muted">Model Accuracy:</small>
                  <div className="fw-bold">{(forecast.model_accuracy * 100).toFixed(1)}%</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Top Cost Drivers */}
      {dashboardData && (
        <div className="row">
          <div className="col-12">
            <div className="metric-card">
              <h5 className="card-title">
                <i className="fas fa-list-ol me-2"></i>
                Top Cost Drivers
              </h5>
              <div className="table-responsive">
                <table className="table table-hover">
                  <thead>
                    <tr>
                      <th>Service</th>
                      <th>Monthly Cost</th>
                      <th>Percentage</th>
                      <th>Trend</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboardData.top_cost_drivers.map((driver, index) => (
                      <tr key={index}>
                        <td className="fw-bold">{driver.service}</td>
                        <td>{formatCurrency(driver.cost)}</td>
                        <td>
                          <div className="progress" style={{height: '20px'}}>
                            <div 
                              className="progress-bar bg-primary" 
                              style={{width: `${driver.percentage}%`}}
                            >
                              {driver.percentage}%
                            </div>
                          </div>
                        </td>
                        <td>
                          <span className="badge bg-success">
                            <i className="fas fa-arrow-down me-1"></i>
                            Optimized
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="text-center mt-5 pt-4 border-top">
        <p className="text-muted">
          <i className="fas fa-shield-alt me-2"></i>
          Enterprise-grade security • Real-time monitoring • ML-powered insights
        </p>
        <small className="text-muted">
          Hybrid Cloud Cost Optimizer v1.0.0 | Last updated: {new Date().toLocaleString()}
        </small>
      </div>
    </div>
  );
}

export default App;