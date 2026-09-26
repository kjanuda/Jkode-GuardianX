interface StatusBadgeProps {
  value:
    | string
    | null
    | undefined;
}


export default function StatusBadge({
  value,
}: StatusBadgeProps) {
  const status =
    value ?? "UNKNOWN";

  let classes =
    "border-white/10 bg-white/5 text-white/50";

  if (
    status === "VERIFIED" ||
    status === "AGREEMENT" ||
    status === "ACCEPTED"
  ) {
    classes =
      "border-emerald-400/20 bg-emerald-400/10 text-emerald-300";
  }

  if (
    status === "REJECTED" ||
    status === "BLOCKED"
  ) {
    classes =
      "border-red-400/20 bg-red-400/10 text-red-300";
  }

  if (
    status.includes(
      "NOT_VERIFIED"
    )
  ) {
    classes =
      "border-amber-400/20 bg-amber-400/10 text-amber-300";
  }

  return (
    <span
      className={[
        "inline-flex rounded-full border px-2.5 py-1 text-[10px]",
        classes,
      ].join(" ")}
    >
      {status}
    </span>
  );
}
