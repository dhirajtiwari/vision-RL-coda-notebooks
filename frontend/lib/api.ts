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
    const q = fmId ? `&failure_mode_id=${encodeURIComponent(fmId)}` : "";
    return fetchJson<any>(
      `/graph/diagnosis-subgraph?product_id=${encodeURIComponent(productId)}&symptom_ids=${encodeURIComponent(sym)}${q}`,
    );
  },

  /** W3C OWL TBox (schema-only Turtle) */
  getRdfSchema: () => fetchJson<any>("/graph/rdf/schema"),

  /** Full product diagram as Turtle (TBox optional + ABox) */
  getRdfProduct: (productId: string, includeSchema = true) =>
    fetchJson<any>(
      `/graph/rdf/product/${encodeURIComponent(productId)}?include_schema=${includeSchema}`,
    ),

  /** OWL class + RDF instance for one Neo4j node (Explorer click) */
  getRdfEntity: (label: string, entityId: string, productId?: string) => {
    const q = new URLSearchParams({ label, entity_id: entityId });
    if (productId) q.set("product_id", productId);
    return fetchJson<any>(`/graph/rdf/entity?${q}`);
  },

  listProducts: () => fetchJson<any>("/products"),

  /** Asset-first CRM session */
  listCustomers: () => fetchJson<{ customers: any[] }>("/crm/customers"),
  listCustomerAssets: (customerId: string) =>
    fetchJson<{ customer: any; registered_assets: any[]; source_system?: string }>(
      `/crm/customers/${encodeURIComponent(customerId)}/assets`,
    ),
  getCrmAsset: (assetId: string) => fetchJson<any>(`/crm/assets/${encodeURIComponent(assetId)}`),

  // ── Study Lab ────────────────────────────────────────────────────────────
  studyModules: () => fetchJson<{ modules: any[] }>("/study/modules"),
  studyModule: (id: string) => fetchJson<any>(`/study/modules/${encodeURIComponent(id)}`),
  studyGenerate: (body: { title?: string; tags?: string[]; text: string; filename?: string }) =>
    fetchJson<any>("/study/modules/generate", { method: "POST", body: JSON.stringify(body) }),
  studyUpload: async (file: File, title = "", tags = "") => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("title", title);
    fd.append("tags", tags);
    const res = await fetch(`${API_BASE}/study/modules/upload`, { method: "POST", body: fd });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  studyGradeFill: (body: { module_id: string; beat_id: string; answers: Record<string, string> }) =>
    fetchJson<any>("/study/grade/fill-blanks", { method: "POST", body: JSON.stringify(body) }),
  studyGradeLine: (body: { module_id: string; beat_id: string; line: number; choice: string }) =>
    fetchJson<any>("/study/grade/line-quiz", { method: "POST", body: JSON.stringify(body) }),
  studyProgressGet: (clientKey = "local") =>
    fetchJson<any>(`/study/progress/${encodeURIComponent(clientKey)}`),
  studyProgressSave: (body: any, clientKey = "local") =>
    fetchJson<any>(`/study/progress?client_key=${encodeURIComponent(clientKey)}`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  studyReseed: () => fetchJson<any>("/study/reseed", { method: "POST" }),
};
