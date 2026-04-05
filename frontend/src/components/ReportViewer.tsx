type ReportViewerProps = {
  markdown: string;
  summary: string;
};


export function ReportViewer({ markdown, summary }: ReportViewerProps) {
  return (
    <section className="report-viewer">
      <article className="detail-panel result-section-card">
        <p className="eyebrow">Executive Summary</p>
        <h3 className="result-section-title">摘要结论</h3>
        <p className="detail-copy">{summary}</p>
      </article>
      <section className="detail-panel report-panel">
        <p className="eyebrow">Report</p>
        <h3 className="result-section-title">详细报告</h3>
        <pre className="report-content">{markdown}</pre>
      </section>
    </section>
  );
}
