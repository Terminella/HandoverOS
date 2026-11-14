import { ArrowLeftRight, Check, Clock, TriangleAlert, AlertCircle, RefreshCw, Target, HelpCircle } from "lucide-react";
import { STATUS_LABEL } from "../../lib/labels";
import type { ItemStatus } from "../../lib/types";

const ICONS = {
  verified: Check,
  needs_verification: TriangleAlert,
  conflicting: ArrowLeftRight,
  pending: Clock,
  identified: Target,
  active: RefreshCw,
  resolved: Check,
  under_review: AlertCircle,
  unknown: HelpCircle,
} as const;

/** Status is always shown as icon + text, never colour alone. */
export default function StatusChip({ status }: { status: ItemStatus }) {
  const Icon = ICONS[status as keyof typeof ICONS];
  return (
    <span className={`chip chip-${status}`}>
      <Icon size={13} aria-hidden="true" />
      {STATUS_LABEL[status]}
    </span>
  );
}
