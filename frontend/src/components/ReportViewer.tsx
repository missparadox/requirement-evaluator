type ReportViewerProps = {
  markdown: string;
};


export function ReportViewer({ markdown }: ReportViewerProps) {
  return (
    <section className="detail-panel report-panel">
      <p className="eyebrow">Report</p>
      <pre className="report-content">{markdown}</pre>
    </section>
  );
}
