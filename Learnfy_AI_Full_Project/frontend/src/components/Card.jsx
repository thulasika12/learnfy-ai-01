import { motion } from "framer-motion";

export default function Card({ children, className = "", hover = true, delay = 0, ...props }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay, ease: [0.22, 1, 0.36, 1] }}
      whileHover={hover ? { y: -4 } : {}}
      className={`glass-card p-5 ${hover ? "motion-card" : ""} ${className}`}
      {...props}
    >
      {children}
    </motion.div>
  );
}
