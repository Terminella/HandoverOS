import type { Stage } from "./types";

/** Single source of truth for the five-stage workflow. */
export const STAGES: Stage[] = [
  { id: "connect", label: "Connect", hint: "Ingest sources" },
  { id: "reconstruct", label: "Reconstruct", hint: "Build project context" },
  { id: "verify", label: "Verify", hint: "Trace, detect and validate" },
  { id: "review", label: "Review", hint: "Edit and confirm" },
  { id: "handover", label: "Handover", hint: "Generate and share" },
];
