import { Skeleton } from "@/components/ui/skeleton";

export function SkeletonCard() { return <div className="rounded-2xl border border-border/70 bg-card p-5"><Skeleton className="mb-4 h-3 w-20" /><Skeleton className="mb-3 h-8 w-28" /><Skeleton className="h-3 w-36" /></div>; }
export function SkeletonChart() { return <div className="rounded-2xl border border-border/70 bg-card p-6"><Skeleton className="mb-6 h-5 w-44" /><Skeleton className="h-64 w-full" /></div>; }
export function SkeletonTable() { return <div className="rounded-2xl border border-border/70 bg-card p-6"><Skeleton className="mb-6 h-5 w-40" />{[1, 2, 3, 4].map((item) => <Skeleton key={item} className="mb-4 h-10 w-full" />)}</div>; }
export function SkeletonList() { return <div className="space-y-3">{[1, 2, 3].map((item) => <div key={item} className="rounded-2xl border border-border/70 bg-card p-5"><Skeleton className="mb-3 h-4 w-1/3" /><Skeleton className="h-3 w-4/5" /></div>)}</div>; }
