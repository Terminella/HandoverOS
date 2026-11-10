/**
 * SYNTHETIC DEMO DATA, not real project data.
 * Dev fallback used by the frontend until a backend API is available.
 * Components only depend on the types in ./types; replace these exports
 * with calls to the backend API when it is ready.
 */
import type { CurrentUser, Handover, KnowledgeItem, Project, Source, TeamMember } from "./types";

export const user: CurrentUser = { name: "Demo User", initials: "DU" };

export const projects: Project[] = [
  {
    id: "campusevents",
    name: "CampusEvents Platform",
    stage: "verify",
    visibleTo: "Project Team",
    draftVersion: "v0.2",
  },
];

export const sources: Source[] = [
  { id: "s1", name: "requirements.pdf", type: "document" },
  { id: "s2", name: "meeting_notes.pdf", type: "notes" },
  { id: "s3", name: "campusevents-portal", type: "repository" },
  { id: "s4", name: "deployment_log.txt", type: "document" },
  { id: "s5", name: "team_chat_export.json", type: "chat" },
  { id: "s6", name: "sprint_board.csv", type: "document" },
];

export const items: KnowledgeItem[] = [
  { id: "d1", kind: "decision", title: "Use Next.js for the new event portal.", summary: "Use Next.js for the new event portal.", status: "verified", sourceIds: ["s1", "s2"], reviewed: true },
  { id: "d2", kind: "decision", title: "Use PostgreSQL for event data.", summary: "Use PostgreSQL for event data.", status: "verified", sourceIds: ["s1"], reviewed: true },
  { id: "d3", kind: "decision", title: "Sign students in with college email.", summary: "Sign students in with college email.", status: "verified", sourceIds: ["s2", "s5"], reviewed: true },
  { id: "d4", kind: "decision", title: "Host the portal on Vercel.", summary: "Host the portal on Vercel.", status: "needs_verification", sourceIds: ["s5"], reviewed: false },
  { id: "t1", kind: "task", title: "Finish registration API.", summary: "Finish registration API.", status: "pending", sourceIds: ["s3"], reviewed: false },
  { id: "t2", kind: "task", title: "Add QR check-in.", summary: "Add QR check-in.", status: "pending", sourceIds: ["s6"], reviewed: false },
  { id: "t3", kind: "task", title: "Write organiser guide.", summary: "Write organiser guide.", status: "verified", sourceIds: ["s6"], reviewed: true },
  { id: "t4", kind: "task", title: "Set up email reminders.", summary: "Set up email reminders.", status: "needs_verification", sourceIds: ["s5"], reviewed: false },
  { id: "t5", kind: "task", title: "Load test the registration page.", summary: "Load test the registration page.", status: "pending", sourceIds: [], reviewed: false },
  { id: "b1", kind: "blocker", title: "Payment gateway credentials pending.", summary: "Payment gateway credentials pending.", status: "needs_verification", sourceIds: ["s5"], reviewed: false },
  { id: "b2", kind: "blocker", title: "Venue API rate limits unclear.", summary: "Venue API rate limits unclear.", status: "pending", sourceIds: ["s3"], reviewed: false },
  { id: "u1", kind: "unresolved", title: "Deployment status differs across sources.", summary: "Deployment status differs across sources.", status: "conflicting", sourceIds: ["s4", "s5"], reviewed: false },
  { id: "u2", kind: "unresolved", title: "Who owns the sponsor portal?", summary: "Who owns the sponsor portal?", status: "pending", sourceIds: [], reviewed: false },
  { id: "r1", kind: "risk", title: "Only one person knows the payment flow.", summary: "Only one person knows the payment flow.", status: "needs_verification", sourceIds: ["s2"], reviewed: false },
];

export const handovers: Handover[] = [
  {
    id: "h1",
    projectId: "campusevents",
    version: "v0.1",
    status: "draft",
    generatedAt: "2024-01-15T09:00:00Z",
    preparedBy: "Demo User",
  },
  {
    id: "h2",
    projectId: "campusevents",
    version: "v0.2",
    status: "pending_review",
    generatedAt: "2024-01-20T14:30:00Z",
    preparedBy: "Demo User",
  },
];

export const teamMembers: TeamMember[] = [
  { id: "u1", name: "Anway Basu", role: "Backend & API Development", initials: "AB" },
  { id: "u2", name: "Aryan Chirag", role: "Data Engineering & Integration", initials: "AC" },
  { id: "u3", name: "Soumallaya Mukherjee", role: "AI/LLM & Frontend Development", initials: "SM" },
  { id: "u4", name: "Achyut Roy", role: "Database, Security & DevOps", initials: "AR" },
];
