interface Props {
  value:
    | string
    | null
    | undefined;
}


export default function ActionStatusBadge({
  value,
}: Props) {
  const status =
    value ?? "UNKNOWN";

  let classes =
    "border-white/10 bg-white/5 text-white/50";

  if (
    status === "VERIFIED_SUCCESS" ||
    status === "VERIFIED" ||
    status === "PASSED" ||
    status === "ELIGIBLE_FOR_POLICY_REVIEW"
  ) {
    classes =
      "border-emerald-400/20 bg-emerald-400/10 text-emerald-300";
  }

  if (
    status === "BLOCKED" ||
    status === "REJECTED" ||
    status === "VERIFIED_FAILED" ||
    status === "ROLLBACK_REQUIRED"
  ) {
    classes =
      "border-red-400/20 bg-red-400/10 text-red-300";
  }

  if (
    status === "ADVISORY" ||
    status === "DRY_RUN"
  ) {
    classes =
      "border-cyan-400/20 bg-cyan-400/10 text-cyan-300";
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
