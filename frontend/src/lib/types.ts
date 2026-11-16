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
export type IntelligenceReviewStatus =
  | "unreviewed"
  | "approved"
  | "rejected"
  | "clarification_required";
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
  sourceIdentifier?: string;
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

export interface IntelligenceRun {
  run_id: string;
  project_id: string;
  status: "pending" | "running" | "completed" | "failed" | string;
  selected_source_count: number;
  result_counts: {
    claims_extracted: number;
    claims_verified: number;
    claims_unsupported: number;
    contradictions: number;
    knowledge_items_created: number;
  } | null;
  error: { code: string; message: string } | null;
  provider: string | null;
  model: string | null;
  idempotency_key: string | null;
  created_at: string | null;
  started_at: string | null;
  finished_at: string | null;
}

export interface IntelligenceEvidence {
  id: string;
  source_id: string;
  source_name: string | null;
  source_identifier: string | null;
  quote: string;
}

export interface IntelligenceContradiction {
  id: string;
  claim_ids: string[];
  source_ids: string[];
  explanation: string;
  requires_human_review: boolean;
}

export interface FindingReviewHistory {
  id: string;
  reviewer_id: string;
  action: string;
  previous_status: string;
  new_status: string;
  previous_version: number;
  new_version: number;
  reviewer_note: string | null;
  corrected_content: string | null;
  created_at: string;
}

export interface IntelligenceFinding {
  id: string;
  project_id: string;
  run_id: string | null;
  claim_id: string | null;
  category: string;
  title: string;
  content: string;
  confidence: number | null;
  verification_status: string;
  review_status: IntelligenceReviewStatus | string;
  reviewed: boolean;
  version: number;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_note: string | null;
  created_at: string;
  evidence: IntelligenceEvidence[];
  contradictions: IntelligenceContradiction[];
  review_history?: FindingReviewHistory[];
}

export type FindingReviewAction = "approve" | "reject" | "correct" | "request_clarification";

export interface IntelligenceChatResponse {
  conversation_id: string;
  message_id: string;
  answer: string;
  citations: string[];
  support: "evidence_backed" | "inference" | "insufficient_evidence" | string;
  context_version: string | null;
  provider: string | null;
  model: string | null;
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
    sourceIdentifier: source.source_id,
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
