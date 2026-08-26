import React, { useState, useEffect, useCallback } from 'react';
import { Line, Doughnut } from 'react-chartjs-2';
import { fetchWithToken } from "../api";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    ArcElement, // Needed for Doughnut chart
} from 'chart.js';
import { DatabaseZap, Cpu, Check, FileText } from 'lucide-react';

// --- CHART REGISTRATION ---
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    ArcElement
);

// --- STATIC COLORS (Defined here for chart consistency) ---
const CHART_COLORS = {
    RED: '#ff3b3b',
    RED_LIGHT: 'rgba(255, 59, 59, 0.1)',
    BLUE: '#17a2b8',
    GREEN: '#28a745',
    GRAY: '#6c757d',
    LIGHT_GRAY_GRID: '#e0e0e0',
    DARK_TEXT: '#1e1e1e',
    WHITE: '#ffffff',
    TOOLTIP_BG: '#f5f5f5',
};

// --- Helper function for common chart options ---
const getChartOptions = (title) => ({
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
        mode: 'index',
        intersect: false,
    },
    plugins: {
        legend: { display: false },
        title: {
            display: true,
            text: title,
            font: { size: 16, weight: '600', family: 'Inter, sans-serif' },
            color: CHART_COLORS.DARK_TEXT,
            padding: { top: 10, bottom: 20 }
        },
        tooltip: {
            backgroundColor: CHART_COLORS.TOOLTIP_BG,
            borderColor: CHART_COLORS.LIGHT_GRAY_GRID,
            borderWidth: 1,
            titleColor: CHART_COLORS.RED,
            bodyColor: CHART_COLORS.DARK_TEXT,
            titleFont: { size: 14, weight: 'bold' },
            bodyFont: { size: 12 },
            boxPadding: 4,
        }
    },
    scales: {
        y: {
            beginAtZero: true,
            grid: {
                color: CHART_COLORS.LIGHT_GRAY_GRID,
                borderDash: [5, 5],
                drawBorder: false,
            },
            borderColor: CHART_COLORS.LIGHT_GRAY_GRID,
            title: { display: true, text: 'Tokens Consumed', color: CHART_COLORS.GRAY },
            ticks: {
                color: CHART_COLORS.DARK_TEXT,
                padding: 10,
                maxRotation: 0
            },
        },
        x: {
            borderColor: CHART_COLORS.LIGHT_GRAY_GRID,
            grid: {
                display: false,
                drawBorder: false,
            },
            title: { display: true, text: 'Time Period', color: CHART_COLORS.GRAY },
            ticks: {
                color: CHART_COLORS.DARK_TEXT,
                padding: 10
            },
        },
    },
});

// --- RENDER 1: Daily Token Usage (Monthly Trend) ---
const MonthlyUsageChart = ({ data }) => {
    const chartData = {
        labels: data.map(d => d.date.substring(5)), // Show MM-DD format
        datasets: [{
            label: 'Daily Tokens',
            data: data.map(d => d.tokens),
            fill: 'origin',
            backgroundColor: CHART_COLORS.RED_LIGHT,
            borderColor: CHART_COLORS.RED,
            borderWidth: 3,
            tension: 0.4,
            pointBackgroundColor: CHART_COLORS.RED,
            pointBorderColor: CHART_COLORS.WHITE,
            pointBorderWidth: 2,
            pointRadius: 5,
            pointHoverRadius: 7,
            spanGaps: true,
        }],
    };
    return (
        <div style={{ height: '350px', padding: '20px' }}>
            <Line data={chartData} options={getChartOptions("Last 30 Days Daily Usage")} />
        </div>
    );
};

// --- RENDER 2: Hourly Token Usage (Today) ---
const HourlyUsageChart = ({ data, dailyTokens }) => {
    // Generate labels for 0h to 23h
    const hourlyLabels = Array.from({ length: 24 }, (_, i) => `${i}:00`);
    
    // Merge fetched data into the 24-hour structure
    const hourlyDataMap = new Map(data.map(d => [d.hour, d.tokens]));
    const dataPoints = hourlyLabels.map((_, index) => hourlyDataMap.get(index) || 0);

    const chartData = {
        labels: hourlyLabels,
        datasets: [{
            label: `Today's Usage (${dailyTokens.toLocaleString()} Total)`,
            data: dataPoints,
            backgroundColor: CHART_COLORS.BLUE,
            borderColor: CHART_COLORS.BLUE,
            borderWidth: 2,
            tension: 0.2,
            pointBackgroundColor: CHART_COLORS.BLUE,
            pointBorderColor: CHART_COLORS.WHITE,
            pointBorderWidth: 1,
            pointRadius: 3,
            pointHoverRadius: 5,
            spanGaps: false,
        }],
    };
    
    const options = getChartOptions("Today's Hourly Usage");
    options.scales.x.title.text = 'Time of Day (24h)';
    
    return (
        <div style={{ height: '350px', padding: '20px' }}>
            <Line data={chartData} options={options} />
        </div>
    );
};


// --- RENDER 3: Overall Token Breakdown (Doughnut) ---
const TotalUsageChart = ({ totalTokens, monthlyTokens, lastMonthTokens, dailyTokens }) => {
    // Calculate tokens older than the current month
    const currentMonthUsage = monthlyTokens; 
    const otherTokens = totalTokens - currentMonthUsage; 
    
    // We only show current month, last month, and older. 
    // This assumes dailyTokens is a subset of monthlyTokens.
    const thisMonthExclToday = monthlyTokens - dailyTokens;

    const chartData = {
        labels: ['Today', 'This Month (Excl. Today)', 'Last Month', 'Older Usage'],
        datasets: [{
            data: [
                dailyTokens,
                thisMonthExclToday > 0 ? thisMonthExclToday : 0, // Ensure non-negative
                lastMonthTokens,
                otherTokens > 0 ? otherTokens : 0
            ],
            backgroundColor: [
                CHART_COLORS.RED, 
                CHART_COLORS.BLUE, 
                CHART_COLORS.GREEN, 
                CHART_COLORS.GRAY
            ],
            hoverOffset: 15
        }]
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    color: CHART_COLORS.DARK_TEXT,
                }
            },
            title: {
                display: true,
                text: `All-Time Token Breakdown (${totalTokens.toLocaleString()})`,
                font: { size: 16, weight: '600', family: 'Inter, sans-serif' },
                color: CHART_COLORS.DARK_TEXT,
            },
        },
    };

    return (
        <div style={{ height: '350px', padding: '20px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ height: '300px', width: '300px' }}>
                <Doughnut data={chartData} options={options} />
            </div>
        </div>
    );
};


// --- MAIN Component (Handles Polling) ---
const TokenUsageCharts = ({ isActive }) => {
    // Polling interval remains 10 seconds
    const POLLING_INTERVAL = 10000; 

    const [tokenStats, setTokenStats] = useState({
        totalTokens: 0,
        dailyTokens: 0,
        monthlyTokens: 0,
        lastMonthTokens: 0,
        dailyTrendData: [],
        hourlyTrendData: [],
    });
    const [isLoading, setIsLoading] = useState(true);

    const fetchUsage = useCallback(async () => {
        try {
            const response = await fetchWithToken('/profile/usage');
            
            // Check if we are still fetching before parsing JSON to prevent runtime errors
            if (response.ok) {
                const data = await response.json();
                setTokenStats({
                    totalTokens: data.total_tokens || 0,
                    dailyTokens: data.daily_tokens || 0,
                    monthlyTokens: data.monthly_tokens || 0,
                    lastMonthTokens: data.last_month_tokens || 0,
                    dailyTrendData: Array.isArray(data.daily_trend_data) ? data.daily_trend_data : [],
                    hourlyTrendData: Array.isArray(data.hourly_trend_data) ? data.hourly_trend_data : [],
                });
            } else {
                // Handle non-OK response errors
                const errorData = await response.json();
                console.error("Failed to fetch usage:", errorData.error);
            }
        } catch (error) {
            console.error("Network error fetching usage:", error);
        } finally {
            setIsLoading(false);
        }
    }, []);

    // --- EFFECT: Real-Time Polling ---
    useEffect(() => {
        let intervalId = null;

        if (isActive) {
            // 1. Fetch immediately when the tab becomes active
            fetchUsage();

            // 2. Set up the polling interval
            intervalId = setInterval(fetchUsage, POLLING_INTERVAL);
        }

        // Cleanup: Clear interval when component unmounts or tab becomes inactive
        return () => {
            if (intervalId) {
                clearInterval(intervalId);
            }
        };
    }, [isActive, fetchUsage]);


    if (isLoading) {
        return (
            <div className="section-content" style={{ textAlign: 'center', minHeight: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div className="loader"></div>
                <p style={{marginLeft: '1rem', color: CHART_COLORS.GRAY}}>Loading real-time usage data...</p>
            </div>
        );
    }
    
    const { totalTokens, dailyTokens, monthlyTokens, lastMonthTokens, dailyTrendData, hourlyTrendData } = tokenStats;

    return (
        <div className="section-content" style={{ padding: '2rem' }}>
            <h3 style={{ marginTop: 0, marginBottom: '2rem', borderBottom: '1px solid var(--scroll-hover)', paddingBottom: '0.5rem' }}>Token Usage Breakdown (Updates Every 10s)</h3>
            
            {/* Detailed Token Stats Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '3rem' }}>
                <div className="stat-card" style={{padding: '1rem', alignItems: 'flex-start'}}>
                    <h4 style={{margin: '0', fontSize: '1.5rem', color: CHART_COLORS.RED}}>{dailyTokens.toLocaleString()}</h4>
                    <p style={{margin: '0', color: CHART_COLORS.GRAY, fontWeight: 500}}>Tokens Used Today</p>
                </div>
                <div className="stat-card" style={{padding: '1rem', alignItems: 'flex-start'}}>
                    <h4 style={{margin: '0', fontSize: '1.5rem', color: CHART_COLORS.BLUE}}>{monthlyTokens.toLocaleString()}</h4>
                    <p style={{margin: '0', color: CHART_COLORS.GRAY, fontWeight: 500}}>Tokens Used This Month</p>
                </div>
                <div className="stat-card" style={{padding: '1rem', alignItems: 'flex-start'}}>
                    <h4 style={{margin: '0', fontSize: '1.5rem', color: CHART_COLORS.GREEN}}>{lastMonthTokens.toLocaleString()}</h4>
                    <p style={{margin: '0', color: CHART_COLORS.GRAY, fontWeight: 500}}>Tokens Used Last Month</p>
                </div>
                 <div className="stat-card" style={{padding: '1rem', alignItems: 'flex-start'}}>
                    <h4 style={{margin: '0', fontSize: '1.5rem', color: CHART_COLORS.GRAY}}>{totalTokens.toLocaleString()}</h4>
                    <p style={{margin: '0', color: CHART_COLORS.GRAY, fontWeight: 500}}>All-Time Usage</p>
                </div>
            </div>

            {/* --- Chart Grid --- */}
            <div className="chart-grid-container" style={{
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', 
                gap: '2rem'
            }}>
                <div style={{ 
                    backgroundColor: CHART_COLORS.WHITE, 
                    borderRadius: '12px', 
                    border: '1px solid var(--scroll-hover)',
                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)'
                }}>
                    <TotalUsageChart 
                        totalTokens={totalTokens} 
                        monthlyTokens={monthlyTokens} 
                        lastMonthTokens={lastMonthTokens} 
                        dailyTokens={dailyTokens}
                    />
                </div>
                
                <div style={{ 
                    backgroundColor: CHART_COLORS.WHITE, 
                    borderRadius: '12px', 
                    border: '1px solid var(--scroll-hover)',
                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)'
                }}>
                    <MonthlyUsageChart data={dailyTrendData} />
                </div>

                <div style={{ 
                    backgroundColor: CHART_COLORS.WHITE, 
                    borderRadius: '12px', 
                    border: '1px solid var(--scroll-hover)',
                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)',
                    gridColumn: '1 / -1' // Span the full width on larger screens
                }}>
                    <HourlyUsageChart data={hourlyTrendData} dailyTokens={dailyTokens} />
                </div>
            </div>
        </div>
    );
};

export default TokenUsageCharts;