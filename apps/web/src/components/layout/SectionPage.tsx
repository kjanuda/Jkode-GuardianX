import type {
  LucideIcon,
} from "lucide-react";

import Sidebar from "@/components/dashboard/Sidebar";
import MobileNav from "@/components/layout/MobileNav";


interface SectionPageProps {
  title: string;
  eyebrow: string;
  description: string;
  icon: LucideIcon;
  children?: React.ReactNode;
}


export default function SectionPage({
  title,
  eyebrow,
  description,
  icon: Icon,
  children,
}: SectionPageProps) {
  return (
    <main className="min-h-screen bg-[#050811] text-white">
      <div className="flex min-h-screen">
        <Sidebar />

        <div className="min-w-0 flex-1">
          <MobileNav />

          <header className="flex min-h-20 items-center border-b border-white/10 px-5 md:px-8">
            <div className="flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-cyan-400/15 bg-cyan-400/5">
                <Icon className="h-5 w-5 text-cyan-300" />
              </div>

              <div>
                <p className="text-[10px] uppercase tracking-[0.18em] text-cyan-300/60">
                  {eyebrow}
                </p>

                <h1 className="mt-1 text-lg font-medium">
                  {title}
                </h1>
              </div>
            </div>
          </header>

          <div className="p-5 md:p-8">
            <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-6">
              <p className="max-w-3xl text-sm leading-7 text-white/45">
                {description}
              </p>

              {children ? (
                <div className="mt-6">
                  {children}
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
