import { motion } from "framer-motion";

export default function Card({ children, className = "", hover = true, ...props }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={hover ? { y: -4 } : {}}
      className={`glass-card p-5 ${className}`}
      {...props}
    >
      {children}
    </motion.div>
  );
}
