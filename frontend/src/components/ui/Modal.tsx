import { type ReactNode, useEffect } from "react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
}

export function Modal({ open, onClose, title, children }: ModalProps) {
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-60 flex items-end justify-center sm:items-center">
      <div
        data-testid="modal-backdrop"
        role="presentation"
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-label={title}
        aria-modal="true"
        className="relative z-10 max-h-[85dvh] w-full max-w-lg overflow-y-auto rounded-t-2xl bg-tg-bg p-6 sm:max-h-[90dvh] sm:rounded-2xl"
      >
        {children}
      </div>
    </div>
  );
}
