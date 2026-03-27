import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';

import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ring-offset-background',
  {
    variants: {
      variant: {
        default: 'border border-[#14110f] bg-[#14110f] text-[#fafaf9] shadow-sm hover:-translate-y-0.5 hover:bg-[#22201d] hover:text-[#fafaf9] hover:shadow-lg hover:shadow-black/10',
        secondary: 'border border-[#14110f]/12 bg-[#faf6ef] text-[#14110f] hover:-translate-y-0.5 hover:border-[#14110f]/24 hover:bg-[#f1e7da] hover:text-[#14110f]',
        ghost: 'text-muted-foreground hover:bg-accent hover:text-foreground',
        link: 'h-auto rounded-none p-0 text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-11 px-5',
        sm: 'h-9 px-4 text-xs',
        lg: 'h-12 px-6 text-base',
        icon: 'size-11 rounded-2xl',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant, size, asChild = false, ...props },
  ref
) {
  const Comp = asChild ? Slot : 'button';
  return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />;
});

export { Button, buttonVariants };
