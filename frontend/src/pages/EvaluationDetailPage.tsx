import { useParams } from "react-router-dom";

import { EvaluationStatusPanel } from "../components/EvaluationStatusPanel";
import { ReportViewer } from "../components/ReportViewer";
import { downloadMarkdown } from "../lib/download";


export function EvaluationDetailPage() {
  const { evaluationId } = useParams();
  const markdown = `# Evaluation ${evaluationId ?? "unknown"}\n\nReport pending.`;

  return (
    <main className="detail-shell">
      <EvaluationStatusPanel evaluationId={evaluationId} />
      <div className="detail-actions">
        <button
          className="upload-button"
          type="button"
          onClick={() => downloadMarkdown(`${evaluationId ?? "evaluation"}.md`, markdown)}
        >
          Download Markdown
        </button>
      </div>
      <ReportViewer markdown={markdown} />
    </main>
  );
}
