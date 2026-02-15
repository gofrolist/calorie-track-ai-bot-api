export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      role="status"
      aria-busy="true"
      aria-label="Loading"
      className={`animate-pulse rounded bg-tg-secondary-bg ${className}`}
    />
  );
}
