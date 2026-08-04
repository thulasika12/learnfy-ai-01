import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import toast from "react-hot-toast";
import { FiHeart, FiBookmark, FiDownload, FiEdit2, FiTrash2, FiSend, FiLayers } from "react-icons/fi";

import { getNote, getComments, postComment, toggleLike, toggleBookmark, deleteNote } from "../../services/api";
import { useAuth } from "../../hooks/useAuth";
import Card from "../../components/Card";
import Loader from "../../components/Loader";
import Button from "../../components/Button";

export default function NoteDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [note, setNote] = useState(null);
  const [comments, setComments] = useState([]);
  const [commentText, setCommentText] = useState("");
  const [loading, setLoading] = useState(true);
  const [posting, setPosting] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [noteRes, commentsRes] = await Promise.all([getNote(id), getComments(id)]);
      setNote(noteRes.data);
      setComments(commentsRes.data);
    } catch {
      toast.error("Could not load this note");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const handleLike = async () => {
    try {
      const res = await toggleLike(id);
      setNote((n) => ({ ...n, is_liked: res.data.liked, likes_count: n.likes_count + (res.data.liked ? 1 : -1) }));
    } catch {
      toast.error("Please log in to like notes");
    }
  };

  const handleBookmark = async () => {
    try {
      const res = await toggleBookmark(id);
      setNote((n) => ({ ...n, is_bookmarked: res.data.bookmarked }));
      toast.success(res.data.bookmarked ? "Bookmarked" : "Bookmark removed");
    } catch {
      toast.error("Please log in to bookmark notes");
    }
  };

  const handleDelete = async () => {
    if (!confirm("Delete this note? This cannot be undone.")) return;
    try {
      await deleteNote(id);
      toast.success("Note deleted");
      navigate("/notes");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not delete note");
    }
  };

  const handleComment = async (ev) => {
    ev.preventDefault();
    if (!commentText.trim()) return;
    setPosting(true);
    try {
      const res = await postComment({ note_id: Number(id), comment: commentText });
      setComments((c) => [...c, res.data]);
      setCommentText("");
    } catch {
      toast.error("Please log in to comment");
    } finally {
      setPosting(false);
    }
  };

  if (loading) return <Loader />;
  if (!note) return <p className="text-center text-slate-500">Note not found.</p>;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <Card>
        <div className="flex items-start justify-between">
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-primary-50 text-primary-700">
            {note.subject}
          </span>
          {(user?.id === note.user_id || user?.role === "admin") && (
            <div className="flex items-center gap-2">
              <Link to={`/notes/${note.id}/edit`} className="text-slate-400 hover:text-primary-600">
                <FiEdit2 />
              </Link>
              <button onClick={handleDelete} className="text-slate-400 hover:text-red-500">
                <FiTrash2 />
              </button>
            </div>
          )}
        </div>
        <h1 className="text-2xl font-bold text-slate-800 mt-3">{note.title}</h1>
        <p className="text-slate-600 mt-2 whitespace-pre-wrap">{note.description}</p>

        <div className="flex items-center gap-2 mt-4">
          <img
            src={note.author?.profile_image || `https://api.dicebear.com/7.x/initials/svg?seed=${note.author?.name}`}
            className="w-7 h-7 rounded-full object-cover"
            alt="author"
          />
          <span className="text-sm text-slate-600 font-medium">{note.author?.name}</span>
          <span className="text-xs text-slate-400 ml-auto">
            {new Date(note.created_at).toLocaleDateString()}
          </span>
        </div>

        <div className="flex items-center gap-5 pt-4 mt-4 border-t border-slate-100 text-slate-500 text-sm">
          {user && <Link to={`/ai/flashcards?noteId=${note.id}`} className="flex items-center gap-1 font-semibold text-primary-600 hover:underline"><FiLayers /> Generate Flashcards</Link>}
          <button
            onClick={handleLike}
            className={`flex items-center gap-1 hover:text-red-500 ${note.is_liked ? "text-red-500" : ""}`}
          >
            <FiHeart className={note.is_liked ? "fill-current" : ""} /> {note.likes_count} Likes
          </button>
          <button
            onClick={handleBookmark}
            className={`flex items-center gap-1 hover:text-primary-600 ${note.is_bookmarked ? "text-primary-600" : ""}`}
          >
            <FiBookmark className={note.is_bookmarked ? "fill-current" : ""} /> Bookmark
          </button>
          {note.file_url && (
            <a
              href={`${import.meta.env.VITE_API_URL || "http://localhost:8000"}${note.file_url}`}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 ml-auto text-primary-600 font-semibold hover:underline"
            >
              <FiDownload /> Download File
            </a>
          )}
        </div>
      </Card>

      <Card>
        <h3 className="font-bold text-slate-800 mb-4">{comments.length} Comments</h3>
        <div className="space-y-4 mb-4">
          {comments.map((c) => (
            <div key={c.id} className="flex gap-3">
              <img
                src={c.user?.profile_image || `https://api.dicebear.com/7.x/initials/svg?seed=${c.user?.name}`}
                className="w-8 h-8 rounded-full object-cover shrink-0"
                alt="commenter"
              />
              <div className="bg-slate-50 rounded-xl px-4 py-2.5 flex-1">
                <p className="text-sm font-semibold text-slate-700">{c.user?.name}</p>
                <p className="text-sm text-slate-600">{c.comment}</p>
              </div>
            </div>
          ))}
          {comments.length === 0 && <p className="text-sm text-slate-400">No comments yet. Be the first!</p>}
        </div>

        <form onSubmit={handleComment} className="flex gap-2">
          <input
            className="input-field flex-1"
            placeholder="Add a comment..."
            value={commentText}
            onChange={(e) => setCommentText(e.target.value)}
          />
          <Button type="submit" loading={posting}>
            <FiSend />
          </Button>
        </form>
      </Card>
    </div>
  );
}
