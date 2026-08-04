import { FiUpload, FiFileText, FiMessageCircle, FiUsers } from "react-icons/fi";

import { useAuth } from "../../hooks/useAuth";
import useFetch from "../../hooks/useFetch";
import { getNotes } from "../../services/api";
import Card from "../../components/Card";
import Loader from "../../components/Loader";
import NoteCard from "../../components/NoteCard";
import { Link } from "react-router-dom";

export default function TeacherDashboard() {
  const { user } = useAuth();
  const { data: notes, loading } = useFetch(() => getNotes({ limit: 6 }), []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title">Welcome, {user?.name?.split(" ")[0]} 👋</h1>
        <p className="text-slate-500 mt-1">
          {user?.is_verified_teacher ? "Verified Teacher" : "Teacher account — pending verification by admin"}
        </p>
      </div>

      <div className="grid sm:grid-cols-3 gap-4">
        <Card className="flex items-center gap-4">
          <div className="w-11 h-11 rounded-xl bg-primary-50 text-primary-600 flex items-center justify-center">
            <FiFileText size={20} />
          </div>
          <div>
            <p className="text-xs text-slate-500">Materials Uploaded</p>
            <p className="text-xl font-bold text-slate-800">9</p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="w-11 h-11 rounded-xl bg-accent-500/10 text-accent-600 flex items-center justify-center">
            <FiMessageCircle size={20} />
          </div>
          <div>
            <p className="text-xs text-slate-500">Doubts Answered</p>
            <p className="text-xl font-bold text-slate-800">21</p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="w-11 h-11 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
            <FiUsers size={20} />
          </div>
          <div>
            <p className="text-xs text-slate-500">Students Reached</p>
            <p className="text-xl font-bold text-slate-800">180</p>
          </div>
        </Card>
      </div>

      <Card className="bg-brand-gradient text-white flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h3 className="font-bold text-lg">Share study material with your students</h3>
          <p className="text-white/85 text-sm mt-1">Upload notes, PDFs, and resources for your classes.</p>
        </div>
        <Link
          to="/notes/upload"
          className="bg-white text-primary-700 font-semibold px-4 py-2.5 rounded-xl flex items-center gap-2 hover:bg-slate-100 shrink-0"
        >
          <FiUpload /> Upload Material
        </Link>
      </Card>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-slate-800 text-lg">Recent Notes & Resources</h3>
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
