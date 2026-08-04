import { motion } from "framer-motion";
import { FiHeart, FiImage } from "react-icons/fi";
import { BASE_URL } from "../../services/api";

export default function FlashcardFlipCard({ card, flipped, onFlip, onFavourite, readOnly = false }) {
  return (
    <div className="h-[320px] w-full [perspective:1200px] sm:h-[360px]">
      <motion.button
        type="button"
        aria-label={flipped ? "Showing answer. Activate to show question" : "Showing question. Activate to show answer"}
        aria-pressed={flipped}
        onClick={onFlip}
        className="relative h-full w-full rounded-lg text-left focus:outline-none focus:ring-4 focus:ring-primary-300"
        animate={{ rotateY: flipped ? 180 : 0 }}
        transition={{ duration: 0.45, ease: "easeInOut" }}
        style={{ transformStyle: "preserve-3d" }}
      >
        {[false, true].map((back) => (
          <span key={String(back)} className={`absolute inset-0 flex flex-col overflow-hidden rounded-lg border p-7 shadow-lg [backface-visibility:hidden] sm:p-10 ${back ? "rotate-y-180 border-emerald-300 bg-emerald-50 dark:border-emerald-700 dark:bg-emerald-950" : "border-primary-200 bg-white dark:border-slate-700 dark:bg-slate-900"}`} style={{ transform: back ? "rotateY(180deg)" : "none" }}>
            <span className="text-xs font-bold uppercase text-slate-400">{back ? "Answer" : "Question"}</span>
            {card.image_url && <img src={card.image_url.startsWith("/") ? `${BASE_URL}${card.image_url}` : card.image_url} alt="Flashcard visual" onError={(event) => { event.currentTarget.style.display = "none"; }} className="mt-3 h-28 w-full rounded object-contain" />}
            {!card.image_url && <FiImage className="mt-5 text-slate-200" size={38} aria-hidden="true" />}
            <span className="flex flex-1 items-center justify-center overflow-y-auto text-center text-lg font-semibold leading-8 text-slate-800 dark:text-slate-100 sm:text-xl">{back ? card.answer : card.question}</span>
          </span>
        ))}
      </motion.button>
      {!readOnly && card.id && <button type="button" onClick={(event) => { event.stopPropagation(); onFavourite?.(card); }} title="Favourite card" className={`relative -mt-12 ml-auto mr-4 flex h-9 w-9 items-center justify-center rounded-full ${card.is_favourite ? "bg-red-100 text-red-600" : "bg-slate-100 text-slate-500"}`}><FiHeart className={card.is_favourite ? "fill-current" : ""} /></button>}
    </div>
  );
}
