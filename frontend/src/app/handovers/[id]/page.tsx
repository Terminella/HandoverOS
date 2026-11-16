"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft, CalendarDays, CheckCircle2, Clock3, FileText,
  FolderKanban, ShieldCheck, UserRound, AlertCircle, ExternalLink, Layers3,
} from "lucide-react";
import { apiRequest, getStoredToken } from "../../../lib/api";

type HandoverItem = {
  id: string;
  section: string;
  content: string;
  position: number;
  knowledgeItem: {
    id: string;
    title: string;
    type: string;
    confidence: number | null;
    reviewed: boolean;
  } | null;
  evidence: {
    id: string;
    name: string;
    title: string | null;
    type: string;
    url: string | null;
  } | null;
};

type Approval = {
  reviewer: string;
  status: string;
  comments: string | null;
  reviewedAt: string | null;
};

type HandoverDetail = {
  id: string;
  projectId: string;
  projectName: string | null;
  version: string;
  status: string;
  generatedAt: string | null;
  preparedBy: string;
  items: HandoverItem[];
  approvals: Approval[];
};

function formatDate(value: string | null | undefined) {
  if (!value) return "Date unavailable";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
}

function readable(value: string | null | undefined) {
  if (!value) return "Uncategorized";
  return value.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function statusClass(status: string) {
  const normalized = status.toLowerCase();
  if (normalized === "approved" || normalized === "verified") return "good";
  if (normalized === "rejected" || normalized === "contradicted") return "bad";
  return "pending";
}

export default function HandoverDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const handoverId = params?.id;
  const [detail, setDetail] = useState<HandoverDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!handoverId) return;
    let active = true;

    async function loadHandover() {
      setLoading(true);
      setError(null);
      try {
        const token = getStoredToken() ?? undefined;
        const response = await apiRequest<HandoverDetail>(
          `/handovers/${encodeURIComponent(handoverId)}/detail`,
          token
        );
        if (active) setDetail(response);
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "Unable to load this handover.");
      } finally {
        if (active) setLoading(false);
      }
    }

    loadHandover();
    return () => { active = false; };
  }, [handoverId]);

  return (
    <main className="handover-detail-page">
      <style jsx global>{`
        .handover-detail-page {
          --hd-border: var(--border, rgba(148,163,184,.2));
          --hd-muted: var(--muted, #94a3b8);
          width: 100%; max-width: 1120px; margin: 0 auto; padding: 24px;
        }
        .hd-back { display:inline-flex; align-items:center; gap:9px; border:1px solid var(--hd-border); border-radius:10px; padding:9px 13px; background:transparent; color:inherit; cursor:pointer; font:inherit; }
        .hd-back:hover { border-color:#7c8cff; }
        .hd-hero { margin-top:22px; padding:28px; border:1px solid var(--hd-border); border-radius:18px; background:linear-gradient(135deg,rgba(99,102,241,.12),rgba(14,165,233,.05)); }
        .hd-eyebrow { display:flex; align-items:center; gap:8px; color:var(--hd-muted); font-size:12px; font-weight:700; letter-spacing:.11em; text-transform:uppercase; }
        .hd-title-row { display:flex; justify-content:space-between; align-items:flex-start; gap:20px; flex-wrap:wrap; margin-top:12px; }
        .hd-title { margin:0; font-size:clamp(27px,4vw,38px); line-height:1.15; }
        .hd-subtitle { margin:9px 0 0; color:var(--hd-muted); }
        .hd-badge { display:inline-flex; align-items:center; gap:7px; border-radius:999px; padding:8px 13px; font-size:12px; font-weight:750; text-transform:capitalize; border:1px solid transparent; }
        .hd-badge.good { color:#16a36a; background:rgba(22,163,106,.1); border-color:rgba(22,163,106,.25); }
        .hd-badge.bad { color:#ef6262; background:rgba(239,98,98,.1); border-color:rgba(239,98,98,.25); }
        .hd-badge.pending { color:#d69a27; background:rgba(214,154,39,.1); border-color:rgba(214,154,39,.25); }
        .hd-meta-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin-top:25px; }
        .hd-meta { display:flex; align-items:center; gap:11px; min-width:0; padding:13px; border:1px solid var(--hd-border); border-radius:12px; background:rgba(15,23,42,.025); }
        .hd-meta-icon { display:grid; place-items:center; width:34px; height:34px; flex:0 0 34px; border-radius:10px; background:rgba(99,102,241,.12); color:#818cf8; }
        .hd-meta-label { color:var(--hd-muted); font-size:11px; }
        .hd-meta-value { overflow-wrap:anywhere; margin-top:3px; font-size:13px; font-weight:650; }
        .hd-section { margin-top:24px; padding:22px; border:1px solid var(--hd-border); border-radius:16px; background:var(--card,transparent); }
        .hd-section-head { display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:17px; }
        .hd-section-title { display:flex; align-items:center; gap:9px; margin:0; font-size:17px; }
        .hd-count { color:var(--hd-muted); font-size:12px; }
        .hd-items,.hd-approval-list { display:grid; gap:12px; }
        .hd-item { padding:17px; border:1px solid var(--hd-border); border-radius:13px; }
        .hd-item-top { display:flex; justify-content:space-between; gap:12px; align-items:center; flex-wrap:wrap; }
        .hd-item-type { color:#818cf8; font-size:11px; font-weight:750; letter-spacing:.07em; text-transform:uppercase; }
        .hd-item-title { margin:7px 0 8px; font-size:14px; font-weight:700; }
        .hd-item-content { margin:0; color:var(--hd-muted); font-size:13px; line-height:1.7; white-space:pre-wrap; overflow-wrap:anywhere; }
        .hd-evidence { display:flex; align-items:flex-start; gap:9px; margin-top:14px; padding:11px 12px; border-radius:10px; background:rgba(99,102,241,.07); font-size:12px; }
        .hd-evidence a { color:#818cf8; text-decoration:none; }
        .hd-evidence a:hover { text-decoration:underline; }
        .hd-approval { display:flex; align-items:flex-start; gap:12px; padding:14px; border:1px solid var(--hd-border); border-radius:12px; }
        .hd-approval-icon { color:#16a36a; }
        .hd-approval-name { font-size:13px; font-weight:700; }
        .hd-approval-meta { margin-top:4px; color:var(--hd-muted); font-size:12px; }
        .hd-approval-comment { margin:9px 0 0; font-size:13px; line-height:1.6; }
        .hd-empty,.hd-state { padding:36px 20px; text-align:center; color:var(--hd-muted); }
        .hd-state h1 { color:inherit; font-size:22px; }
        .hd-error { color:#ef6262; }
        @media(max-width:700px) { .handover-detail-page{padding:14px}.hd-hero,.hd-section{padding:18px}.hd-meta-grid{grid-template-columns:1fr} }
      `}</style>

      <button className="hd-back" type="button" onClick={() => router.push("/handovers")}>
        <ArrowLeft size={16} /> Back to handovers
      </button>

      {loading ? (
        <section className="hd-section hd-state" role="status">
          <Clock3 size={25} /><h1>Loading handover…</h1>
          <p>Retrieving the handover record and supporting evidence.</p>
        </section>
      ) : error ? (
        <section className="hd-section hd-state hd-error" role="alert">
          <AlertCircle size={28} /><h1>Unable to load handover</h1><p>{error}</p>
          <button className="hd-back" type="button" onClick={() => router.refresh()}>Try again</button>
        </section>
      ) : detail ? (
        <>
          <section className="hd-hero">
            <div className="hd-eyebrow"><FileText size={15} /> Handover record · {detail.version}</div>
            <div className="hd-title-row">
              <div>
                <h1 className="hd-title">{detail.projectName || "Project handover"}</h1>
                <p className="hd-subtitle">Version {detail.version.replace(/^v/i, "")} · Generated handover snapshot</p>
              </div>
              <span className={`hd-badge ${statusClass(detail.status)}`}>
                {detail.status === "approved" ? <CheckCircle2 size={14} /> : <Clock3 size={14} />}
                {readable(detail.status)}
              </span>
            </div>
            <div className="hd-meta-grid">
              <div className="hd-meta"><span className="hd-meta-icon"><FolderKanban size={17} /></span><div><div className="hd-meta-label">Project</div><div className="hd-meta-value">{detail.projectName || detail.projectId}</div></div></div>
              <div className="hd-meta"><span className="hd-meta-icon"><UserRound size={17} /></span><div><div className="hd-meta-label">Prepared by</div><div className="hd-meta-value">{detail.preparedBy || "Unknown"}</div></div></div>
              <div className="hd-meta"><span className="hd-meta-icon"><CalendarDays size={17} /></span><div><div className="hd-meta-label">Generated</div><div className="hd-meta-value">{formatDate(detail.generatedAt)}</div></div></div>
            </div>
          </section>

          <section className="hd-section">
            <div className="hd-section-head"><h2 className="hd-section-title"><Layers3 size={18} /> Knowledge snapshot</h2><span className="hd-count">{detail.items.length} items</span></div>
            {detail.items.length === 0 ? <div className="hd-empty">No knowledge items were included in this handover.</div> : (
              <div className="hd-items">
                {detail.items.map((item, index) => (
                  <article className="hd-item" key={item.id}>
                    <div className="hd-item-top"><span className="hd-item-type">{readable(item.section)}</span><span className="hd-count">Item {index + 1}</span></div>
                    {item.knowledgeItem?.title ? <h3 className="hd-item-title">{item.knowledgeItem.title}</h3> : null}
                    <p className="hd-item-content">{item.content}</p>
                    {item.evidence ? (
                      <div className="hd-evidence"><FileText size={15} /><div><strong>Source: </strong>
                        {item.evidence.url ? <a href={item.evidence.url} target="_blank" rel="noreferrer">{item.evidence.title || item.evidence.name} <ExternalLink size={11} style={{display:"inline",marginLeft:4}} /></a> : <span>{item.evidence.title || item.evidence.name}</span>}
                        <div className="hd-count">{readable(item.evidence.type)}{item.knowledgeItem?.confidence != null ? ` · Confidence: ${Math.round(item.knowledgeItem.confidence * 100)}%` : ""}</div>
                      </div></div>
                    ) : null}
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="hd-section">
            <div className="hd-section-head"><h2 className="hd-section-title"><ShieldCheck size={18} /> Approval history</h2><span className="hd-count">{detail.approvals.length} records</span></div>
            {detail.approvals.length === 0 ? <div className="hd-empty">No approval activity has been recorded.</div> : (
              <div className="hd-approval-list">
                {detail.approvals.map((approval, index) => (
                  <article className="hd-approval" key={`${approval.reviewer}-${approval.reviewedAt || index}`}>
                    <span className="hd-approval-icon"><CheckCircle2 size={19} /></span>
                    <div><div className="hd-approval-name">{approval.reviewer}</div><div className="hd-approval-meta">{readable(approval.status)} · {formatDate(approval.reviewedAt)}</div>
                      {approval.comments ? <p className="hd-approval-comment">{approval.comments}</p> : null}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      ) : null}
    </main>
  );
}
