import { Bar, Doughnut } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
} from "chart.js";
import Card from "../../components/Card";
import { useState } from "react";
import StreamSelect from "../../components/subjects/StreamSelect";
import SubjectSelect from "../../components/subjects/SubjectSelect";

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend);

const subjectHours = {
  labels: ["Math", "Physics", "Chemistry", "Biology", "English"],
  datasets: [
    {
      label: "Hours studied",
      data: [12, 9, 7, 5, 4],
      backgroundColor: ["#6366f1", "#0ea5e9", "#a78bfa", "#34d399", "#fbbf24"],
      borderRadius: 8,
    },
  ],
};

const completionData = {
  labels: ["Completed", "In Progress", "Not Started"],
  datasets: [
    {
      data: [58, 27, 15],
      backgroundColor: ["#4f46e5", "#0ea5e9", "#e2e8f0"],
      borderWidth: 0,
    },
  ],
};

export default function Progress() {
  const [stream, setStream] = useState("");
  const [subject, setSubject] = useState("");
  return (
    <div className="space-y-6">
      <h1 className="page-title">My Learning Progress</h1>
      <div className="grid gap-3 sm:grid-cols-2"><StreamSelect value={stream} includeAll onChange={(value) => { setStream(value); setSubject(""); }} /><SubjectSelect stream={stream} value={subject} includeAll onChange={setSubject} /></div>

      <div className="grid lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <h3 className="font-bold text-slate-800 mb-4">Hours by Subject</h3>
          <Bar
            data={subjectHours}
            options={{
              plugins: { legend: { display: false } },
              scales: { y: { grid: { color: "#f1f5f9" } }, x: { grid: { display: false } } },
            }}
          />
        </Card>

        <Card>
          <h3 className="font-bold text-slate-800 mb-4">Overall Completion</h3>
          <Doughnut data={completionData} options={{ plugins: { legend: { position: "bottom" } } }} />
        </Card>
      </div>

      <Card>
        <h3 className="font-bold text-slate-800 mb-4">Upcoming Tasks</h3>
        <ul className="divide-y divide-slate-100">
          {[
            { task: "Finish Physics Chapter 5 notes", due: "Tomorrow" },
            { task: "Attempt AI-generated Chemistry quiz", due: "In 2 days" },
            { task: "Group discussion: DSA problem set", due: "Friday" },
          ].map((t) => (
            <li key={t.task} className="flex items-center justify-between py-3 text-sm">
              <span className="text-slate-700 font-medium">{t.task}</span>
              <span className="text-slate-400">{t.due}</span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
