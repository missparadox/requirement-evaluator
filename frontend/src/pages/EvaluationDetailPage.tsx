import { Link, useNavigate, useParams } from "react-router-dom";

import { EvaluationStatusPanel } from "../components/EvaluationStatusPanel";
import { ReportViewer } from "../components/ReportViewer";
import { useEvaluationDetail } from "../features/evaluations/hooks";
import { downloadMarkdown } from "../lib/download";

function getReportScore(markdown: string) {
  const match = markdown.match(/(?:总体评分|总分|score)\s*[:：]?\s*(\d{1,3})/i);

  return match?.[1] ?? "待解析";
}

function getReportSummary(markdown: string) {
  const lines = markdown
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0 && !line.startsWith("#"));

  return lines[0] ?? "结果摘要将随报告内容展示。";
}

function WaitingStateCard({ status }: { status: "pending" | "running" }) {
  const title = status === "pending" ? "评估准备中" : "评估进行中";
  const message =
    status === "pending"
      ? "评估任务已创建，系统正在准备分析所需内容。结果将自动刷新，请稍候。"
      : "平台正在基于当前文档执行结构化分析与模型评估，结果将在处理完成后自动同步至页面。";

  return (
    <section className="state-card waiting-card" aria-live="polite">
      <div className="state-card-mark" aria-hidden="true">
        ◌
      </div>
      <p className="state-card-label">Status</p>
      <h2 className="detail-card-title">{title}</h2>
      <p className="detail-copy">{message}</p>
      <div className="refresh-inline-card">
        <div className="refresh-circle">20s</div>
        <div>
          <p className="refresh-inline-title">状态刷新</p>
          <p>系统将在 20 秒后刷新最新状态</p>
        </div>
      </div>
    </section>
  );
}

function FailedStateCard({
  errorMessage,
  onRetry,
}: {
  errorMessage: string;
  onRetry: () => void;
}) {
  return (
    <section className="state-card failed-card" aria-live="polite">
      <div className="state-card-mark" aria-hidden="true">
        !
      </div>
      <p className="state-card-label">Status</p>
      <h2 className="detail-card-title">评估失败</h2>
      <p className="detail-copy">
        当前评估任务未能完成结果生成。你可以重新发起评估，或返回首页重新提交文档。
      </p>
      <div className="error-block">
        <p className="error-block-label">异常说明</p>
        <p>{errorMessage}</p>
      </div>
      <div className="detail-card-actions">
        <button className="upload-primary-button" type="button" onClick={onRetry}>
          重新发起评估
        </button>
        <Link className="detail-link" to="/">
          返回首页
        </Link>
      </div>
    </section>
  );
}

function SucceededState({ evaluationId, markdown }: { evaluationId: string; markdown: string }) {
  const reportScore = getReportScore(markdown);
  const reportSummary = getReportSummary(markdown);

  return (
    <>
      <section className="detail-panel conclusion-hero-card">
        <div className="conclusion-hero-header">
          <div>
            <p className="eyebrow">Overall Assessment</p>
            <h2 className="detail-card-title">评估已完成</h2>
          </div>
          <button
            className="upload-primary-button"
            type="button"
            onClick={() => downloadMarkdown(`${evaluationId}.md`, markdown)}
          >
            下载评估报告
          </button>
        </div>
        <p className="detail-copy">
          系统已完成当前文档的结构化评估，以下为本次任务的结果摘要。
        </p>
      </section>
      <section className="result-side-cards">
        <article className="detail-panel result-metric-card">
          <p>总体评分</p>
          <strong>{reportScore}</strong>
        </article>
        <article className="detail-panel result-metric-card">
          <p>摘要结论</p>
          <strong>{reportSummary}</strong>
        </article>
      </section>
      <ReportViewer markdown={markdown} summary={reportSummary} />
    </>
  );
}

export function EvaluationDetailPage() {
  const { evaluationId } = useParams();
  const navigate = useNavigate();
  const evaluationDetailQuery = useEvaluationDetail(evaluationId);
  const evaluation = evaluationDetailQuery.data;
  const markdown =
    evaluation?.report_markdown ?? `# Evaluation ${evaluationId ?? "unknown"}\n\nReport pending.`;

  if (evaluationDetailQuery.isError) {
    const errorMessage =
      evaluationDetailQuery.error instanceof Error
        ? evaluationDetailQuery.error.message
        : "评估状态获取失败，请稍后重试。";

    return (
      <main className="detail-shell">
        <FailedStateCard errorMessage={errorMessage} onRetry={() => navigate("/")} />
      </main>
    );
  }

  const renderStateCard = () => {
    if (!evaluation || evaluation.status === "pending") {
      return <WaitingStateCard status="pending" />;
    }

    if (evaluation.status === "running") {
      return <WaitingStateCard status="running" />;
    }

    if (evaluation.status === "failed") {
      return (
        <FailedStateCard
          errorMessage={evaluation.error_message ?? "评估执行失败，请重新发起任务。"}
          onRetry={() => navigate("/")}
        />
      );
    }

    return <SucceededState evaluationId={evaluationId ?? "evaluation"} markdown={markdown} />;
  };

  return (
    <main className="detail-shell">
      <EvaluationStatusPanel evaluationId={evaluationId} evaluation={evaluation ?? null} />
      {renderStateCard()}
    </main>
  );
}
