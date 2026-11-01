import React from 'react'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'indigo' | 'cyan' | 'success' | 'error' | 'warning' | 'outline' | 'neutral'
  size?: 'xs' | 'sm' | 'md'
  dot?: boolean
}

export function Badge({
  className,
  variant = 'default',
  size = 'sm',
  dot = false,
  children,
  ...props
}: BadgeProps) {
  const baseStyles = 'inline-flex items-center font-medium select-none tracking-wide transition-colors'

  const sizeStyles = {
    xs: 'text-[10px] px-1.5 py-0.5 rounded-[5px] gap-1',
    sm: 'text-xs px-2.5 py-0.5 rounded-[6px] gap-1.5',
    md: 'text-xs px-3 py-1 rounded-[8px] gap-1.5',
  }[size]

  const variantStyles = {
    default:
      'bg-slate-800/80 text-slate-300 border border-slate-700/60 light:bg-slate-200 light:text-slate-800 light:border-slate-300',
    indigo:
      'bg-indigo-500/10 text-indigo-400 border border-indigo-500/25 light:bg-indigo-50 light:text-indigo-700 light:border-indigo-200',
    cyan:
      'bg-cyan-500/10 text-cyan-400 border border-cyan-500/25 light:bg-cyan-50 light:text-cyan-700 light:border-cyan-200',
    success:
      'bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 light:bg-emerald-50 light:text-emerald-700 light:border-emerald-200',
    error:
      'bg-rose-500/10 text-rose-400 border border-rose-500/25 light:bg-rose-50 light:text-rose-700 light:border-rose-200',
    warning:
      'bg-amber-500/10 text-amber-400 border border-amber-500/25 light:bg-amber-50 light:text-amber-700 light:border-amber-200',
    outline:
      'bg-transparent text-slate-400 border border-slate-700/80 light:text-slate-600 light:border-slate-300',
    neutral:
      'bg-slate-900/60 text-slate-400 border border-slate-800 light:bg-slate-100 light:text-slate-600 light:border-slate-200',
  }[variant]

  const dotColors = {
    default: 'bg-slate-400',
    indigo: 'bg-indigo-400 animate-pulse',
    cyan: 'bg-cyan-400 animate-pulse',
    success: 'bg-emerald-400',
    error: 'bg-rose-400',
    warning: 'bg-amber-400',
    outline: 'bg-slate-400',
    neutral: 'bg-slate-400',
  }[variant]

  return (
    <span className={twMerge(clsx(baseStyles, sizeStyles, variantStyles, className))} {...props}>
      {dot && <span className={clsx('h-1.5 w-1.5 rounded-full', dotColors)} />}
      {children}
    </span>
  )
}
