import { useEffect } from "react";
import { Link } from "react-router-dom";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
} from "chart.js";
import { FiFileText, FiMessageCircle, FiUsers, FiZap, FiArrowRight } from "react-icons/fi";

import { useAuth } from "../../hooks/useAuth";
import useFetch from "../../hooks/useFetch";
import { DASHBOARD_STATS_EVENT, getDashboardStats, getNotes } from "../../services/api";
import Card from "../../components/Card";
import Loader from "../../components/Loader";
import NoteCard from "../../components/NoteCard";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler);

const progressData = {
  labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
  datasets: [
    {
      label: "Study hours",
      data: [1.5, 2, 1, 3, 2.5, 1.5, 2],
      borderColor: "#6366f1",
      backgroundColor: "rgba(99,102,241,0.15)",
      fill: true,
      tension: 0.4,
      pointBackgroundColor: "#4f46e5",
    },
  ],
};

const chartOptions = {
  responsive: true,
  plugins: { legend: { display: false } },
  scales: {
    y: { beginAtZero: true, grid: { color: "#f1f5f9" } },
    x: { grid: { display: false } },
  },
};

export default function Dashboard() {
  const { user } = useAuth();
  const { data: notes, loading } = useFetch(() => getNotes({ limit: 3 }), []);
  const { data: stats, loading: statsLoading, error: statsError, refetch: refetchStats } = useFetch(getDashboardStats, []);
  useEffect(() => {
    window.addEventListener(DASHBOARD_STATS_EVENT, refetchStats);
    window.addEventListener("focus", refetchStats);
    return () => { window.removeEventListener(DASHBOARD_STATS_EVENT, refetchStats); window.removeEventListener("focus", refetchStats); };
  }, [refetchStats]);
  const statValues = stats || { uploaded_notes: 0, ai_doubts: 0, quizzes_generated: 0, study_groups: 0 };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title">Welcome back, {user?.name?.split(" ")[0]} 👋</h1>
        <p className="text-slate-500 mt-1">Here's what's happening with your learning today.</p>
      </div>

      {/* Top stat cards */}
      {statsError && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">Could not load dashboard statistics: {statsError}</div>}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="flex items-center gap-4">
          <div className="w-11 h-11 rounded-xl bg-primary-50 text-primary-600 flex items-center justify-center">
            <FiFileText size={20} />
          </div>
          <div>
            <p className="text-xs text-slate-500">Notes Uploaded</p>
            <p className="text-xl font-bold text-slate-800">{statsLoading ? "…" : statValues.uploaded_notes}</p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="w-11 h-11 rounded-xl bg-accent-500/10 text-accent-600 flex items-center justify-center">
            <FiMessageCircle size={20} />
          </div>
          <div>
            <p className="text-xs text-slate-500">AI Doubts Solved</p>
            <p className="text-xl font-bold text-slate-800">{statsLoading ? "…" : statValues.ai_doubts}</p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="w-11 h-11 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
            <FiUsers size={20} />
          </div>
          <div>
            <p className="text-xs text-slate-500">Study Groups</p>
            <p className="text-xl font-bold text-slate-800">{statsLoading ? "…" : statValues.study_groups}</p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="w-11 h-11 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <FiZap size={20} />
          </div>
          <div>
            <p className="text-xs text-slate-500">Quizzes Generated</p>
            <p className="text-xl font-bold text-slate-800">{statsLoading ? "…" : statValues.quizzes_generated}</p>
          </div>
        </Card>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Progress chart */}
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-800">Learning Progress</h3>
            <span className="text-xs text-slate-400">This week</span>
          </div>
          <Line data={progressData} options={chartOptions} />
        </Card>

        {/* AI assistant card */}
        <Card className="bg-brand-gradient text-white flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-lg mb-2">Ask your AI Tutor</h3>
            <p className="text-white/85 text-sm mb-6">
              Stuck on a problem? Get instant, clear explanations from your AI study assistant.
            </p>
          </div>
          <Link
            to="/ai/chat"
            className="inline-flex items-center gap-2 bg-white text-primary-700 font-semibold px-4 py-2.5 rounded-xl w-fit hover:bg-slate-100"
          >
            Start Chatting <FiArrowRight />
          </Link>
        </Card>
      </div>

      {/* Recent notes */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-slate-800 text-lg">Recent Notes</h3>
          <Link to="/notes" className="text-sm font-semibold text-primary-600 hover:underline">
            View all
          </Link>
        </div>
        {loading ? (
          <Loader />
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {notes?.map((note) => (
              <NoteCard key={note.id} note={note} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
