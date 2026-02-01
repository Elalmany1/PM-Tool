/**
 * Frontend Integration Examples for KPI API
 * Complete examples for React, Vue, and vanilla JavaScript
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

const API_BASE_URL = 'http://localhost:8000';

// ============================================================================
// API CLIENT CLASS (Vanilla JS/TypeScript)
// ============================================================================

class KPIApiClient {
  constructor(baseUrl = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async request(endpoint, method = 'GET', data = null) {
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (data && (method === 'POST' || method === 'PUT')) {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, options);
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'API request failed');
      }
      
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // Financial Metrics
  async calculateARPU(totalRevenue, totalUsers, timeFrame = 'monthly') {
    return this.request('/metrics/arpu', 'POST', {
      total_revenue: totalRevenue,
      total_users: totalUsers,
      time_frame: timeFrame
    });
  }

  async calculateMRR(data) {
    // data can be either {arpu, number_of_accounts} or detailed breakdown
    return this.request('/metrics/mrr', 'POST', data);
  }

  async calculateCLTV(lifetimeMonths, arpu) {
    return this.request('/metrics/cltv', 'POST', {
      average_customer_lifetime_months: lifetimeMonths,
      average_revenue_per_user: arpu
    });
  }

  async calculateCAC(marketingSpend, salesSpend, newCustomers) {
    return this.request('/metrics/cac', 'POST', {
      total_marketing_spending: marketingSpend,
      total_sales_spending: salesSpend,
      number_of_new_customers: newCustomers
    });
  }

  // Customer Loyalty Metrics
  async calculateRetentionRate(customersStart, customersEnd, newCustomers) {
    return this.request('/metrics/retention-rate', 'POST', {
      customers_at_start: customersStart,
      customers_at_end: customersEnd,
      new_customers_acquired: newCustomers
    });
  }

  async calculateChurnRate(customersLost, totalCustomers, revenueLost = null, totalRevenue = null) {
    const data = {
      customers_lost: customersLost,
      total_customers_at_start: totalCustomers
    };
    if (revenueLost !== null) data.revenue_from_lost_customers = revenueLost;
    if (totalRevenue !== null) data.total_revenue_at_start = totalRevenue;
    
    return this.request('/metrics/churn-rate', 'POST', data);
  }

  async calculateNRR(mrrStart, expansion, contraction, churned) {
    return this.request('/metrics/nrr', 'POST', {
      mrr_at_beginning: mrrStart,
      expansion_revenue: expansion,
      contraction_revenue: contraction,
      churned_revenue: churned
    });
  }

  // User Engagement Metrics
  async calculateConversionRate(conversions, totalVisitors, conversionType = null) {
    const data = {
      number_of_conversions: conversions,
      total_visitors_or_users: totalVisitors
    };
    if (conversionType) data.conversion_type = conversionType;
    
    return this.request('/metrics/conversion-rate', 'POST', data);
  }

  async calculateTraffic(organicTraffic, paidTraffic, timeFrame = 'monthly') {
    return this.request('/metrics/traffic', 'POST', {
      organic_traffic: organicTraffic,
      paid_traffic: paidTraffic,
      time_frame: timeFrame
    });
  }

  async calculateDAUMAU(dau, mau, measurementDate = null) {
    const data = {
      daily_active_users: dau,
      monthly_active_users: mau
    };
    if (measurementDate) data.measurement_date = measurementDate;
    
    return this.request('/metrics/dau-mau', 'POST', data);
  }

  async calculateSessionDuration(totalDurationSeconds, totalSessions) {
    return this.request('/metrics/session-duration', 'POST', {
      total_session_duration_seconds: totalDurationSeconds,
      total_number_of_sessions: totalSessions
    });
  }

  async calculateBounceRate(nonEngagedSessions, totalSessions) {
    return this.request('/metrics/bounce-rate', 'POST', {
      number_of_non_engaged_sessions: nonEngagedSessions,
      total_number_of_sessions: totalSessions
    });
  }

  // Product Metrics
  async calculateSessionsPerUser(totalSessions, numberOfUsers) {
    return this.request('/metrics/sessions-per-user', 'POST', {
      total_number_of_sessions: totalSessions,
      number_of_users: numberOfUsers
    });
  }

  async calculateUserActions(totalActions, totalSessions, actionTypes = null) {
    const data = {
      total_actions: totalActions,
      total_sessions: totalSessions
    };
    if (actionTypes) data.action_types = actionTypes;
    
    return this.request('/metrics/user-actions', 'POST', data);
  }

  async calculateFeatureAdoption(usersUsingFeature, totalActiveUsers, featureName = null) {
    const data = {
      users_using_feature: usersUsingFeature,
      total_active_users: totalActiveUsers
    };
    if (featureName) data.feature_name = featureName;
    
    return this.request('/metrics/feature-adoption', 'POST', data);
  }

  // Satisfaction Metrics
  async calculateNPS(promoters, passives, detractors) {
    return this.request('/metrics/nps', 'POST', {
      promoters,
      passives,
      detractors
    });
  }

  async calculateCSAT(satisfiedResponses, totalResponses, scaleType = '5-point') {
    return this.request('/metrics/csat', 'POST', {
      number_of_satisfied_responses: satisfiedResponses,
      total_number_of_responses: totalResponses,
      scale_type: scaleType
    });
  }

  async calculateCES(sumOfScores, totalRespondents, scaleMax = 7) {
    return this.request('/metrics/ces', 'POST', {
      sum_of_all_effort_scores: sumOfScores,
      total_number_of_respondents: totalRespondents,
      scale_max: scaleMax
    });
  }

  // ML Predictions
  async predictMetric(metricName, historicalValues, periodsAhead = 3, timestamps = null) {
    const data = {
      metric_name: metricName,
      historical_values: historicalValues,
      periods_ahead: periodsAhead
    };
    if (timestamps) data.timestamps = timestamps;
    
    return this.request('/predict/metric', 'POST', data);
  }

  async analyzePattern(metricName, historicalValues, timestamps = null) {
    const data = {
      metric_name: metricName,
      historical_values: historicalValues
    };
    if (timestamps) data.timestamps = timestamps;
    
    return this.request('/analyze/pattern', 'POST', data);
  }

  // Utility
  async healthCheck() {
    return this.request('/health');
  }

  async listAllMetrics() {
    return this.request('/metrics/list');
  }
}

// ============================================================================
// REACT HOOKS
// ============================================================================

// Custom React hook for KPI calculations
function useKPIApi() {
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState(null);
  const apiClient = React.useMemo(() => new KPIApiClient(), []);

  const calculate = React.useCallback(async (metricFunction, ...args) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await metricFunction.apply(apiClient, args);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiClient]);

  return { calculate, loading, error, apiClient };
}

// ============================================================================
// REACT COMPONENT EXAMPLES
// ============================================================================

// Example 1: ARPU Calculator Component
function ARPUCalculator() {
  const [revenue, setRevenue] = React.useState('');
  const [users, setUsers] = React.useState('');
  const [result, setResult] = React.useState(null);
  const { calculate, loading, error } = useKPIApi();

  const handleCalculate = async () => {
    try {
      const data = await calculate(
        (api) => api.calculateARPU(
          parseFloat(revenue),
          parseInt(users)
        )
      );
      setResult(data);
    } catch (err) {
      console.error('Calculation failed:', err);
    }
  };

  return (
    <div className="arpu-calculator">
      <h2>ARPU Calculator</h2>
      
      <div className="input-group">
        <label>Total Revenue ($)</label>
        <input
          type="number"
          value={revenue}
          onChange={(e) => setRevenue(e.target.value)}
          placeholder="50000"
        />
      </div>

      <div className="input-group">
        <label>Total Users</label>
        <input
          type="number"
          value={users}
          onChange={(e) => setUsers(e.target.value)}
          placeholder="1000"
        />
      </div>

      <button 
        onClick={handleCalculate}
        disabled={loading || !revenue || !users}
      >
        {loading ? 'Calculating...' : 'Calculate ARPU'}
      </button>

      {error && <div className="error">{error}</div>}

      {result && (
        <div className="result">
          <h3>{result.metric_name}: ${result.value}</h3>
          <p>{result.interpretation}</p>
          <p className="benchmark"><small>{result.benchmark}</small></p>
        </div>
      )}
    </div>
  );
}

// Example 2: Churn Rate Calculator
function ChurnRateCalculator() {
  const [customersLost, setCustomersLost] = React.useState('');
  const [totalCustomers, setTotalCustomers] = React.useState('');
  const [result, setResult] = React.useState(null);
  const { calculate, loading } = useKPIApi();

  const handleCalculate = async () => {
    const data = await calculate(
      (api) => api.calculateChurnRate(
        parseInt(customersLost),
        parseInt(totalCustomers)
      )
    );
    setResult(data);
  };

  return (
    <div className="churn-calculator">
      <h2>Churn Rate Calculator</h2>
      
      <input
        type="number"
        value={customersLost}
        onChange={(e) => setCustomersLost(e.target.value)}
        placeholder="Customers Lost"
      />

      <input
        type="number"
        value={totalCustomers}
        onChange={(e) => setTotalCustomers(e.target.value)}
        placeholder="Total Customers at Start"
      />

      <button onClick={handleCalculate} disabled={loading}>
        Calculate Churn Rate
      </button>

      {result && (
        <div className={`result ${result.value > 5 ? 'warning' : 'good'}`}>
          <h3>Churn Rate: {result.value}%</h3>
          <p>{result.interpretation}</p>
        </div>
      )}
    </div>
  );
}

// Example 3: ML Prediction Component
function MetricPredictor() {
  const [metricName, setMetricName] = React.useState('churn_rate');
  const [historicalData, setHistoricalData] = React.useState('5.0,4.8,4.5,4.3,4.0,3.8,3.5');
  const [periodsAhead, setPeriodsAhead] = React.useState(3);
  const [prediction, setPrediction] = React.useState(null);
  const { calculate, loading } = useKPIApi();

  const handlePredict = async () => {
    const values = historicalData.split(',').map(v => parseFloat(v.trim()));
    const result = await calculate(
      (api) => api.predictMetric(metricName, values, periodsAhead)
    );
    setPrediction(result);
  };

  return (
    <div className="metric-predictor">
      <h2>Metric Predictor</h2>
      
      <select value={metricName} onChange={(e) => setMetricName(e.target.value)}>
        <option value="churn_rate">Churn Rate</option>
        <option value="mrr">MRR</option>
        <option value="dau">DAU</option>
      </select>

      <textarea
        value={historicalData}
        onChange={(e) => setHistoricalData(e.target.value)}
        placeholder="Historical values (comma-separated)"
        rows={3}
      />

      <input
        type="number"
        value={periodsAhead}
        onChange={(e) => setPeriodsAhead(parseInt(e.target.value))}
        min="1"
        max="12"
      />

      <button onClick={handlePredict} disabled={loading}>
        Predict
      </button>

      {prediction && (
        <div className="prediction-result">
          <h3>Predictions for {prediction.metric_name}</h3>
          <p>Current: {prediction.current_value}</p>
          <p>Trend: {prediction.trend} ({prediction.volatility} volatility)</p>
          <p>Confidence: {prediction.confidence_level}</p>
          
          <h4>Forecasted Values:</h4>
          <ul>
            {prediction.predictions.map((pred, idx) => (
              <li key={idx}>Period +{idx + 1}: {pred}</li>
            ))}
          </ul>

          <div className="insights">
            {prediction.insights.map((insight, idx) => (
              <p key={idx}>{insight}</p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// VUE.JS COMPOSITION API EXAMPLES
// ============================================================================

// Vue composable
const useKPI = () => {
  const loading = Vue.ref(false);
  const error = Vue.ref(null);
  const apiClient = new KPIApiClient();

  const calculate = async (metricFunction, ...args) => {
    loading.value = true;
    error.value = null;
    
    try {
      const result = await metricFunction.apply(apiClient, args);
      return result;
    } catch (err) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  return { calculate, loading, error, apiClient };
};

// Vue component example
const ARPUCalculatorVue = {
  setup() {
    const revenue = Vue.ref('');
    const users = Vue.ref('');
    const result = Vue.ref(null);
    const { calculate, loading, error } = useKPI();

    const handleCalculate = async () => {
      const data = await calculate(
        (api) => api.calculateARPU(
          parseFloat(revenue.value),
          parseInt(users.value)
        )
      );
      result.value = data;
    };

    return {
      revenue,
      users,
      result,
      loading,
      error,
      handleCalculate
    };
  },
  template: `
    <div class="arpu-calculator">
      <h2>ARPU Calculator</h2>
      <input v-model="revenue" type="number" placeholder="Total Revenue" />
      <input v-model="users" type="number" placeholder="Total Users" />
      <button @click="handleCalculate" :disabled="loading">Calculate</button>
      
      <div v-if="error" class="error">{{ error }}</div>
      
      <div v-if="result" class="result">
        <h3>{{ result.metric_name }}: ${{ result.value }}</h3>
        <p>{{ result.interpretation }}</p>
      </div>
    </div>
  `
};

// ============================================================================
// VANILLA JAVASCRIPT EXAMPLES
// ============================================================================

// Simple usage without framework
async function exampleUsage() {
  const api = new KPIApiClient();

  try {
    // Calculate ARPU
    const arpu = await api.calculateARPU(50000, 1000);
    console.log('ARPU:', arpu);

    // Calculate Churn Rate
    const churn = await api.calculateChurnRate(50, 1000);
    console.log('Churn Rate:', churn);

    // Predict future churn
    const prediction = await api.predictMetric(
      'churn_rate',
      [5.0, 4.8, 4.5, 4.3, 4.0, 3.8, 3.5],
      3
    );
    console.log('Churn Prediction:', prediction);

  } catch (error) {
    console.error('Error:', error);
  }
}

// Form submission example
document.getElementById('arpu-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const api = new KPIApiClient();
  const revenue = parseFloat(document.getElementById('revenue').value);
  const users = parseInt(document.getElementById('users').value);

  try {
    const result = await api.calculateARPU(revenue, users);
    
    document.getElementById('result').innerHTML = `
      <h3>${result.metric_name}: $${result.value}</h3>
      <p>${result.interpretation}</p>
      <p class="benchmark">${result.benchmark}</p>
    `;
  } catch (error) {
    document.getElementById('result').innerHTML = `
      <div class="error">Error: ${error.message}</div>
    `;
  }
});

// ============================================================================
// TYPESCRIPT DEFINITIONS
// ============================================================================

interface MetricResult {
  metric_name: string;
  value: number;
  unit: string;
  interpretation: string | null;
  benchmark: string | null;
  timestamp: string;
}

interface PredictionResult {
  metric_name: string;
  current_value: number | null;
  predictions: number[];
  confidence_level: 'high' | 'medium' | 'low';
  trend: 'increasing' | 'decreasing' | 'stable';
  volatility: 'high' | 'medium' | 'low';
  insights: string[];
}

// ============================================================================
// EXPORT FOR MODULE USAGE
// ============================================================================

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    KPIApiClient,
    useKPIApi,
    ARPUCalculator,
    ChurnRateCalculator,
    MetricPredictor
  };
}

if (typeof window !== 'undefined') {
  window.KPIApiClient = KPIApiClient;
}
