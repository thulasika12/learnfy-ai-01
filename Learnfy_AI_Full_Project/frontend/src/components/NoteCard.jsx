import { FiHeart, FiBookmark, FiDownload, FiMessageSquare } from "react-icons/fi";
import { Link } from "react-router-dom";
import Card from "./Card";

export default function NoteCard({ note, onLike, onBookmark }) {
  return (
    <Card className="flex flex-col gap-3">
      <div className="flex items-start justify-between">
        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-primary-50 text-primary-700">
          {[note.grade, note.subject, note.medium?.toUpperCase()].filter(Boolean).join(" · ")}
        </span>
        <span className="text-xs text-slate-400">
          {new Date(note.created_at).toLocaleDateString()}
        </span>
      </div>

      <Link to={`/notes/${note.id}`}>
        <h3 className="font-bold text-slate-800 hover:text-primary-600 line-clamp-2">{note.title}</h3>
      </Link>
      <p className="text-sm text-slate-500 line-clamp-3">{note.description}</p>

      <div className="flex items-center gap-2 mt-1">
        <img
          src={note.author?.profile_image || `https://api.dicebear.com/7.x/initials/svg?seed=${note.author?.name}`}
          className="w-6 h-6 rounded-full object-cover"
          alt="author"
        />
        <span className="text-xs text-slate-500 font-medium">{note.author?.name || "Unknown"}</span>
      </div>

      <div className="flex items-center justify-between pt-3 border-t border-slate-100 mt-1">
        <div className="flex items-center gap-4 text-slate-500 text-sm">
          <button
            onClick={() => onLike?.(note.id)}
            className={`flex items-center gap-1 hover:text-red-500 transition-colors ${
              note.is_liked ? "text-red-500" : ""
            }`}
          >
            <FiHeart className={note.is_liked ? "fill-current" : ""} /> {note.likes_count || 0}
          </button>
          <Link to={`/notes/${note.id}`} className="flex items-center gap-1 hover:text-primary-600">
            <FiMessageSquare /> {note.comments_count || 0}
          </Link>
          <button
            onClick={() => onBookmark?.(note.id)}
            className={`hover:text-primary-600 transition-colors ${
              note.is_bookmarked ? "text-primary-600" : ""
            }`}
          >
            <FiBookmark className={note.is_bookmarked ? "fill-current" : ""} />
          </button>
        </div>
        {note.file_url && (
          <a
            href={`${import.meta.env.VITE_API_URL || "http://localhost:8000"}${note.file_url}`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1 text-sm font-semibold text-primary-600 hover:underline"
          >
            <FiDownload /> Download
          </a>
        )}
      </div>
    </Card>
  );
}
