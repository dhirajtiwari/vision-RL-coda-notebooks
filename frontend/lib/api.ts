const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  health: () => fetchJson<any>("/health"),

  diagnose: (body: any) =>
    fetchJson<any>("/diagnose", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  listClaims: (limit = 30) => fetchJson<any>(`/claims?limit=${limit}`),

  submitClaim: (body: any) =>
    fetchJson<any>("/claims/submit", { method: "POST", body: JSON.stringify(body) }),

  updateClaimStatus: (claimId: string, status: string, agent_notes = "") =>
    fetchJson<any>(`/claims/${claimId}/status?status=${status}&agent_notes=${encodeURIComponent(agent_notes)}`, {
      method: "PATCH",
    }),

  listBatches: (limit = 12) => fetchJson<any>(`/lineage/batches?limit=${limit}`),

  integrationsStatus: () => fetchJson<any>("/integrations/status"),

  getOntology: () => fetchJson<any>("/graph/ontology"),

  getProductGraph: (productId: string) =>
    fetchJson<any>(`/graph/product/${productId}`),

  getDiagnosisSubgraph: (productId: string, symptomIds: string[] = [], fmId?: string) => {
    const sym = symptomIds.join(",");
    const q = fmId ? `&failure_mode_id=${fmId}` : "";
    return fetchJson<any>(`/graph/diagnosis-subgraph?product_id=${productId}&symptom_ids=${sym}${q}`);
  },

  listProducts: () => fetchJson<any>("/products"),
};
