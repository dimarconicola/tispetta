import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function RouteLoading({
  eyebrow,
  title,
  body,
}: {
  eyebrow: string;
  title: string;
  body: string;
}) {
  return (
    <div className="grid gap-6 pb-8">
      <Card>
        <CardHeader className="gap-3">
          <Badge variant="soft" className="w-fit">
            {eyebrow}
          </Badge>
          <CardTitle className="text-4xl leading-[0.95]">{title}</CardTitle>
          <p className="max-w-2xl text-base leading-7 text-slate-500">{body}</p>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-3">
          <LoadingStat />
          <LoadingStat />
          <LoadingStat />
        </CardContent>
      </Card>

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        <LoadingCard />
        <LoadingCard />
        <LoadingCard className="hidden xl:grid" />
      </div>
    </div>
  );
}

function LoadingStat() {
  return (
    <div className="grid gap-3 rounded-[1.5rem] border border-border/70 bg-slate-50/85 p-4 shadow-sm">
      <div className="h-3 w-24 animate-pulse rounded-full bg-slate-200" />
      <div className="h-8 w-16 animate-pulse rounded-full bg-slate-200" />
    </div>
  );
}

function LoadingCard({ className = '' }: { className?: string }) {
  return (
    <div className={`grid gap-4 rounded-[2rem] border border-border/70 bg-white/85 p-5 shadow-sm ${className}`}>
      <div className="h-6 w-28 animate-pulse rounded-full bg-slate-200" />
      <div className="grid gap-3">
        <div className="h-8 w-5/6 animate-pulse rounded-2xl bg-slate-200" />
        <div className="h-8 w-2/3 animate-pulse rounded-2xl bg-slate-200" />
      </div>
      <div className="h-16 animate-pulse rounded-[1.5rem] bg-slate-100" />
      <div className="grid gap-2 rounded-[1.5rem] border border-slate-100 bg-slate-50/90 p-4">
        <div className="h-4 w-3/4 animate-pulse rounded-full bg-slate-200" />
        <div className="h-4 w-1/2 animate-pulse rounded-full bg-slate-200" />
        <div className="h-4 w-2/3 animate-pulse rounded-full bg-slate-200" />
      </div>
      <div className="flex gap-2">
        <div className="h-8 w-24 animate-pulse rounded-full bg-slate-200" />
        <div className="h-8 w-20 animate-pulse rounded-full bg-slate-200" />
      </div>
    </div>
  );
}
