import type {
  LucideIcon,
} from "lucide-react";


interface StatCardProps {
  title: string;
  value: number | string;
  description: string;
  icon: LucideIcon;
}


export default function StatCard({
  title,
  value,
  description,
  icon: Icon,
}: StatCardProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.035] p-5 shadow-2xl shadow-black/10">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.15em] text-white/35">
            {title}
          </p>

          <p className="mt-3 text-3xl font-semibold tracking-tight text-white">
            {value}
          </p>
        </div>

        <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5">
          <Icon className="h-5 w-5 text-cyan-300" />
        </div>
      </div>

      <p className="mt-4 text-xs text-white/35">
        {description}
      </p>
    </div>
  );
}
