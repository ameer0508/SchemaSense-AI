import React, { forwardRef } from 'react'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'subtle'
  size?: 'xs' | 'sm' | 'md' | 'lg'
  isLoading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'secondary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      'inline-flex items-center justify-center font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 disabled:opacity-50 disabled:cursor-not-allowed select-none'

    const sizeStyles = {
      xs: 'text-xs px-2.5 py-1 rounded-[6px] gap-1.5',
      sm: 'text-xs px-3 py-1.5 rounded-[8px] gap-2',
      md: 'text-sm px-4 py-2 rounded-[10px] gap-2',
      lg: 'text-base px-5 py-2.5 rounded-[12px] gap-2.5',
    }[size]

    const variantStyles = {
      primary:
        'bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm hover:shadow-indigo-500/25 active:bg-indigo-700 disabled:hover:bg-indigo-600',
      secondary:
        'bg-slate-800/80 hover:bg-slate-700/80 text-slate-100 border border-slate-700/80 hover:border-slate-600 active:bg-slate-800 light:bg-slate-100 light:hover:bg-slate-200 light:text-slate-900 light:border-slate-300',
      outline:
        'bg-transparent hover:bg-slate-800/50 text-slate-300 hover:text-white border border-slate-700/80 light:text-slate-700 light:hover:bg-slate-100 light:border-slate-300',
      ghost:
        'bg-transparent hover:bg-slate-800/60 text-slate-400 hover:text-slate-200 light:hover:bg-slate-100 light:text-slate-600 light:hover:text-slate-900',
      danger:
        'bg-rose-600/15 hover:bg-rose-600/25 text-rose-400 border border-rose-500/30 active:bg-rose-600/30',
      subtle:
        'bg-slate-800/40 hover:bg-slate-800 text-slate-300 hover:text-white border border-transparent hover:border-slate-700/60 light:bg-slate-100 light:text-slate-700',
    }[variant]

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={twMerge(clsx(baseStyles, sizeStyles, variantStyles, className))}
        {...props}
      >
        {isLoading ? (
          <svg
            className="animate-spin -ml-0.5 mr-2 h-4 w-4 text-current"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
            />
          </svg>
        ) : (
          leftIcon
        )}
        {children}
        {!isLoading && rightIcon}
      </button>
    )
  }
)

Button.displayName = 'Button'
