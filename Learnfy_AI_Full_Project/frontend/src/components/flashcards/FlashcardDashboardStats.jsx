import { FiAward, FiLayers, FiTarget, FiTrendingUp } from "react-icons/fi";

export default function FlashcardDashboardStats({ stats }) {
  const items = [{ label: "Saved sets", value: stats?.total_sets || 0, icon: FiLayers }, { label: "Cards studied", value: stats?.total_cards_studied || 0, icon: FiTarget }, { label: "Average score", value: `${Math.round(stats?.average_score || 0)}%`, icon: FiTrendingUp }, { label: "Revision streak", value: `${stats?.revision_streak || 0} days`, icon: FiAward }];
  return <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{items.map((item) => <div key={item.label} className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900"><item.icon className="text-primary-600" /><p className="mt-3 text-2xl font-black text-slate-900 dark:text-white">{item.value}</p><p className="text-xs text-slate-500">{item.label}</p></div>)}</div>;
}
