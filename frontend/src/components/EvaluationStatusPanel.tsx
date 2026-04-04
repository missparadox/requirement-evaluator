type EvaluationStatusPanelProps = {
  evaluationId?: string;
};


export function EvaluationStatusPanel({ evaluationId }: EvaluationStatusPanelProps) {
  return (
    <section className="detail-panel">
      <p className="eyebrow">Evaluation</p>
      <h1>Evaluation Status</h1>
      <p className="detail-copy">Tracking evaluation {evaluationId ?? "unknown"}.</p>
      <p className="detail-status">Current status: pending</p>
    </section>
  );
}
