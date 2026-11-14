import type { ItemKind, ItemStatus } from "./types";

export const STATUS_LABEL: Record<ItemStatus, string> = {
  verified: "Verified",
  needs_verification: "Needs Verification",
  conflicting: "Conflicting",
  pending: "Pending",
  identified: "Identified",
  active: "Active",
  resolved: "Resolved",
  under_review: "Under Review",
  unknown: "Unknown",
};

export const KIND_LABEL: Record<ItemKind, string> = {
  decision: "Key Decision",
  task: "Task",
  blocker: "Blocker",
  risk: "Risk",
  unresolved: "Unresolved Question",
  dependency: "Dependency",
  architecture: "Architecture",
  issue: "Issue",
  other: "Other",
};
