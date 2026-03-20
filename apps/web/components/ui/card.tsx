import * as React from 'react';

import { cn } from '@/lib/utils';

const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(function Card(
  { className, ...props },
  ref
) {
  return <div ref={ref} className={cn('rounded-[2rem] border border-border/80 bg-card/95 shadow-[0_20px_60px_rgba(15,23,42,0.08)] backdrop-blur', className)} {...props} />;
});

const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(function CardHeader(
  { className, ...props },
  ref
) {
  return <div ref={ref} className={cn('flex flex-col gap-2 p-6 pb-0', className)} {...props} />;
});

const CardTitle = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLHeadingElement>>(function CardTitle(
  { className, ...props },
  ref
) {
  return <h3 ref={ref} className={cn('font-heading text-xl font-semibold tracking-tight text-foreground', className)} {...props} />;
});

const CardDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(function CardDescription(
  { className, ...props },
  ref
) {
  return <p ref={ref} className={cn('text-sm leading-6 text-muted-foreground', className)} {...props} />;
});

const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(function CardContent(
  { className, ...props },
  ref
) {
  return <div ref={ref} className={cn('p-6', className)} {...props} />;
});

const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(function CardFooter(
  { className, ...props },
  ref
) {
  return <div ref={ref} className={cn('flex items-center gap-3 p-6 pt-0', className)} {...props} />;
});

export { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle };
