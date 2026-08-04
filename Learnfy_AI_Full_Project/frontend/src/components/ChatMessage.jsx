import { motion } from "framer-motion";
import { FiUser, FiZap } from "react-icons/fi";

export default function ChatMessage({ role, content }) {
  const isUser = role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex items-start gap-3 ${isUser ? "flex-row-reverse" : ""}`}
    >
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
          isUser ? "bg-primary-600 text-white" : "bg-brand-gradient text-white"
        }`}
      >
        {isUser ? <FiUser size={16} /> : <FiZap size={16} />}
      </div>
      <div
        className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm whitespace-pre-wrap leading-relaxed ${
          isUser
            ? "bg-primary-600 text-white rounded-tr-sm"
            : "bg-white border border-slate-100 text-slate-700 rounded-tl-sm shadow-sm"
        }`}
      >
        {content}
      </div>
    </motion.div>
  );
}
