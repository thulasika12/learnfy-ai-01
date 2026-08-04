import { motion } from "framer-motion";

export default function Loader({ full = false, label = "Loading..." }) {
  const content = (
    <div className="flex flex-col items-center justify-center gap-3 py-10">
      <motion.div
        className="w-10 h-10 rounded-full border-4 border-primary-200 border-t-primary-600"
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 0.8, ease: "linear" }}
      />
      {label && <p className="text-sm text-slate-500 font-medium">{label}</p>}
    </div>
  );

  if (full) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/70 backdrop-blur-sm">
        {content}
      </div>
    );
  }

  return content;
}
