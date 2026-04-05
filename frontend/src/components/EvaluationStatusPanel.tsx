import type { EvaluationDetailResponse, EvaluationStatus } from "../features/evaluations/types";

type EvaluationStatusPanelProps = {
  evaluationId?: string;
  evaluation?: EvaluationDetailResponse | null;
};

const STATUS_LABELS: Record<EvaluationStatus, string> = {
  pending: "评估准备中",
  running: "评估进行中",
  succeeded: "评估已完成",
  failed: "评估失败",
};

function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return "待更新";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function EvaluationStatusPanel({ evaluationId, evaluation }: EvaluationStatusPanelProps) {
  const currentEvaluationId = evaluation?.evaluation_id ?? evaluationId ?? "unknown";
  const statusLabel = evaluation ? `当前状态 · ${STATUS_LABELS[evaluation.status]}` : "状态加载中";

  return (
    <section className="detail-panel detail-status-panel">
      <p className="eyebrow">Requirements Evaluation Suite</p>
      <h1 className="page-title">需求评估结果</h1>
      <div className="detail-panel-heading detail-panel-heading-secondary">
        <div>
          <h2 className="detail-title">任务信息</h2>
          <p className="detail-copy">跟踪评估任务的执行状态与结果产出。</p>
        </div>
        <p className="detail-status-chip">{statusLabel}</p>
      </div>
      <dl className="detail-summary-grid">
        <div className="detail-summary-item">
          <dt>任务编号</dt>
          <dd>{currentEvaluationId}</dd>
        </div>
        <div className="detail-summary-item">
          <dt>评估文件</dt>
          <dd>{evaluation?.filename ?? "待获取"}</dd>
        </div>
        <div className="detail-summary-item">
          <dt>创建时间</dt>
          <dd>{formatDateTime(evaluation?.created_at)}</dd>
        </div>
        <div className="detail-summary-item">
          <dt>完成时间</dt>
          <dd>{formatDateTime(evaluation?.finished_at)}</dd>
        </div>
      </dl>
    </section>
  );
}
