import { useCallback, useEffect, useState } from "react";
import { FiChevronLeft, FiChevronRight, FiPause, FiPlay, FiRotateCw, FiSquare } from "react-icons/fi";
import toast from "react-hot-toast";

import FlashcardFlipCard from "./FlashcardFlipCard";

const speechLang = { en: "en-US", ta: "ta-IN", si: "si-LK" };

export default function FlashcardViewer({ cards, language = "en", onFavourite, readOnly = false }) {
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [speechState, setSpeechState] = useState("idle");
  const current = cards[index];
  const stopSpeech = useCallback(() => { window.speechSynthesis?.cancel(); setSpeechState("idle"); }, []);
  const move = useCallback((next) => { stopSpeech(); setIndex((value) => Math.max(0, Math.min(cards.length - 1, value + next))); setFlipped(false); }, [cards.length, stopSpeech]);

  useEffect(() => {
    const keydown = (event) => {
      if (["INPUT", "TEXTAREA", "SELECT"].includes(event.target.tagName)) return;
      if (event.code === "Space") { event.preventDefault(); setFlipped((value) => !value); stopSpeech(); }
      if (event.key === "ArrowLeft") move(-1);
      if (event.key === "ArrowRight") move(1);
    };
    window.addEventListener("keydown", keydown);
    return () => { window.removeEventListener("keydown", keydown); stopSpeech(); };
  }, [move, stopSpeech]);

  useEffect(() => { if (index >= cards.length) setIndex(0); }, [cards.length, index]);

  const speak = () => {
    if (!("speechSynthesis" in window)) return toast.error("Text-to-speech is unavailable in this browser");
    const desired = speechLang[language] || speechLang.en;
    const voices = window.speechSynthesis.getVoices();
    const voice = voices.find((item) => item.lang.toLowerCase().startsWith(desired.slice(0, 2)));
    if (!voice && language !== "en") toast("A matching voice is unavailable; the browser default will be used.");
    stopSpeech();
    const utterance = new SpeechSynthesisUtterance(flipped ? current.answer : current.question);
    utterance.lang = desired; if (voice) utterance.voice = voice;
    utterance.onend = () => setSpeechState("idle"); utterance.onerror = () => setSpeechState("idle");
    window.speechSynthesis.speak(utterance); setSpeechState("playing");
  };
  const pauseResume = () => { if (speechState === "playing") { window.speechSynthesis.pause(); setSpeechState("paused"); } else { window.speechSynthesis.resume(); setSpeechState("playing"); } };

  if (!current) return null;
  return <div className="space-y-4">
    <FlashcardFlipCard card={current} flipped={flipped} onFlip={() => { stopSpeech(); setFlipped((value) => !value); }} onFavourite={onFavourite} readOnly={readOnly} />
    <div className="flex flex-wrap items-center justify-between gap-3">
      <button className="btn-secondary" disabled={index === 0} onClick={() => move(-1)} aria-label="Previous card"><FiChevronLeft /></button>
      <div className="flex items-center gap-2">
        <button className="rounded-lg p-2 text-primary-600 hover:bg-primary-50" onClick={() => setFlipped((value) => !value)} title="Flip card"><FiRotateCw /></button>
        <button className="rounded-lg p-2 text-primary-600 hover:bg-primary-50" onClick={speak} title="Read card aloud"><FiPlay /></button>
        {speechState !== "idle" && <button className="rounded-lg p-2 text-primary-600" onClick={pauseResume} title={speechState === "paused" ? "Resume speech" : "Pause speech"}>{speechState === "paused" ? <FiPlay /> : <FiPause />}</button>}
        {speechState !== "idle" && <button className="rounded-lg p-2 text-red-500" onClick={stopSpeech} title="Stop speech"><FiSquare /></button>}
      </div>
      <span className="text-sm font-semibold text-slate-600 dark:text-slate-300">Card {index + 1} of {cards.length}</span>
      <button className="btn-secondary" disabled={index === cards.length - 1} onClick={() => move(1)} aria-label="Next card"><FiChevronRight /></button>
    </div>
  </div>;
}
