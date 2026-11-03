import React, { useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  LogarithmicScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import { TrendingDown, PieChart, BarChart3, Info, AlertCircle, ShieldAlert } from 'lucide-react';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  LogarithmicScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function PerformanceDashboard({ result }) {
  const [useLogScale, setUseLogScale] = useState(false);
  const [activeChartTab, setActiveChartTab] = useState('scaling');

  if (!result || result.status !== 'success') {
    return (
      <div className="bg-white rounded-2xl shadow-xs border border-[#E5E9E5] p-10 text-center flex flex-col items-center justify-center min-h-[400px]">
        <div className="w-14 h-14 rounded-2xl bg-[#F3F5F2] text-[#174F4A] flex items-center justify-center mb-3 border border-[#E5E9E5]">
          <BarChart3 className="w-7 h-7 text-[#174F4A]" />
        </div>
        <h3 className="text-lg font-bold text-[#202824]">No Benchmark Scaling Data Available</h3>
        <p className="text-xs text-[#68736D] mt-1 max-w-sm">
          Run analysis on valid code to generate theoretical complexity scaling curves and AST metric visualizations.
        </p>
      </div>
    );
  }

  const benchmark = result.benchmark_model;
  const patterns = result.patterns || [];
  const astMetrics = result.ast_metrics;

  // 1. Data for Scaling Curve (Line Chart)
  const scalingData = {
    labels: benchmark?.data_points?.map((p) => `N=${p.input_size}`) || [],
    datasets: [
      {
        label: benchmark?.baseline_label || 'Current Implementation',
        data: benchmark?.data_points?.map((p) => p.baseline_ops) || [],
        borderColor: '#D64545',
        backgroundColor: 'rgba(214, 69, 69, 0.08)',
        fill: true,
        tension: 0.35,
        pointRadius: 4,
        pointHoverRadius: 6,
        borderWidth: 2,
      },
      {
        label: benchmark?.optimized_label || 'Optimized Suggestion',
        data: benchmark?.data_points?.map((p) => p.optimized_ops) || [],
        borderColor: '#174F4A',
        backgroundColor: 'rgba(23, 79, 74, 0.08)',
        fill: true,
        tension: 0.35,
        pointRadius: 4,
        pointHoverRadius: 6,
        borderWidth: 2.5,
      },
    ],
  };

  const scalingOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          font: { size: 12, family: 'sans-serif', weight: '600' },
          color: '#202824',
        },
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const val = context.parsed.y;
            return ` ${context.dataset.label}: ${val.toLocaleString()} theoretical operations`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: { color: '#E5E9E5' },
        ticks: { color: '#68736D', font: { size: 11 } },
      },
      y: {
        type: useLogScale ? 'logarithmic' : 'linear',
        grid: { color: '#E5E9E5' },
        ticks: {
          color: '#68736D',
          font: { size: 11 },
          callback: (value) => value.toLocaleString(),
        },
        title: {
          display: true,
          text: useLogScale ? 'Theoretical Operations (Log Scale)' : 'Theoretical Operations (Linear)',
          color: '#68736D',
          font: { size: 11, weight: '600' },
        },
      },
    },
  };

  // 2. Data for Category Distribution (Doughnut Chart)
  const categoryCounts = {
    complexity: patterns.filter((p) => p.category === 'complexity').length,
    performance: patterns.filter((p) => p.category === 'performance').length,
    idiom: patterns.filter((p) => p.category === 'idiom').length,
    best_practice: patterns.filter((p) => p.category === 'best_practice').length,
  };

  const doughnutData = {
    labels: ['Complexity Bottlenecks', 'Performance / Memory', 'Idioms', 'Best Practices'],
    datasets: [
      {
        data: [
          categoryCounts.complexity,
          categoryCounts.performance,
          categoryCounts.idiom,
          categoryCounts.best_practice,
        ],
        backgroundColor: ['#D64545', '#D99A28', '#3979B9', '#21865A'],
        borderWidth: 2,
        borderColor: '#FFFFFF',
      },
    ],
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
        labels: { font: { size: 12, weight: '600' }, color: '#202824' },
      },
    },
  };

  // 3. Data for AST Metrics (Bar Chart)
  const barData = {
    labels: ['Nesting Depth', 'Loop Blocks', 'Branch Blocks', 'Functions', 'Classes'],
    datasets: [
      {
        label: 'AST Count',
        data: [
          astMetrics?.max_nesting_depth || 0,
          astMetrics?.loops_count || 0,
          astMetrics?.branches_count || 0,
          astMetrics?.functions_count || 0,
          astMetrics?.classes_count || 0,
        ],
        backgroundColor: '#174F4A',
        borderRadius: 6,
      },
    ],
  };

  const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { stepSize: 1, color: '#68736D' },
        grid: { color: '#E5E9E5' },
      },
      x: {
        ticks: { color: '#68736D' },
        grid: { display: false },
      },
    },
  };

  return (
    <div className="bg-white rounded-2xl shadow-xs border border-[#E5E9E5] overflow-hidden space-y-4 transition-all">
      {/* Dashboard Sub-navigation */}
      <div className="bg-[#F3F5F2] px-4 py-3 border-b border-[#E5E9E5] flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-1 sm:space-x-2">
          <button
            onClick={() => setActiveChartTab('scaling')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center space-x-1.5 cursor-pointer ${
              activeChartTab === 'scaling'
                ? 'bg-[#174F4A] text-white font-bold shadow-xs'
                : 'text-[#68736D] hover:text-[#202824] bg-white border border-[#E5E9E5]'
            }`}
          >
            <TrendingDown className="w-3.5 h-3.5" />
            <span>Algorithmic Scaling Curve</span>
          </button>

          <button
            onClick={() => setActiveChartTab('distribution')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center space-x-1.5 cursor-pointer ${
              activeChartTab === 'distribution'
                ? 'bg-[#174F4A] text-white font-bold shadow-xs'
                : 'text-[#68736D] hover:text-[#202824] bg-white border border-[#E5E9E5]'
            }`}
          >
            <PieChart className="w-3.5 h-3.5" />
            <span>Issue Breakdown</span>
          </button>

          <button
            onClick={() => setActiveChartTab('ast')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center space-x-1.5 cursor-pointer ${
              activeChartTab === 'ast'
                ? 'bg-[#174F4A] text-white font-bold shadow-xs'
                : 'text-[#68736D] hover:text-[#202824] bg-white border border-[#E5E9E5]'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>AST Structure</span>
          </button>
        </div>

        {activeChartTab === 'scaling' && (
          <div className="flex items-center space-x-2 text-xs">
            <span className="text-[#68736D] font-medium">Y-Axis Scale:</span>
            <button
              onClick={() => setUseLogScale(!useLogScale)}
              className={`px-2.5 py-1 rounded-lg text-xs font-bold border transition-all cursor-pointer ${
                useLogScale
                  ? 'bg-[#174F4A] text-white border-[#174F4A]'
                  : 'bg-white text-[#202824] border-[#E5E9E5] hover:bg-[#F3F5F2]'
              }`}
            >
              {useLogScale ? 'Logarithmic (Active)' : 'Linear'}
            </button>
          </div>
        )}
      </div>

      {/* Chart Canvas Area */}
      <div className="p-6">
        {activeChartTab === 'scaling' && (
          <div className="space-y-4">
            <div className="h-[340px] w-full">
              <Line data={scalingData} options={scalingOptions} />
            </div>

            {/* Mandatory Testing & Simulation Disclaimer */}
            <div className="p-3 bg-[#FEFCE8] rounded-xl border border-[#FEF08A] text-xs text-[#202824] flex items-start space-x-2">
              <ShieldAlert className="w-4 h-4 text-[#D99A28] shrink-0 mt-0.5" />
              <div className="leading-relaxed">
                <strong className="text-[#D99A28]">Honesty & Testing Notice:</strong> {benchmark?.disclaimer} Actual empirical speedups must be
                measured in a controlled testing environment using tools like <code className="text-[#174F4A] bg-white px-1.5 py-0.5 rounded border border-[#E5E9E5] font-mono">pytest-benchmark</code> or{' '}
                <code className="text-[#174F4A] bg-white px-1.5 py-0.5 rounded border border-[#E5E9E5] font-mono">timeit</code>, as memory locality, branch prediction, and dataset distribution can affect real-world execution.
              </div>
            </div>
          </div>
        )}

        {activeChartTab === 'distribution' && (
          <div className="space-y-4">
            <div className="h-[300px] w-full flex items-center justify-center">
              {patterns.length > 0 ? (
                <Doughnut data={doughnutData} options={doughnutOptions} />
              ) : (
                <div className="text-center text-xs text-[#68736D]">
                  Zero anti-patterns detected in current codebase.
                </div>
              )}
            </div>
            <p className="text-xs text-center text-[#68736D]">
              Categorical breakdown of static rule triggers across complexity, memory, and idiom domains.
            </p>
          </div>
        )}

        {activeChartTab === 'ast' && (
          <div className="space-y-4">
            <div className="h-[300px] w-full">
              <Bar data={barData} options={barOptions} />
            </div>
            <p className="text-xs text-center text-[#68736D]">
              Structural complexity components extracted directly from AST node hierarchy.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
