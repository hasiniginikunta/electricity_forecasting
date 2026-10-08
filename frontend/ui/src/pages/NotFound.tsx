import { ArrowLeft, Compass } from "lucide-react";
import { Link } from "react-router-dom";

const NotFound = () => <div className="flex min-h-screen items-center justify-center bg-background px-5 text-foreground"><div className="text-center"><div className="mx-auto grid size-16 place-items-center rounded-2xl bg-violet-500/10 text-violet-300"><Compass className="size-7" /></div><p className="mt-7 text-xs font-semibold uppercase tracking-[0.2em] text-violet-300">Energy Intelligence</p><h1 className="mt-3 font-display text-6xl font-semibold">404</h1><p className="mt-3 text-sm text-muted-foreground">That energy signal couldn't be found.</p><Link to="/" className="mt-7 inline-flex items-center gap-2 rounded-xl bg-violet-500 px-4 py-2.5 text-sm font-semibold text-white hover:bg-violet-400"><ArrowLeft className="size-4" />Return to overview</Link></div></div>;
export default NotFound;
