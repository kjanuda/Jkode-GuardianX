import {
  Bot,
  BrainCircuit,
  LayoutDashboard,
  MapIcon,
  RadioTower,
  Siren,
  Wrench,
} from "lucide-react";


export const navigation = [
  {
    label: "Overview",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    label: "Network",
    href: "/",
    icon: RadioTower,
  },
  {
    label: "Alerts",
    href: "/alerts",
    icon: Siren,
  },
  {
    label: "RCA Intelligence",
    href: "/rca",
    icon: BrainCircuit,
  },
  {
    label: "Actions",
    href: "/actions",
    icon: Wrench,
  },
  {
    label: "Geo Map",
    href: "/map",
    icon: MapIcon,
  },
  {
    label: "AI Agent",
    href: "/agent",
    icon: Bot,
  },
];
