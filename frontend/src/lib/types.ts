export type StageId = "connect" | "reconstruct" | "verify" | "review" | "handover";
export type ItemKind =
  | "decision"
  | "task"
  | "blocker"
  | "risk"
  | "unresolved"
  | "dependency"
  | "architecture"
  | "issue"
  | "other";
export type ItemStatus =
  | "verified"
  | "needs_verification"
  | "conflicting"
  | "pending"
  | "identified"
  | "active"
  | "resolved"
  | "under_review"
  | "unknown";
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

export interface BackendProject {
  id: string;
  name: string;
  description: string;
  owner_id: string;
  members: string[];
  status: string;
  created_at?: string;
}

export interface BackendKnowledgeItem {
  id: string;
  kind: string;
  title: string;
  summary: string;
  status: string;
  sourceIds: string[];
  reviewed: boolean;
}

export interface BackendSource {
  id: string;
  name: string;
  type: string;
  source_id: string;
  project_id: string;
}

export interface BackendSourceDetail {
  id: string;
  name: string;
  title: string | null;
  type: string;
  content: string;
  metadata: Record<string, unknown>;
}

export interface BackendHandover {
  id: string;
  projectId: string;
  version: string;
  status: string;
  generatedAt: string | null;
  preparedBy: string;
}

export interface AuthResponse {
  message: string;
  access_token?: string;
  token_type?: string;
  user_id?: string;
}

export interface CurrentUserProfile {
  id: string;
  name: string;
  email: string;
}

export interface ReconstructionResult {
  project_id: string;
  claims_extracted: number;
  claims_verified: number;
  claims_unsupported: number;
  contradictions: number;
  knowledge_items_created: number;
  message: string;
}

export interface OllamaModel {
  name: string;
  size: number | null;
  digest: string | null;
  modified_at: string | null;
  parameter_size: string | null;
  quantization: string | null;
  family: string | null;
}

export interface LlmStatus {
  provider: string;
  model: string | null;
  ollama_base_url: string;
  ollama_model: string | null;
  model_selection_mode: string;
  is_ollama_provider: boolean;
}

export interface CompatibilityTestResult {
  model: string;
  status: string;
  message: string;
  claims_extracted: number;
}

export function mapBackendKnowledgeItem(item: BackendKnowledgeItem): KnowledgeItem {
  const kind: ItemKind = (() => {
    switch (item.kind) {
      case "decision": return "decision";
      case "task": return "task";
      case "risk": return "risk";
      case "dependency": return "dependency";
      case "architecture": return "architecture";
      case "issue": return "issue";
      case "other": return "other";
      case "blocker": return "blocker";
      case "unresolved": return "unresolved";
      default: return "task";
    }
  })();

  const status: ItemStatus = (() => {
    switch (item.status) {
      case "verified": return "verified";
      case "contradicted": return "conflicting";
      case "unverified": return "needs_verification";
      case "identified": return "identified";
      case "active": return "active";
      case "resolved": return "resolved";
      case "under_review": return "under_review";
      case "unknown": return "unknown";
      default: return "pending";
    }
  })();

  return {
    id: item.id,
    kind,
    title: item.title,
    summary: item.summary,
    status,
    sourceIds: item.sourceIds,
    reviewed: item.reviewed,
  };
}

export function mapBackendProject(project: BackendProject): Project {
  return {
    id: project.id,
    name: project.name,
    stage: (project.status as StageId) || "connect",
    visibleTo: "Project Team",
    draftVersion: "v0.1",
  };
}

export function mapBackendSource(source: BackendSource): Source {
  return {
    id: source.id,
    name: source.name,
    type: (source.type as SourceType) || "document",
  };
}

export function mapBackendHandover(handover: BackendHandover): Handover {
  return {
    id: handover.id,
    projectId: handover.projectId,
    version: handover.version,
    status: (handover.status as Handover["status"]) || "draft",
    generatedAt: handover.generatedAt || "",
    preparedBy: handover.preparedBy,
  };
}
