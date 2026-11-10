import type { ItemKind, ItemStatus, KnowledgeItem } from "./types";

export function pct(part: number, whole: number): number {
  return whole === 0 ? 0 : Math.round((part / whole) * 100);
}

export function countKind(items: KnowledgeItem[], kind: ItemKind): number {
  return items.filter((i) => i.kind === kind).length;
}

/**
 * Metric definitions (computed in one place so the numbers cannot disagree):
 *  - evidenceCoverage: share of items that cite at least one source
 *  - verified / needsVerification / conflicting / pending: item counts by status
 *  - readiness: share of items that are BOTH verified and reviewed by a person
 */
export function computeMetrics(items: KnowledgeItem[]) {
  const total = items.length;
  const count = (s: ItemStatus) => items.filter((i) => i.status === s).length;
  const withEvidence = items.filter((i) => i.sourceIds.length > 0).length;
  const verifiedAndReviewed = items.filter((i) => i.status === "verified" && i.reviewed).length;

  return {
    total,
    verified: count("verified"),
    needsVerification: count("needs_verification"),
    conflicting: count("conflicting"),
    pending: count("pending"),
    evidenceCoverage: pct(withEvidence, total),
    readiness: pct(verifiedAndReviewed, total),
  };
}
