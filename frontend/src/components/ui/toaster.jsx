import { CheckCircle2, Info, XCircle } from 'lucide-react'
import { useToast } from "@/hooks/use-toast"
import {
  Toast,
  ToastClose,
  ToastDescription,
  ToastProvider,
  ToastTitle,
  ToastViewport,
} from "@/components/ui/toast"
import { cn } from '@/lib/utils'

export function Toaster() {
  const { toasts } = useToast()

  const iconVariants = {
    success: 'border-emerald-400 bg-emerald-500 text-white shadow-[0_4px_12px_rgba(16,185,129,0.35)]',
    destructive: 'border-red-400 bg-red-500 text-white shadow-[0_4px_12px_rgba(239,68,68,0.35)]',
    default: 'border-slate-200 bg-slate-100 text-slate-700 shadow-[0_4px_12px_rgba(148,163,184,0.35)]',
  }

  const iconComponents = {
    success: CheckCircle2,
    destructive: XCircle,
    default: Info,
  }

  return (
    <ToastProvider>
      {toasts.map(function ({ id, title, description, action, ...props }) {
        const variant = props.variant || 'default'
        const Icon = iconComponents[variant] || iconComponents.default
        const iconClassName = iconVariants[variant] || iconVariants.default

        return (
          <Toast key={id} variant={variant} {...props}>
            <div className="flex w-full items-start gap-3">
              <span
                className={cn(
                  'flex h-10 w-10 items-center justify-center rounded-full border-2',
                  iconClassName
                )}
              >
                <Icon className="h-5 w-5" />
              </span>
              <div className="grid gap-1 text-sm">
                {title && <ToastTitle className="text-base font-semibold">{title}</ToastTitle>}
                {description && (
                  <ToastDescription className="text-sm leading-relaxed text-current/80">
                    {description}
                  </ToastDescription>
                )}
              </div>
            </div>
            {action}
            <ToastClose />
          </Toast>
        );
      })}
      <ToastViewport />
    </ToastProvider>
  );
}
