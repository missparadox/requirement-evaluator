import { FormEvent, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { createEvaluation } from "../features/evaluations/api";

export function FileUploadForm() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!selectedFile) {
      setError("请选择待评估文件。");
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      const result = await createEvaluation(selectedFile);
      navigate(`/evaluations/${result.evaluation_id}`);
    } catch {
      setError("评估提交失败，请稍后重试。");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <label className="sr-only" htmlFor="requirements-file">
        评估文件上传
      </label>
      <div className="upload-file-row">
        <div className="upload-file-name">{selectedFile?.name ?? "请选择待评估文件"}</div>
        <button
          className="upload-secondary-button"
          type="button"
          onClick={() => {
            inputRef.current?.click();
          }}
        >
          选择文件
        </button>
        <input
          ref={inputRef}
          id="requirements-file"
          name="file"
          type="file"
          onChange={(event) => {
            const file = event.target.files?.[0] ?? null;
            setSelectedFile(file);
            setError(null);
          }}
        />
      </div>
      <p className="upload-help">
        支持 CSV、Excel 与 JSON 格式。文件提交后，平台将立即创建评估任务并启动处理流程。
      </p>
      <button className="upload-primary-button" type="submit" disabled={isSubmitting}>
        {isSubmitting ? "提交中..." : "开始评估"}
      </button>
      {error ? <p className="upload-error">{error}</p> : null}
    </form>
  );
}
