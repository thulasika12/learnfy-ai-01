import { useState } from "react";
import { FiSearch } from "react-icons/fi";
import toast from "react-hot-toast";

import useFetch from "../../hooks/useFetch";
import { getNotes, toggleLike, toggleBookmark } from "../../services/api";
import NoteCard from "../../components/NoteCard";
import { SkeletonGrid } from "../../components/Motion";
import AcademicContextFields from "../../components/subjects/AcademicContextFields";
import { useAcademicDefaults } from "../../hooks/useAcademicDefaults";

export default function NotesList() {
  const [search, setSearch] = useState("");
  const [academic, setAcademic] = useAcademicDefaults();

  const { data: notes, loading, error, setData } = useFetch(
    () => getNotes({ search: search || undefined, subject: academic.subject || undefined, grade: academic.grade || undefined, medium: academic.medium || undefined }),
    [search, academic.subject, academic.grade, academic.medium]
  );

  const handleLike = async (id) => {
    try {
      const res = await toggleLike(id);
      setData((prev) =>
        prev.map((n) =>
          n.id === id
            ? { ...n, is_liked: res.data.liked, likes_count: n.likes_count + (res.data.liked ? 1 : -1) }
            : n
        )
      );
    } catch {
      toast.error("Please log in to like notes");
    }
  };

  const handleBookmark = async (id) => {
    try {
      const res = await toggleBookmark(id);
      setData((prev) => prev.map((n) => (n.id === id ? { ...n, is_bookmarked: res.data.bookmarked } : n)));
      toast.success(res.data.bookmarked ? "Bookmarked" : "Bookmark removed");
    } catch {
      toast.error("Please log in to bookmark notes");
    }
  };

  return (
    <div className="relative z-0 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h1 className="page-title">Explore Notes</h1>
      </div>

      <div className="relative z-10 flex flex-col md:flex-row gap-3">
        <div className="relative flex-1">
          <FiSearch className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            className="input-field pl-10"
            placeholder="Search notes by title or description..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>
      <div className="relative z-10"><AcademicContextFields value={academic} onChange={setAcademic} requireSubject={false} className="grid gap-3 md:grid-cols-3" /></div>

      {error ? <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">{error}</div> : loading ? (
        <SkeletonGrid />
      ) : notes?.length ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {notes.map((note) => (
            <NoteCard key={note.id} note={note} onLike={handleLike} onBookmark={handleBookmark} />
          ))}
        </div>
      ) : (
        <div className="text-center text-slate-500 py-16">No notes found. Try a different search.</div>
      )}
    </div>
  );
}
