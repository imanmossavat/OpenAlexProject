import React from 'react'

const base = 'inline-flex items-center justify-center whitespace-nowrap transition-colors focus:outline-none disabled:opacity-50 disabled:pointer-events-none'

const variants = {
  default: 'bg-gray-900 text-white hover:bg-gray-800',
  outline: 'bg-white border border-gray-200 text-black hover:bg-gray-50',
  secondary: 'bg-gray-100 text-black hover:bg-gray-200',
  ghost: '', // Empty variant that doesn't apply any styles
}

const sizes = {
  default: 'h-10 px-4 py-2 text-sm',
  lg: 'h-12 px-8 py-3 text-base',
  sm: 'h-9 px-3 text-sm',
}

export function Button({ variant = 'default', size = 'default', className = '', asChild = false, ...props }) {
  const variantClass = variant && variant !== 'ghost' ? (variants[variant] || variants.default) : ''
  
  const cls = [base, variantClass, sizes[size] || sizes.default, className]
    .filter(Boolean)
    .join(' ')
  
  const Comp = asChild ? 'span' : 'button'
  return <Comp className={cls} {...props} />
}

export default Button