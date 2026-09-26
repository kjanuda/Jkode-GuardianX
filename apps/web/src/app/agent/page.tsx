import {
  Sparkles,
} from "lucide-react";

import AgentChat from "@/components/agent/AgentChat";
import SectionPage from "@/components/layout/SectionPage";

export default function AgentPage() {
  return (
    <SectionPage
      eyebrow="Evidence Assistant"
      title="Guardian AI Agent"
      description="Ask natural-language questions across RCA, alerts, telemetry and guarded action plans using local evidence-grounded AI."
      icon={Sparkles}
    >
      <AgentChat />
    </SectionPage>
  );
}
