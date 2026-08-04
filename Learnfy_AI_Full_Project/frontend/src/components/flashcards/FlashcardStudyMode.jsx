import { useState } from "react";
import { FiCheck, FiRefreshCw } from "react-icons/fi";
import toast from "react-hot-toast";

import FlashcardFlipCard from "./FlashcardFlipCard";
import { saveFlashcardStudySession } from "../../services/api";

export default function FlashcardStudyMode({ flashcardSet, onComplete }) {
  const [index, setIndex] = useState(0); const [flipped, setFlipped] = useState(false); const [answers, setAnswers] = useState([]); const [started] = useState(() => Date.now()); const [saving, setSaving] = useState(false); const [result, setResult] = useState(null);
  const card = flashcardSet.cards[index];
  const answer = async (status) => {
    const next = [...answers, { card_id: card.id, status }];
    if (index < flashcardSet.cards.length - 1) { setAnswers(next); setIndex(index + 1); setFlipped(false); return; }
    setSaving(true);
    try { const response = await saveFlashcardStudySession(flashcardSet.id, { answers: next, duration_seconds: Math.round((Date.now() - started) / 1000) }); setResult(response.data); onComplete?.(response.data); }
    catch (error) { toast.error(error.response?.data?.detail || "Could not save study result"); }
    finally { setSaving(false); }
  };
  if (result) return <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-8 text-center dark:border-emerald-800 dark:bg-emerald-950"><h3 className="text-2xl font-black text-emerald-700 dark:text-emerald-300">Study complete</h3><p className="mt-3 text-5xl font-black text-slate-900 dark:text-white">{Math.round(result.score_percentage)}%</p><p className="mt-2 text-slate-600 dark:text-slate-300">{result.correct_count} known · {result.incorrect_count} to review · {result.duration_seconds}s</p></div>;
  return <div className="space-y-4"><p className="text-center text-sm font-semibold text-slate-500">Study card {index + 1} of {flashcardSet.cards.length}</p><FlashcardFlipCard card={card} flipped={flipped} onFlip={() => setFlipped(!flipped)} readOnly /><div className="grid gap-3 sm:grid-cols-2"><button disabled={saving} onClick={() => answer("review")} className="btn-secondary justify-center"><FiRefreshCw /> Review Again</button><button disabled={saving} onClick={() => answer("known")} className="btn-primary justify-center"><FiCheck /> I Know This</button></div></div>;
}
