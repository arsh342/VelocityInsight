interface LoadingProps {
  size?: "sm" | "md" | "lg";
  variant?: "spinner" | "dots" | "pulse";
  text?: string;
  className?: string;
}

export default function Loading({
  size = "md",
  variant = "spinner",
  text,
  className = "",
}: LoadingProps) {
  const sizeClasses = {
    sm: "w-4 h-4",
    md: "w-8 h-8",
    lg: "w-12 h-12",
  };

  const containerClasses = `flex flex-col items-center justify-center gap-3 text-muted-foreground ${className}`;

  return (
    <div className={containerClasses}>
      {variant === "spinner" && (
        <div className={`${sizeClasses[size]} border-4 border-primary border-t-transparent rounded-full animate-spin`}></div>
      )}
      {variant === "dots" && (
        <div className="flex gap-1">
          <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]"></div>
          <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.15s]"></div>
          <div className="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
        </div>
      )}
      {variant === "pulse" && (
        <div className={`${sizeClasses[size]} bg-primary/50 rounded-full animate-pulse`}></div>
      )}
      {text && <p className="text-sm font-medium animate-pulse">{text}</p>}
    </div>
  );
}
