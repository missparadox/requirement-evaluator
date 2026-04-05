import type { CreateEvaluationResponse, EvaluationDetailResponse } from "./types";
import { getJson, postForm } from "../../lib/http";

export function createEvaluation(file: File): Promise<CreateEvaluationResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return postForm<CreateEvaluationResponse>("/api/evaluations", formData);
}

export function getEvaluationDetail(evaluationId: string): Promise<EvaluationDetailResponse> {
  return getJson<EvaluationDetailResponse>(`/api/evaluations/${evaluationId}`);
}
