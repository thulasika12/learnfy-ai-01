import { useState } from "react";
import toast from "react-hot-toast";
import { FiCalendar, FiPlus, FiX, FiCheckSquare } from "react-icons/fi";

import { aiStudyPlan } from "../../services/api";
import Card from "../../components/Card";
import Button from "../../components/Button";
import Loader from "../../components/Loader";
import AcademicContextFields from "../../components/subjects/AcademicContextFields";
import { useAcademicDefaults } from "../../hooks/useAcademicDefaults";
import { usePreferences } from "../../hooks/usePreferences";

export default function StudyPlanner() {
  const [subjects, setSubjects] = useState([]);
  const [academic, setAcademic] = useAcademicDefaults();
  const [subjectInput, setSubjectInput] = useState("");
  const [hoursPerDay, setHoursPerDay] = useState(2);
  const [days, setDays] = useState(7);
  const [goal, setGoal] = useState("");
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const { language } = usePreferences();

  const addSubject = () => {
    const s = (academic.subject || subjectInput).trim();
    if (!s) return;
    if (subjects.includes(s)) return toast.error("Subject already added");
    setSubjects((prev) => [...prev, s]);
    setSubjectInput("");
    setAcademic((current) => ({ ...current, subject:"", subjectId:null }));
  };

  const removeSubject = (s) => setSubjects((prev) => prev.filter((x) => x !== s));

  const handleGenerate = async (ev) => {
    ev.preventDefault();
    if (subjects.length === 0) return toast.error("Add at least one subject");
    setLoading(true);
    setPlan(null);
    try {
      const res = await aiStudyPlan({ subjects, hours_per_day: hoursPerDay, days, goal: goal || undefined, grade: academic.grade || undefined, medium: academic.medium || undefined, response_language: language });
      setPlan(res.data.plan);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not generate a study plan");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="page-title flex items-center gap-2">
          <FiCalendar className="text-primary-600" /> AI Study Planner
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Build a personalized day-by-day schedule based on your subjects and available time.
        </p>
      </div>

      <Card>
        <form onSubmit={handleGenerate} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-600 mb-1 block">Subjects</label>
            <div className="flex gap-2">
              <div className="flex-1"><AcademicContextFields value={academic} onChange={setAcademic} /></div>
              <button type="button" onClick={addSubject} className="btn-secondary px-4">
                <FiPlus />
              </button>
            </div>
            <div className="flex flex-wrap gap-2 mt-3">
              {subjects.map((s) => (
                <span
                  key={s}
                  className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-full bg-primary-50 text-primary-700"
                >
                  {s}
                  <button type="button" onClick={() => removeSubject(s)}>
                    <FiX size={12} />
                  </button>
                </span>
              ))}
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-slate-600 mb-1 block">Hours per day</label>
              <input
                type="number"
                min={0.5}
                max={16}
                step={0.5}
                className="input-field"
                value={hoursPerDay}
                onChange={(e) => setHoursPerDay(Number(e.target.value))}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-600 mb-1 block">Number of days</label>
              <input
                type="number"
                min={1}
                max={90}
                className="input-field"
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-600 mb-1 block">Goal (optional)</label>
            <input
              className="input-field"
              placeholder="e.g. Prepare for mid-term exams"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
            />
          </div>

          <Button type="submit" className="w-full" loading={loading}>
            Generate Study Plan
          </Button>
        </form>
      </Card>

      {loading && <Loader label="Building your study plan..." />}

      {plan && (
        <div className="space-y-3">
          {plan.map((day) => (
            <Card key={day.day}>
              <h3 className="font-bold text-slate-800 mb-3">Day {day.day}</h3>
              <ul className="space-y-2">
                {day.tasks.map((task, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                    <FiCheckSquare className="text-primary-500 mt-0.5 shrink-0" />
                    {task}
                  </li>
                ))}
              </ul>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
