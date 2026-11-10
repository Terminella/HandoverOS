export type StageId = "connect" | "reconstruct" | "verify" | "review" | "handover";
export type ItemKind = "decision" | "task" | "blocker" | "risk" | "unresolved";
export type ItemStatus = "verified" | "needs_verification" | "conflicting" | "pending";
export type SourceType = "document" | "repository" | "notes" | "chat";

export interface Stage {
  id: StageId;
  label: string;
  hint: string;
}

export interface Source {
  id: string;
  name: string;
  type: SourceType;
}

export interface KnowledgeItem {
  id: string;
  kind: ItemKind;
  title: string;
  summary: string;
  status: ItemStatus;
  sourceIds: string[];
  reviewed: boolean;
}

export interface Project {
  id: string;
  name: string;
  stage: StageId;
  visibleTo: string;
  draftVersion: string;
}

export interface CurrentUser {
  name: string;
  initials: string;
}

export interface Handover {
  id: string;
  projectId: string;
  version: string;
  status: "draft" | "pending_review" | "approved";
  generatedAt: string;
  preparedBy: string;
}

export interface TeamMember {
  id: string;
  name: string;
  role: string;
  initials: string;
}
