export default function Button({
  children,
  variant = "primary",
  className = "",
  loading = false,
  disabled = false,
  type = "button",
  ...props
}) {
  const base = variant === "primary" ? "btn-primary" : "btn-secondary";

  return (
    <button
      type={type}
      disabled={disabled || loading}
      className={`${base} ${className}`}
      {...props}
    >
      {loading && (
        <span className="w-4 h-4 border-2 border-white/50 border-t-white rounded-full animate-spin" />
      )}
      {children}
    </button>
  );
}
