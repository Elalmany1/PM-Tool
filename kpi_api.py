"""
Product Management KPI API
FastAPI backend for calculating and predicting ALL product management metrics
Based on AltexSoft's 15 Key Product Management Metrics + Additional Essential Metrics
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum
import numpy as np
import pandas as pd
from scipy import stats
import json

# Try to import ML libraries
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

app = FastAPI(
    title="Product Management KPI API",
    description="Comprehensive API for calculating and predicting product management metrics",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class TimeFrame(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

# ============================================================================
# REQUEST/RESPONSE MODELS - ORGANIZED BY CATEGORY
# ============================================================================

# -------------------------
# 1. FINANCIAL METRICS
# -------------------------

class ARPUInput(BaseModel):
    """Average Revenue Per User calculation"""
    total_revenue: float = Field(..., description="Total revenue in the period", example=50000.0)
    total_users: int = Field(..., description="Total number of users", example=1000, gt=0)
    time_frame: TimeFrame = Field(default=TimeFrame.MONTHLY, description="Time period for calculation")

class MRRInput(BaseModel):
    """Monthly Recurring Revenue calculation"""
    # Method 1: Simple calculation
    arpu: Optional[float] = Field(None, description="Average Revenue Per User (monthly)", example=50.0)
    number_of_accounts: Optional[int] = Field(None, description="Number of subscriber accounts", example=1000)
    
    # Method 2: Detailed calculation
    current_monthly_subscriptions: Optional[float] = Field(None, description="Sum of all current monthly subscriptions", example=45000.0)
    revenue_new_subscriptions: Optional[float] = Field(None, description="Revenue from new subscriptions this month", example=5000.0)
    revenue_upgrades: Optional[float] = Field(None, description="Revenue from plan upgrades", example=2000.0)
    revenue_downgrades: Optional[float] = Field(None, description="Revenue lost from downgrades", example=500.0)
    revenue_lost_customers: Optional[float] = Field(None, description="Revenue lost from churned customers", example=1500.0)

class CLTVInput(BaseModel):
    """Customer Lifetime Value calculation"""
    average_customer_lifetime_months: float = Field(..., description="Average customer lifespan in months", example=24.0, gt=0)
    average_revenue_per_user: float = Field(..., description="Average monthly revenue per user (ARPU)", example=50.0, gt=0)

class CACInput(BaseModel):
    """Customer Acquisition Cost calculation"""
    total_marketing_spending: float = Field(..., description="Total marketing spend in period", example=10000.0, ge=0)
    total_sales_spending: float = Field(..., description="Total sales spend in period (including salaries)", example=5000.0, ge=0)
    number_of_new_customers: int = Field(..., description="Number of customers acquired in period", example=50, gt=0)

# -------------------------
# 2. CUSTOMER LOYALTY METRICS
# -------------------------

class RetentionRateInput(BaseModel):
    """Customer Retention Rate calculation"""
    customers_at_start: int = Field(..., description="Customers at the beginning of period", example=1000, gt=0)
    customers_at_end: int = Field(..., description="Customers at the end of period", example=950, ge=0)
    new_customers_acquired: int = Field(..., description="New customers acquired during period", example=100, ge=0)

class ChurnRateInput(BaseModel):
    """Customer and Revenue Churn Rate calculation"""
    # Customer churn
    customers_lost: int = Field(..., description="Number of customers who canceled/churned", example=50, ge=0)
    total_customers_at_start: int = Field(..., description="Total customers at beginning of period", example=1000, gt=0)
    
    # Revenue churn (optional)
    revenue_from_lost_customers: Optional[float] = Field(None, description="Revenue lost from churned customers", example=2500.0)
    total_revenue_at_start: Optional[float] = Field(None, description="Total revenue at beginning of period", example=50000.0)

class NRRInput(BaseModel):
    """Net Revenue Retention calculation"""
    mrr_at_beginning: float = Field(..., description="MRR at the start of period", example=50000.0, gt=0)
    expansion_revenue: float = Field(..., description="Revenue from expansions/upsells", example=5000.0, ge=0)
    contraction_revenue: float = Field(..., description="Revenue lost from downgrades", example=1000.0, ge=0)
    churned_revenue: float = Field(..., description="Revenue lost from churn", example=2000.0, ge=0)

# -------------------------
# 3. USER ENGAGEMENT METRICS
# -------------------------

class ConversionRateInput(BaseModel):
    """Conversion Rate calculation"""
    number_of_conversions: int = Field(..., description="Number of users who completed desired action", example=250, ge=0)
    total_visitors_or_users: int = Field(..., description="Total number of visitors/users exposed to CTA", example=10000, gt=0)
    conversion_type: Optional[str] = Field(None, description="Type of conversion (e.g., signup, purchase, download)", example="signup")

class TrafficInput(BaseModel):
    """Website Traffic metrics"""
    organic_traffic: int = Field(..., description="Visitors from organic search", example=5000, ge=0)
    paid_traffic: int = Field(..., description="Visitors from paid sources", example=3000, ge=0)
    time_frame: TimeFrame = Field(default=TimeFrame.MONTHLY, description="Time period")

class DAUMAUInput(BaseModel):
    """Daily/Monthly Active Users calculation"""
    daily_active_users: int = Field(..., description="Number of unique active users in a day", example=5000, ge=0)
    monthly_active_users: int = Field(..., description="Number of unique active users in a month", example=15000, gt=0)
    measurement_date: Optional[date] = Field(None, description="Date of measurement")

class SessionDurationInput(BaseModel):
    """Average Session Duration calculation"""
    total_session_duration_seconds: float = Field(..., description="Total time of all sessions in seconds", example=360000.0, ge=0)
    total_number_of_sessions: int = Field(..., description="Total number of sessions", example=10000, gt=0)

class BounceRateInput(BaseModel):
    """Bounce Rate calculation (GA4 definition)"""
    number_of_non_engaged_sessions: int = Field(..., description="Sessions <10s OR no conversion events OR <2 pages", example=4500, ge=0)
    total_number_of_sessions: int = Field(..., description="Total sessions", example=10000, gt=0)

# -------------------------
# 4. PRODUCT/FEATURE POPULARITY METRICS
# -------------------------

class SessionsPerUserInput(BaseModel):
    """Average Sessions Per User calculation"""
    total_number_of_sessions: int = Field(..., description="Total sessions in period", example=14000, ge=0)
    number_of_users: int = Field(..., description="Number of unique users in period", example=10000, gt=0)

class UserActionsInput(BaseModel):
    """User Actions Per Session calculation"""
    total_actions: int = Field(..., description="Total actions/interactions performed", example=50000, ge=0)
    total_sessions: int = Field(..., description="Total number of sessions", example=10000, gt=0)
    action_types: Optional[Dict[str, int]] = Field(None, description="Breakdown by action type", example={"clicks": 30000, "scrolls": 15000, "form_fills": 5000})

# -------------------------
# 5. USER SATISFACTION METRICS
# -------------------------

class NPSInput(BaseModel):
    """Net Promoter Score calculation"""
    promoters: int = Field(..., description="Users who rated 9-10", example=500, ge=0)
    passives: int = Field(..., description="Users who rated 7-8", example=300, ge=0)
    detractors: int = Field(..., description="Users who rated 0-6", example=200, ge=0)

class EGRInput(BaseModel):
    """Earned Growth Rate calculation"""
    # For NRR component
    mrr_at_beginning: float = Field(..., description="MRR at start of period", example=100000.0, gt=0)
    expansion_revenue: float = Field(..., description="Revenue from expansions/upsells", example=10000.0, ge=0)
    upsell_revenue: float = Field(..., description="Revenue from upsells", example=5000.0, ge=0)
    churn_revenue: float = Field(..., description="Revenue lost to churn", example=8000.0, ge=0)
    contraction_revenue: float = Field(..., description="Revenue lost to downgrades", example=2000.0, ge=0)
    
    # For ENC component
    new_customer_revenue_from_referrals: float = Field(..., description="Revenue from referred new customers", example=15000.0, ge=0)
    total_new_customer_revenue: float = Field(..., description="Total revenue from all new customers", example=50000.0, gt=0)

class CSATInput(BaseModel):
    """Customer Satisfaction Score calculation"""
    number_of_satisfied_responses: int = Field(..., description="Responses rated 4-5 (on 5-point scale) or 8-10 (on 10-point scale)", example=750, ge=0)
    total_number_of_responses: int = Field(..., description="Total survey responses", example=1000, gt=0)
    scale_type: Optional[str] = Field("5-point", description="Scale used: '5-point' or '10-point'")

class OSATInput(BaseModel):
    """Overall Satisfaction Score calculation"""
    number_of_satisfied_responses: int = Field(..., description="Overall satisfied responses (4-5 on 5-point or 8-10 on 10-point)", example=800, ge=0)
    total_number_of_responses: int = Field(..., description="Total survey responses", example=1000, gt=0)
    scale_type: Optional[str] = Field("5-point", description="Scale used: '5-point' or '10-point'")

class CESInput(BaseModel):
    """Customer Effort Score calculation"""
    sum_of_all_effort_scores: float = Field(..., description="Sum of all effort ratings", example=2500.0, ge=0)
    total_number_of_respondents: int = Field(..., description="Total survey respondents", example=1000, gt=0)
    scale_max: int = Field(7, description="Maximum value on scale (typically 5 or 7)", ge=1)

# -------------------------
# 6. ADDITIONAL ESSENTIAL PM METRICS
# -------------------------

class ActivationRateInput(BaseModel):
    """Activation Rate calculation"""
    activated_users: int = Field(..., description="Users who completed activation milestone", example=850, ge=0)
    total_signups: int = Field(..., description="Total new signups", example=1000, gt=0)
    activation_criteria: Optional[str] = Field(None, description="What defines 'activated'", example="Completed onboarding + first action")

class TimeToValueInput(BaseModel):
    """Time to Value calculation"""
    total_time_to_value_hours: float = Field(..., description="Sum of time for all users to reach value", example=2400.0, ge=0)
    number_of_users: int = Field(..., description="Number of users who reached value", example=800, gt=0)

class FeatureAdoptionInput(BaseModel):
    """Feature Adoption Rate calculation"""
    users_using_feature: int = Field(..., description="Users who used the feature at least once", example=600, ge=0)
    total_active_users: int = Field(..., description="Total active users in period", example=1000, gt=0)
    feature_name: Optional[str] = Field(None, description="Name of the feature", example="Advanced Reporting")

class ProductQualityInput(BaseModel):
    """Product Quality Metrics (Defect Rate, etc.)"""
    number_of_defects: int = Field(..., description="Number of bugs/defects reported", example=25, ge=0)
    total_features_or_releases: int = Field(..., description="Total features shipped or releases made", example=100, gt=0)

class VelocityInput(BaseModel):
    """Development Velocity (Story Points or Features)"""
    story_points_completed: int = Field(..., description="Story points completed in sprint", example=85, ge=0)
    sprint_length_days: int = Field(..., description="Sprint length in days", example=14, gt=0)
    team_size: Optional[int] = Field(None, description="Number of team members", example=8)

# -------------------------
# 7. ML PREDICTION INPUTS
# -------------------------

class HistoricalDataInput(BaseModel):
    """Historical data for ML predictions"""
    metric_name: str = Field(..., description="Name of metric to predict", example="churn_rate")
    historical_values: List[float] = Field(..., description="Historical values (time-ordered)", min_items=3)
    timestamps: Optional[List[str]] = Field(None, description="ISO timestamps for each value")
    periods_ahead: int = Field(3, description="Number of periods to predict into future", ge=1, le=12)

class BulkHistoricalInput(BaseModel):
    """Bulk historical data for multiple metrics"""
    data: Dict[str, List[float]] = Field(..., description="Dictionary of metric_name: [values]")
    timestamps: List[str] = Field(..., description="ISO timestamps (shared across all metrics)")

# -------------------------
# RESPONSE MODELS
# -------------------------

class MetricResult(BaseModel):
    """Standard metric calculation result"""
    metric_name: str
    value: float
    unit: str
    interpretation: Optional[str] = None
    benchmark: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class PredictionResult(BaseModel):
    """ML prediction result"""
    metric_name: str
    current_value: Optional[float] = None
    predictions: List[float]
    confidence_level: str  # "high", "medium", "low"
    trend: str  # "increasing", "decreasing", "stable"
    volatility: str  # "high", "medium", "low"
    insights: List[str]

class PatternAnalysisResult(BaseModel):
    """Pattern analysis result"""
    metric_name: str
    trend: str
    slope: float
    volatility_level: str
    volatility_value: float
    seasonality: str
    average: float
    recent_average: float
    insights: List[str]

class BulkMetricsResult(BaseModel):
    """Result for multiple metrics calculated at once"""
    timestamp: datetime = Field(default_factory=datetime.now)
    metrics: List[MetricResult]
    summary: Optional[Dict[str, Any]] = None

# ============================================================================
# CALCULATION FUNCTIONS
# ============================================================================

class KPICalculator:
    """All KPI calculation methods"""
    
    # -------------------------
    # FINANCIAL METRICS
    # -------------------------
    
    @staticmethod
    def calculate_arpu(data: ARPUInput) -> MetricResult:
        """Calculate Average Revenue Per User"""
        arpu = data.total_revenue / data.total_users
        
        return MetricResult(
            metric_name="ARPU",
            value=round(arpu, 2),
            unit="currency",
            interpretation=f"Average revenue per user: ${arpu:.2f} per {data.time_frame.value}",
            benchmark="Varies by industry. SaaS: $50-500/month typical"
        )
    
    @staticmethod
    def calculate_mrr(data: MRRInput) -> MetricResult:
        """Calculate Monthly Recurring Revenue"""
        # Method 1: Simple calculation
        if data.arpu is not None and data.number_of_accounts is not None:
            mrr = data.arpu * data.number_of_accounts
        # Method 2: Detailed calculation
        elif data.current_monthly_subscriptions is not None:
            mrr = (
                data.current_monthly_subscriptions +
                (data.revenue_new_subscriptions or 0) +
                (data.revenue_upgrades or 0) -
                (data.revenue_downgrades or 0) -
                (data.revenue_lost_customers or 0)
            )
        else:
            raise HTTPException(400, "Must provide either (arpu + number_of_accounts) or (current_monthly_subscriptions + other components)")
        
        arr = mrr * 12
        
        return MetricResult(
            metric_name="MRR",
            value=round(mrr, 2),
            unit="currency",
            interpretation=f"MRR: ${mrr:,.2f}, ARR: ${arr:,.2f}",
            benchmark="Target: 10-20% MoM growth for healthy SaaS"
        )
    
    @staticmethod
    def calculate_cltv(data: CLTVInput) -> MetricResult:
        """Calculate Customer Lifetime Value"""
        cltv = data.average_customer_lifetime_months * data.average_revenue_per_user
        
        return MetricResult(
            metric_name="CLTV",
            value=round(cltv, 2),
            unit="currency",
            interpretation=f"Customer lifetime value: ${cltv:,.2f}",
            benchmark="Should be 3x CAC minimum"
        )
    
    @staticmethod
    def calculate_cac(data: CACInput) -> MetricResult:
        """Calculate Customer Acquisition Cost"""
        total_spend = data.total_marketing_spending + data.total_sales_spending
        cac = total_spend / data.number_of_new_customers
        
        return MetricResult(
            metric_name="CAC",
            value=round(cac, 2),
            unit="currency",
            interpretation=f"Cost to acquire one customer: ${cac:,.2f}",
            benchmark="B2B SaaS average: $239. Ideal CAC:CLTV ratio is 1:3"
        )
    
    # -------------------------
    # CUSTOMER LOYALTY METRICS
    # -------------------------
    
    @staticmethod
    def calculate_retention_rate(data: RetentionRateInput) -> MetricResult:
        """Calculate Customer Retention Rate"""
        retention_rate = (
            (data.customers_at_end - data.new_customers_acquired) / 
            data.customers_at_start
        ) * 100
        
        retention_rate = max(0, min(100, retention_rate))  # Clamp between 0-100
        
        interpretation = "Excellent (>90%)" if retention_rate > 90 else \
                        "Good (75-90%)" if retention_rate > 75 else \
                        "Average (60-75%)" if retention_rate > 60 else \
                        "Needs improvement (<60%)"
        
        return MetricResult(
            metric_name="Retention Rate",
            value=round(retention_rate, 2),
            unit="percentage",
            interpretation=f"Customer retention: {retention_rate:.2f}% - {interpretation}",
            benchmark="SaaS: >90% good, >85% acceptable"
        )
    
    @staticmethod
    def calculate_churn_rate(data: ChurnRateInput) -> MetricResult:
        """Calculate Customer and Revenue Churn Rate"""
        customer_churn = (data.customers_lost / data.total_customers_at_start) * 100
        
        result_data = {
            "customer_churn_rate": round(customer_churn, 2)
        }
        
        if data.revenue_from_lost_customers and data.total_revenue_at_start:
            revenue_churn = (data.revenue_from_lost_customers / data.total_revenue_at_start) * 100
            result_data["revenue_churn_rate"] = round(revenue_churn, 2)
            interpretation = f"Customer churn: {customer_churn:.2f}%, Revenue churn: {revenue_churn:.2f}%"
        else:
            interpretation = f"Customer churn: {customer_churn:.2f}%"
        
        health_status = "Excellent (<2%)" if customer_churn < 2 else \
                       "Good (2-5%)" if customer_churn < 5 else \
                       "Acceptable (5-7%)" if customer_churn < 7 else \
                       "High - needs attention (>7%)"
        
        return MetricResult(
            metric_name="Churn Rate",
            value=round(customer_churn, 2),
            unit="percentage",
            interpretation=f"{interpretation} - {health_status}",
            benchmark="SaaS monthly: <5% good, <2% excellent"
        )
    
    @staticmethod
    def calculate_nrr(data: NRRInput) -> MetricResult:
        """Calculate Net Revenue Retention"""
        end_mrr = (
            data.mrr_at_beginning +
            data.expansion_revenue -
            data.contraction_revenue -
            data.churned_revenue
        )
        
        nrr = (end_mrr / data.mrr_at_beginning) * 100
        
        interpretation = "Excellent (>110%)" if nrr > 110 else \
                        "Good (100-110%)" if nrr >= 100 else \
                        "Needs improvement (<100%)"
        
        return MetricResult(
            metric_name="Net Revenue Retention (NRR)",
            value=round(nrr, 2),
            unit="percentage",
            interpretation=f"NRR: {nrr:.2f}% - {interpretation}",
            benchmark=">100% means growing revenue from existing customers. >110% is excellent"
        )
    
    # -------------------------
    # USER ENGAGEMENT METRICS
    # -------------------------
    
    @staticmethod
    def calculate_conversion_rate(data: ConversionRateInput) -> MetricResult:
        """Calculate Conversion Rate"""
        conversion_rate = (data.number_of_conversions / data.total_visitors_or_users) * 100
        
        interpretation = "Excellent (>5%)" if conversion_rate > 5 else \
                        "Good (2-5%)" if conversion_rate >= 2 else \
                        "Needs improvement (<2%)"
        
        return MetricResult(
            metric_name="Conversion Rate",
            value=round(conversion_rate, 2),
            unit="percentage",
            interpretation=f"Conversion rate: {conversion_rate:.2f}% - {interpretation}",
            benchmark="E-commerce: 2-3%, SaaS: 3-5%, Landing pages: 5-15%"
        )
    
    @staticmethod
    def calculate_traffic(data: TrafficInput) -> MetricResult:
        """Calculate Total Traffic and breakdown"""
        total_traffic = data.organic_traffic + data.paid_traffic
        organic_percentage = (data.organic_traffic / total_traffic * 100) if total_traffic > 0 else 0
        
        return MetricResult(
            metric_name="Website Traffic",
            value=total_traffic,
            unit="visitors",
            interpretation=f"Total: {total_traffic:,} ({organic_percentage:.1f}% organic, {100-organic_percentage:.1f}% paid)",
            benchmark="Aim for 70%+ organic traffic for sustainable growth"
        )
    
    @staticmethod
    def calculate_dau_mau(data: DAUMAUInput) -> MetricResult:
        """Calculate DAU/MAU Stickiness Ratio"""
        stickiness = (data.daily_active_users / data.monthly_active_users) * 100
        
        interpretation = "Excellent (>40%)" if stickiness > 40 else \
                        "Good (20-40%)" if stickiness >= 20 else \
                        "Needs improvement (<20%)"
        
        return MetricResult(
            metric_name="DAU/MAU Stickiness",
            value=round(stickiness, 2),
            unit="percentage",
            interpretation=f"Stickiness: {stickiness:.2f}% - {interpretation}. DAU: {data.daily_active_users:,}, MAU: {data.monthly_active_users:,}",
            benchmark=">20% good, >40% excellent. Varies by product type"
        )
    
    @staticmethod
    def calculate_session_duration(data: SessionDurationInput) -> MetricResult:
        """Calculate Average Session Duration"""
        avg_duration_seconds = data.total_session_duration_seconds / data.total_number_of_sessions
        avg_duration_minutes = avg_duration_seconds / 60
        
        return MetricResult(
            metric_name="Average Session Duration",
            value=round(avg_duration_seconds, 2),
            unit="seconds",
            interpretation=f"Average session: {avg_duration_minutes:.2f} minutes ({avg_duration_seconds:.0f} seconds)",
            benchmark="Varies widely by industry. E-commerce: 2-3 min, Media: 5-10 min"
        )
    
    @staticmethod
    def calculate_bounce_rate(data: BounceRateInput) -> MetricResult:
        """Calculate Bounce Rate (GA4 definition)"""
        bounce_rate = (data.number_of_non_engaged_sessions / data.total_number_of_sessions) * 100
        
        interpretation = "Excellent (<35%)" if bounce_rate < 35 else \
                        "Good (35-50%)" if bounce_rate < 50 else \
                        "High - needs improvement (>50%)"
        
        return MetricResult(
            metric_name="Bounce Rate",
            value=round(bounce_rate, 2),
            unit="percentage",
            interpretation=f"Bounce rate: {bounce_rate:.2f}% - {interpretation}",
            benchmark="<40% good. Varies by industry (see Contentsquare benchmarks)"
        )
    
    # -------------------------
    # PRODUCT/FEATURE METRICS
    # -------------------------
    
    @staticmethod
    def calculate_sessions_per_user(data: SessionsPerUserInput) -> MetricResult:
        """Calculate Average Sessions Per User"""
        avg_sessions = data.total_number_of_sessions / data.number_of_users
        
        interpretation = "Excellent (>2.0)" if avg_sessions > 2.0 else \
                        "Good (1.4-2.0)" if avg_sessions >= 1.4 else \
                        "Needs improvement (<1.4)"
        
        return MetricResult(
            metric_name="Sessions Per User",
            value=round(avg_sessions, 2),
            unit="sessions",
            interpretation=f"Average: {avg_sessions:.2f} sessions per user - {interpretation}",
            benchmark="Average is 1.4, >2.0 indicates good engagement"
        )
    
    @staticmethod
    def calculate_user_actions(data: UserActionsInput) -> MetricResult:
        """Calculate User Actions Per Session"""
        avg_actions = data.total_actions / data.total_sessions
        
        return MetricResult(
            metric_name="User Actions Per Session",
            value=round(avg_actions, 2),
            unit="actions",
            interpretation=f"Average: {avg_actions:.2f} actions per session",
            benchmark="Higher is better. Track trends and correlate with retention"
        )
    
    # -------------------------
    # USER SATISFACTION METRICS
    # -------------------------
    
    @staticmethod
    def calculate_nps(data: NPSInput) -> MetricResult:
        """Calculate Net Promoter Score"""
        total_responses = data.promoters + data.passives + data.detractors
        
        if total_responses == 0:
            raise HTTPException(400, "Total responses cannot be zero")
        
        promoter_pct = (data.promoters / total_responses) * 100
        detractor_pct = (data.detractors / total_responses) * 100
        
        nps = promoter_pct - detractor_pct
        
        interpretation = "Excellent (>50)" if nps > 50 else \
                        "Good (30-50)" if nps > 30 else \
                        "Average (0-30)" if nps >= 0 else \
                        "Needs urgent improvement (<0)"
        
        return MetricResult(
            metric_name="Net Promoter Score (NPS)",
            value=round(nps, 2),
            unit="score",
            interpretation=f"NPS: {nps:.2f} - {interpretation}. Promoters: {promoter_pct:.1f}%, Detractors: {detractor_pct:.1f}%",
            benchmark=">50 excellent, 30-50 good, 0-30 average, <0 poor"
        )
    
    @staticmethod
    def calculate_egr(data: EGRInput) -> MetricResult:
        """Calculate Earned Growth Rate"""
        # Calculate NRR
        end_mrr = (
            data.mrr_at_beginning +
            data.expansion_revenue +
            data.upsell_revenue -
            data.churn_revenue -
            data.contraction_revenue
        )
        nrr = (end_mrr / data.mrr_at_beginning) * 100
        
        # Calculate ENC (Earned New Customers)
        enc = (data.new_customer_revenue_from_referrals / data.total_new_customer_revenue) * 100
        
        # Calculate EGR
        egr = nrr + enc - 100
        
        interpretation = "Excellent (>20%)" if egr > 20 else \
                        "Good (10-20%)" if egr > 10 else \
                        "Average (0-10%)" if egr >= 0 else \
                        "Negative growth"
        
        return MetricResult(
            metric_name="Earned Growth Rate (EGR)",
            value=round(egr, 2),
            unit="percentage",
            interpretation=f"EGR: {egr:.2f}% - {interpretation}. NRR: {nrr:.2f}%, ENC: {enc:.2f}%",
            benchmark="Positive EGR indicates organic growth from loyalty and referrals"
        )
    
    @staticmethod
    def calculate_csat(data: CSATInput) -> MetricResult:
        """Calculate Customer Satisfaction Score"""
        csat = (data.number_of_satisfied_responses / data.total_number_of_responses) * 100
        
        interpretation = "Excellent (>80%)" if csat > 80 else \
                        "Good (70-80%)" if csat >= 70 else \
                        "Average (60-70%)" if csat >= 60 else \
                        "Needs improvement (<60%)"
        
        return MetricResult(
            metric_name="Customer Satisfaction Score (CSAT)",
            value=round(csat, 2),
            unit="percentage",
            interpretation=f"CSAT: {csat:.2f}% - {interpretation}",
            benchmark=">75% is good, varies by industry"
        )
    
    @staticmethod
    def calculate_osat(data: OSATInput) -> MetricResult:
        """Calculate Overall Satisfaction Score"""
        osat = (data.number_of_satisfied_responses / data.total_number_of_responses) * 100
        
        interpretation = "Excellent (>80%)" if osat > 80 else \
                        "Good (70-80%)" if osat >= 70 else \
                        "Average (60-70%)" if osat >= 60 else \
                        "Needs improvement (<60%)"
        
        return MetricResult(
            metric_name="Overall Satisfaction Score (OSAT)",
            value=round(osat, 2),
            unit="percentage",
            interpretation=f"OSAT: {osat:.2f}% - {interpretation}",
            benchmark="Check ACSI (American Customer Satisfaction Index) for industry benchmarks"
        )
    
    @staticmethod
    def calculate_ces(data: CESInput) -> MetricResult:
        """Calculate Customer Effort Score"""
        ces = data.sum_of_all_effort_scores / data.total_number_of_respondents
        
        # Lower CES is better (less effort)
        interpretation = "Excellent - Very easy (<2.0)" if ces < 2.0 else \
                        "Good - Easy (2.0-3.0)" if ces < 3.0 else \
                        "Average - Moderate effort (3.0-4.0)" if ces < 4.0 else \
                        "High effort - needs improvement (>4.0)"
        
        return MetricResult(
            metric_name="Customer Effort Score (CES)",
            value=round(ces, 2),
            unit="score",
            interpretation=f"CES: {ces:.2f} on {data.scale_max}-point scale - {interpretation}",
            benchmark="Lower is better. <3.0 on 7-point scale is good"
        )
    
    # -------------------------
    # ADDITIONAL PM METRICS
    # -------------------------
    
    @staticmethod
    def calculate_activation_rate(data: ActivationRateInput) -> MetricResult:
        """Calculate Activation Rate"""
        activation_rate = (data.activated_users / data.total_signups) * 100
        
        interpretation = "Excellent (>60%)" if activation_rate > 60 else \
                        "Good (40-60%)" if activation_rate >= 40 else \
                        "Needs improvement (<40%)"
        
        return MetricResult(
            metric_name="Activation Rate",
            value=round(activation_rate, 2),
            unit="percentage",
            interpretation=f"Activation: {activation_rate:.2f}% - {interpretation}",
            benchmark=">50% is good. Define clear activation criteria"
        )
    
    @staticmethod
    def calculate_time_to_value(data: TimeToValueInput) -> MetricResult:
        """Calculate Average Time to Value"""
        avg_ttv_hours = data.total_time_to_value_hours / data.number_of_users
        avg_ttv_days = avg_ttv_hours / 24
        
        return MetricResult(
            metric_name="Time to Value (TTV)",
            value=round(avg_ttv_hours, 2),
            unit="hours",
            interpretation=f"Average time to value: {avg_ttv_hours:.2f} hours ({avg_ttv_days:.2f} days)",
            benchmark="Shorter is better. Aim for <24 hours for SaaS products"
        )
    
    @staticmethod
    def calculate_feature_adoption(data: FeatureAdoptionInput) -> MetricResult:
        """Calculate Feature Adoption Rate"""
        adoption_rate = (data.users_using_feature / data.total_active_users) * 100
        
        interpretation = "High adoption (>50%)" if adoption_rate > 50 else \
                        "Moderate adoption (25-50%)" if adoption_rate >= 25 else \
                        "Low adoption (<25%)"
        
        return MetricResult(
            metric_name="Feature Adoption Rate",
            value=round(adoption_rate, 2),
            unit="percentage",
            interpretation=f"Adoption: {adoption_rate:.2f}% - {interpretation}",
            benchmark="Target depends on feature type. Core features should have >50% adoption"
        )
    
    @staticmethod
    def calculate_product_quality(data: ProductQualityInput) -> MetricResult:
        """Calculate Defect/Escape Rate"""
        defect_rate = (data.number_of_defects / data.total_features_or_releases) * 100
        
        interpretation = "Excellent (<5%)" if defect_rate < 5 else \
                        "Good (5-10%)" if defect_rate < 10 else \
                        "Needs improvement (>10%)"
        
        return MetricResult(
            metric_name="Defect Rate",
            value=round(defect_rate, 2),
            unit="percentage",
            interpretation=f"Defect rate: {defect_rate:.2f}% - {interpretation}",
            benchmark="<5% is excellent. Track trends over time"
        )
    
    @staticmethod
    def calculate_velocity(data: VelocityInput) -> MetricResult:
        """Calculate Development Velocity"""
        velocity_per_day = data.story_points_completed / data.sprint_length_days
        
        if data.team_size:
            velocity_per_person = data.story_points_completed / data.team_size
            interpretation = f"Velocity: {data.story_points_completed} points in {data.sprint_length_days} days. {velocity_per_person:.2f} points per person"
        else:
            interpretation = f"Velocity: {data.story_points_completed} points in {data.sprint_length_days} days ({velocity_per_day:.2f} points/day)"
        
        return MetricResult(
            metric_name="Development Velocity",
            value=data.story_points_completed,
            unit="story_points",
            interpretation=interpretation,
            benchmark="Track trends over time. Aim for consistent velocity, not maximum"
        )


class MLPredictor:
    """Machine Learning prediction engine"""
    
    @staticmethod
    def prepare_time_series_data(historical_data: List[float], lookback: int = 3):
        """Prepare time series data for ML"""
        X, y = [], []
        for i in range(lookback, len(historical_data)):
            X.append(historical_data[i-lookback:i])
            y.append(historical_data[i])
        return np.array(X), np.array(y)
    
    @staticmethod
    def predict_metric(data: HistoricalDataInput) -> PredictionResult:
        """Predict future values for any metric"""
        if len(data.historical_values) < 3:
            raise HTTPException(400, "Need at least 3 historical data points for prediction")
        
        historical_values = data.historical_values
        
        # Pattern analysis
        pattern = MLPredictor.detect_patterns(historical_values)
        
        # Make predictions
        if not SKLEARN_AVAILABLE or len(historical_values) < 5:
            # Fallback: Simple moving average with trend
            recent_values = historical_values[-3:]
            trend_slope = (historical_values[-1] - historical_values[0]) / len(historical_values)
            
            predictions = []
            last_value = historical_values[-1]
            for i in range(data.periods_ahead):
                pred = last_value + trend_slope * (i + 1)
                predictions.append(max(0, pred))
            
            confidence = "low"
        else:
            # ML prediction
            X, y = MLPredictor.prepare_time_series_data(historical_values)
            
            if len(X) == 0:
                # Not enough data for ML
                avg_value = np.mean(historical_values)
                predictions = [avg_value] * data.periods_ahead
                confidence = "low"
            else:
                # Use Gradient Boosting
                model = GradientBoostingRegressor(n_estimators=50, random_state=42)
                model.fit(X, y)
                
                predictions = []
                current_window = list(historical_values[-3:])
                
                for _ in range(data.periods_ahead):
                    pred = model.predict([current_window])[0]
                    predictions.append(max(0, pred))
                    current_window = current_window[1:] + [pred]
                
                # Determine confidence based on data quality
                if len(historical_values) >= 10 and pattern['volatility'] < 0.3:
                    confidence = "high"
                elif len(historical_values) >= 5:
                    confidence = "medium"
                else:
                    confidence = "low"
        
        # Generate insights
        insights = []
        if pattern['trend'] == 'increasing':
            insights.append(f"📈 Upward trend detected with slope {pattern['slope']:.4f}")
        elif pattern['trend'] == 'decreasing':
            insights.append(f"📉 Downward trend detected with slope {pattern['slope']:.4f}")
        else:
            insights.append("➡️ Metric appears stable")
        
        if pattern['volatility_level'] == 'high':
            insights.append("⚠️ High volatility detected - predictions may be less reliable")
        
        if predictions[0] > historical_values[-1] * 1.2:
            insights.append("🚀 Significant growth predicted")
        elif predictions[0] < historical_values[-1] * 0.8:
            insights.append("⚠️ Significant decline predicted")
        
        return PredictionResult(
            metric_name=data.metric_name,
            current_value=historical_values[-1],
            predictions=[round(p, 2) for p in predictions],
            confidence_level=confidence,
            trend=pattern['trend'],
            volatility=pattern['volatility_level'],
            insights=insights
        )
    
    @staticmethod
    def detect_patterns(data: List[float]) -> Dict[str, Any]:
        """Detect patterns in time series data"""
        if len(data) < 3:
            return {
                "pattern": "insufficient_data",
                "trend": "unknown",
                "slope": 0,
                "volatility": 0,
                "volatility_level": "unknown",
                "avg": 0,
                "recent_avg": 0
            }
        
        # Calculate trend using linear regression
        x = np.arange(len(data))
        y = np.array(data)
        
        if SKLEARN_AVAILABLE:
            model = LinearRegression()
            model.fit(x.reshape(-1, 1), y)
            slope = model.coef_[0]
        else:
            # Simple linear regression
            slope = (y[-1] - y[0]) / len(data)
        
        trend = "increasing" if slope > 0.01 else "decreasing" if slope < -0.01 else "stable"
        
        # Calculate volatility (coefficient of variation)
        mean_val = np.mean(data)
        volatility = np.std(data) / mean_val if mean_val != 0 else 0
        
        volatility_level = "high" if volatility > 0.3 else "medium" if volatility > 0.1 else "low"
        
        return {
            "trend": trend,
            "slope": slope,
            "volatility": volatility,
            "volatility_level": volatility_level,
            "avg": np.mean(data),
            "recent_avg": np.mean(data[-3:]) if len(data) >= 3 else np.mean(data)
        }
    
    @staticmethod
    def analyze_pattern(data: HistoricalDataInput) -> PatternAnalysisResult:
        """Analyze patterns in historical data"""
        pattern = MLPredictor.detect_patterns(data.historical_values)
        
        # Generate insights
        insights = []
        
        if pattern['trend'] == 'increasing':
            insights.append(f"✅ Positive trend: Metric is growing at {pattern['slope']:.4f} per period")
        elif pattern['trend'] == 'decreasing':
            insights.append(f"⚠️ Negative trend: Metric is declining at {pattern['slope']:.4f} per period")
        else:
            insights.append("➡️ Stable: No significant trend detected")
        
        if pattern['volatility_level'] == 'high':
            insights.append("📊 High volatility: Metric shows significant fluctuation")
        elif pattern['volatility_level'] == 'low':
            insights.append("📊 Low volatility: Metric is relatively stable")
        
        if pattern['recent_avg'] > pattern['avg'] * 1.1:
            insights.append("🔥 Recent performance is above historical average")
        elif pattern['recent_avg'] < pattern['avg'] * 0.9:
            insights.append("⚠️ Recent performance is below historical average")
        
        return PatternAnalysisResult(
            metric_name=data.metric_name,
            trend=pattern['trend'],
            slope=round(pattern['slope'], 4),
            volatility_level=pattern['volatility_level'],
            volatility_value=round(pattern['volatility'], 4),
            seasonality="Not detected (need more data)" if len(data.historical_values) < 12 else "Analysis requires 12+ periods",
            average=round(pattern['avg'], 2),
            recent_average=round(pattern['recent_avg'], 2),
            insights=insights
        )


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
def read_root():
    """API root endpoint"""
    return {
        "message": "Product Management KPI API",
        "version": "2.0.0",
        "documentation": "/docs",
        "metrics_available": 25,
        "categories": [
            "Financial Metrics",
            "Customer Loyalty Metrics",
            "User Engagement Metrics",
            "Product/Feature Popularity Metrics",
            "User Satisfaction Metrics",
            "Additional PM Metrics",
            "ML Predictions"
        ]
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "sklearn_available": SKLEARN_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }

# -------------------------
# FINANCIAL METRICS ENDPOINTS
# -------------------------

@app.post("/metrics/arpu", response_model=MetricResult, tags=["Financial Metrics"])
def calculate_arpu(data: ARPUInput):
    """Calculate Average Revenue Per User (ARPU)"""
    return KPICalculator.calculate_arpu(data)

@app.post("/metrics/mrr", response_model=MetricResult, tags=["Financial Metrics"])
def calculate_mrr(data: MRRInput):
    """Calculate Monthly Recurring Revenue (MRR) and Annual Recurring Revenue (ARR)"""
    return KPICalculator.calculate_mrr(data)

@app.post("/metrics/cltv", response_model=MetricResult, tags=["Financial Metrics"])
def calculate_cltv(data: CLTVInput):
    """Calculate Customer Lifetime Value (CLTV/LTV)"""
    return KPICalculator.calculate_cltv(data)

@app.post("/metrics/cac", response_model=MetricResult, tags=["Financial Metrics"])
def calculate_cac(data: CACInput):
    """Calculate Customer Acquisition Cost (CAC)"""
    return KPICalculator.calculate_cac(data)

# -------------------------
# CUSTOMER LOYALTY ENDPOINTS
# -------------------------

@app.post("/metrics/retention-rate", response_model=MetricResult, tags=["Customer Loyalty"])
def calculate_retention_rate(data: RetentionRateInput):
    """Calculate Customer Retention Rate (CRR)"""
    return KPICalculator.calculate_retention_rate(data)

@app.post("/metrics/churn-rate", response_model=MetricResult, tags=["Customer Loyalty"])
def calculate_churn_rate(data: ChurnRateInput):
    """Calculate Customer Churn Rate and Revenue Churn Rate"""
    return KPICalculator.calculate_churn_rate(data)

@app.post("/metrics/nrr", response_model=MetricResult, tags=["Customer Loyalty"])
def calculate_nrr(data: NRRInput):
    """Calculate Net Revenue Retention (NRR)"""
    return KPICalculator.calculate_nrr(data)

# -------------------------
# USER ENGAGEMENT ENDPOINTS
# -------------------------

@app.post("/metrics/conversion-rate", response_model=MetricResult, tags=["User Engagement"])
def calculate_conversion_rate(data: ConversionRateInput):
    """Calculate Conversion Rate"""
    return KPICalculator.calculate_conversion_rate(data)

@app.post("/metrics/traffic", response_model=MetricResult, tags=["User Engagement"])
def calculate_traffic(data: TrafficInput):
    """Calculate Website Traffic (Organic/Paid)"""
    return KPICalculator.calculate_traffic(data)

@app.post("/metrics/dau-mau", response_model=MetricResult, tags=["User Engagement"])
def calculate_dau_mau(data: DAUMAUInput):
    """Calculate DAU/MAU Stickiness Ratio"""
    return KPICalculator.calculate_dau_mau(data)

@app.post("/metrics/session-duration", response_model=MetricResult, tags=["User Engagement"])
def calculate_session_duration(data: SessionDurationInput):
    """Calculate Average Session Duration"""
    return KPICalculator.calculate_session_duration(data)

@app.post("/metrics/bounce-rate", response_model=MetricResult, tags=["User Engagement"])
def calculate_bounce_rate(data: BounceRateInput):
    """Calculate Bounce Rate (GA4 definition)"""
    return KPICalculator.calculate_bounce_rate(data)

# -------------------------
# PRODUCT/FEATURE ENDPOINTS
# -------------------------

@app.post("/metrics/sessions-per-user", response_model=MetricResult, tags=["Product Metrics"])
def calculate_sessions_per_user(data: SessionsPerUserInput):
    """Calculate Average Sessions Per User"""
    return KPICalculator.calculate_sessions_per_user(data)

@app.post("/metrics/user-actions", response_model=MetricResult, tags=["Product Metrics"])
def calculate_user_actions(data: UserActionsInput):
    """Calculate User Actions Per Session"""
    return KPICalculator.calculate_user_actions(data)

@app.post("/metrics/feature-adoption", response_model=MetricResult, tags=["Product Metrics"])
def calculate_feature_adoption(data: FeatureAdoptionInput):
    """Calculate Feature Adoption Rate"""
    return KPICalculator.calculate_feature_adoption(data)

# -------------------------
# USER SATISFACTION ENDPOINTS
# -------------------------

@app.post("/metrics/nps", response_model=MetricResult, tags=["User Satisfaction"])
def calculate_nps(data: NPSInput):
    """Calculate Net Promoter Score (NPS)"""
    return KPICalculator.calculate_nps(data)

@app.post("/metrics/egr", response_model=MetricResult, tags=["User Satisfaction"])
def calculate_egr(data: EGRInput):
    """Calculate Earned Growth Rate (EGR)"""
    return KPICalculator.calculate_egr(data)

@app.post("/metrics/csat", response_model=MetricResult, tags=["User Satisfaction"])
def calculate_csat(data: CSATInput):
    """Calculate Customer Satisfaction Score (CSAT)"""
    return KPICalculator.calculate_csat(data)

@app.post("/metrics/osat", response_model=MetricResult, tags=["User Satisfaction"])
def calculate_osat(data: OSATInput):
    """Calculate Overall Satisfaction Score (OSAT)"""
    return KPICalculator.calculate_osat(data)

@app.post("/metrics/ces", response_model=MetricResult, tags=["User Satisfaction"])
def calculate_ces(data: CESInput):
    """Calculate Customer Effort Score (CES)"""
    return KPICalculator.calculate_ces(data)

# -------------------------
# ADDITIONAL PM METRICS
# -------------------------

@app.post("/metrics/activation-rate", response_model=MetricResult, tags=["Additional Metrics"])
def calculate_activation_rate(data: ActivationRateInput):
    """Calculate Activation Rate"""
    return KPICalculator.calculate_activation_rate(data)

@app.post("/metrics/time-to-value", response_model=MetricResult, tags=["Additional Metrics"])
def calculate_time_to_value(data: TimeToValueInput):
    """Calculate Time to Value (TTV)"""
    return KPICalculator.calculate_time_to_value(data)

@app.post("/metrics/product-quality", response_model=MetricResult, tags=["Additional Metrics"])
def calculate_product_quality(data: ProductQualityInput):
    """Calculate Defect/Escape Rate"""
    return KPICalculator.calculate_product_quality(data)

@app.post("/metrics/velocity", response_model=MetricResult, tags=["Additional Metrics"])
def calculate_velocity(data: VelocityInput):
    """Calculate Development Velocity"""
    return KPICalculator.calculate_velocity(data)

# -------------------------
# ML PREDICTION ENDPOINTS
# -------------------------

@app.post("/predict/metric", response_model=PredictionResult, tags=["ML Predictions"])
def predict_metric(data: HistoricalDataInput):
    """Predict future values for any metric using ML"""
    return MLPredictor.predict_metric(data)

@app.post("/analyze/pattern", response_model=PatternAnalysisResult, tags=["ML Predictions"])
def analyze_pattern(data: HistoricalDataInput):
    """Analyze patterns in historical metric data"""
    return MLPredictor.analyze_pattern(data)

# -------------------------
# BULK OPERATIONS
# -------------------------

@app.get("/metrics/list", tags=["Utility"])
def list_all_metrics():
    """Get list of all available metrics with their input requirements"""
    return {
        "financial_metrics": {
            "arpu": {
                "name": "Average Revenue Per User",
                "endpoint": "/metrics/arpu",
                "required_fields": ["total_revenue", "total_users"]
            },
            "mrr": {
                "name": "Monthly Recurring Revenue",
                "endpoint": "/metrics/mrr",
                "required_fields": ["arpu + number_of_accounts OR current_monthly_subscriptions + components"]
            },
            "cltv": {
                "name": "Customer Lifetime Value",
                "endpoint": "/metrics/cltv",
                "required_fields": ["average_customer_lifetime_months", "average_revenue_per_user"]
            },
            "cac": {
                "name": "Customer Acquisition Cost",
                "endpoint": "/metrics/cac",
                "required_fields": ["total_marketing_spending", "total_sales_spending", "number_of_new_customers"]
            }
        },
        "customer_loyalty_metrics": {
            "retention_rate": {
                "name": "Customer Retention Rate",
                "endpoint": "/metrics/retention-rate",
                "required_fields": ["customers_at_start", "customers_at_end", "new_customers_acquired"]
            },
            "churn_rate": {
                "name": "Churn Rate",
                "endpoint": "/metrics/churn-rate",
                "required_fields": ["customers_lost", "total_customers_at_start"]
            },
            "nrr": {
                "name": "Net Revenue Retention",
                "endpoint": "/metrics/nrr",
                "required_fields": ["mrr_at_beginning", "expansion_revenue", "contraction_revenue", "churned_revenue"]
            }
        },
        "user_engagement_metrics": {
            "conversion_rate": {
                "name": "Conversion Rate",
                "endpoint": "/metrics/conversion-rate",
                "required_fields": ["number_of_conversions", "total_visitors_or_users"]
            },
            "traffic": {
                "name": "Website Traffic",
                "endpoint": "/metrics/traffic",
                "required_fields": ["organic_traffic", "paid_traffic"]
            },
            "dau_mau": {
                "name": "DAU/MAU Stickiness",
                "endpoint": "/metrics/dau-mau",
                "required_fields": ["daily_active_users", "monthly_active_users"]
            },
            "session_duration": {
                "name": "Average Session Duration",
                "endpoint": "/metrics/session-duration",
                "required_fields": ["total_session_duration_seconds", "total_number_of_sessions"]
            },
            "bounce_rate": {
                "name": "Bounce Rate",
                "endpoint": "/metrics/bounce-rate",
                "required_fields": ["number_of_non_engaged_sessions", "total_number_of_sessions"]
            }
        },
        "product_metrics": {
            "sessions_per_user": {
                "name": "Sessions Per User",
                "endpoint": "/metrics/sessions-per-user",
                "required_fields": ["total_number_of_sessions", "number_of_users"]
            },
            "user_actions": {
                "name": "User Actions Per Session",
                "endpoint": "/metrics/user-actions",
                "required_fields": ["total_actions", "total_sessions"]
            },
            "feature_adoption": {
                "name": "Feature Adoption Rate",
                "endpoint": "/metrics/feature-adoption",
                "required_fields": ["users_using_feature", "total_active_users"]
            }
        },
        "satisfaction_metrics": {
            "nps": {
                "name": "Net Promoter Score",
                "endpoint": "/metrics/nps",
                "required_fields": ["promoters", "passives", "detractors"]
            },
            "egr": {
                "name": "Earned Growth Rate",
                "endpoint": "/metrics/egr",
                "required_fields": ["mrr_at_beginning", "expansion_revenue", "upsell_revenue", "churn_revenue", "contraction_revenue", "new_customer_revenue_from_referrals", "total_new_customer_revenue"]
            },
            "csat": {
                "name": "Customer Satisfaction Score",
                "endpoint": "/metrics/csat",
                "required_fields": ["number_of_satisfied_responses", "total_number_of_responses"]
            },
            "osat": {
                "name": "Overall Satisfaction Score",
                "endpoint": "/metrics/osat",
                "required_fields": ["number_of_satisfied_responses", "total_number_of_responses"]
            },
            "ces": {
                "name": "Customer Effort Score",
                "endpoint": "/metrics/ces",
                "required_fields": ["sum_of_all_effort_scores", "total_number_of_respondents"]
            }
        },
        "additional_metrics": {
            "activation_rate": {
                "name": "Activation Rate",
                "endpoint": "/metrics/activation-rate",
                "required_fields": ["activated_users", "total_signups"]
            },
            "time_to_value": {
                "name": "Time to Value",
                "endpoint": "/metrics/time-to-value",
                "required_fields": ["total_time_to_value_hours", "number_of_users"]
            },
            "product_quality": {
                "name": "Defect Rate",
                "endpoint": "/metrics/product-quality",
                "required_fields": ["number_of_defects", "total_features_or_releases"]
            },
            "velocity": {
                "name": "Development Velocity",
                "endpoint": "/metrics/velocity",
                "required_fields": ["story_points_completed", "sprint_length_days"]
            }
        },
        "ml_predictions": {
            "predict": {
                "name": "Metric Prediction",
                "endpoint": "/predict/metric",
                "required_fields": ["metric_name", "historical_values", "periods_ahead"]
            },
            "analyze": {
                "name": "Pattern Analysis",
                "endpoint": "/analyze/pattern",
                "required_fields": ["metric_name", "historical_values"]
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
