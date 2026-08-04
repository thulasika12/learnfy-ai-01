import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { FiLock } from "react-icons/fi";
import FlashcardViewer from "../../components/flashcards/FlashcardViewer";
import Loader from "../../components/Loader";
import { getSharedFlashcardSet } from "../../services/api";

export default function SharedFlashcard() {
  const { token } = useParams(); const [item, setItem] = useState(null); const [error, setError] = useState("");
  useEffect(() => { getSharedFlashcardSet(token).then((res) => setItem(res.data)).catch((err) => setError(err.response?.data?.detail || "This share link is unavailable")); }, [token]);
  if (error) return <div className="mx-auto max-w-lg py-20 text-center"><FiLock className="mx-auto text-slate-400" size={40} /><h1 className="mt-4 text-2xl font-black dark:text-white">Link unavailable</h1><p className="mt-2 text-slate-500">{error}</p><Link to="/" className="btn-primary mt-6">Go to Learnfy AI</Link></div>;
  if (!item) return <Loader />;
  return <div className="mx-auto max-w-3xl px-5 py-12"><p className="text-sm font-bold text-primary-600">Shared Learnfy AI flashcards · Read only</p><h1 className="mt-2 text-3xl font-black text-slate-900 dark:text-white">{item.title}</h1><p className="mb-7 mt-2 text-sm text-slate-500">{item.subject} · {item.difficulty} · {item.cards.length} cards</p><FlashcardViewer cards={item.cards} language={item.language} readOnly /></div>;
}
