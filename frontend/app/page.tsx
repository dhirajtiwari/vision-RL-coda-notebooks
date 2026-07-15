"use client";

import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  MessageCircle, Users, GitBranch, Activity, FileText, Send, RefreshCw,
  ChevronRight, ChevronDown, Shield, Zap, AlertTriangle, Database, HelpCircle, FolderOpen, Eye,
  Maximize2, ZoomIn, ZoomOut, Search, Crosshair, Layers, CheckCircle2, Circle, ListOrdered,
  PackagePlus, Play, ClipboardCheck, Rocket, GraduationCap
} from 'lucide-react';
import Link from 'next/link';
import { AnimatePresence } from 'framer-motion';
import { api } from '../lib/api';
import type { DiagnoseResponse } from '../lib/types';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ReactFlow, Background, Controls, MiniMap, Node, Edge, Panel } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';
import { toast } from 'sonner';

// 2026 Modern Enterprise Diagnostics UI — Glass + AI-Native + Data-First

type View = 'chat' | 'cases' | 'explorer' | 'ops' | 'admin';
type Role = 'customer' | 'agent' | 'analyst';

/** Full ontology neighborhood for a product (true Neo4j subgraph types) */
const FULL_ONTOLOGY_TYPES = [
  'Product', 'Symptom', 'FailureMode', 'DiagnosticStep', 'Part', 'Component',
  'ErrorCode', 'HistoricalResolution', 'Resolution', 'Model', 'SKU', 'Asset',
  'WarrantyPolicy', 'Claim',
] as const;

/**
 * Persona presets for the explorer — optional density filters, NOT a hard wall.
 * Default explorer mode is **full ontology** so parts/steps/policies always appear.
 */
const PERSONA_NODE_TYPES: Record<Role, string[]> = {
  customer: ['Product', 'Symptom', 'FailureMode', 'DiagnosticStep', 'Part', 'ErrorCode'],
  agent: [
    'Product', 'Symptom', 'FailureMode', 'Part', 'DiagnosticStep', 'ErrorCode',
    'Component', 'HistoricalResolution', 'Asset', 'WarrantyPolicy',
  ],
  analyst: [...FULL_ONTOLOGY_TYPES],
};

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  diagnosis?: DiagnoseResponse['diagnosis'];
  full?: DiagnoseResponse;
}

// ─────────────────────────────────────────────────────────────────────────────
// Pure highlight overlay — separated from layout so layout is stable.
// Uses node.className for opacity state (ReactFlow theming docs pattern) and
// inline boxShadow only for the dynamic-color path-node glow.
// ─────────────────────────────────────────────────────────────────────────────
function edgeOnDiagnosisPath(
  edge: Edge,
  hEdges: Set<string>,
): boolean {
  if (hEdges.has(edge.id)) return true;
  // API may use source|TYPE|target or source|target — accept either
  if (hEdges.has(`${edge.source}|${edge.target}`)) return true;
  if (hEdges.has(`${edge.target}|${edge.source}`)) return true;
  for (const he of hEdges) {
    if (he.includes(edge.source) && he.includes(edge.target)) return true;
  }
  return false;
}

function applyHighlight(
  baseNodes: Node[],
  baseEdges: Edge[],
  highlight: { nodes: string[]; edges: string[] } | null,
): { nodes: Node[]; edges: Edge[] } {
  const hNodes = new Set(highlight?.nodes ?? []);
  const hEdges = new Set(highlight?.edges ?? []);
  const hasH = hNodes.size > 0;

  const nodes = baseNodes.map(n => {
    if (!hasH) return { ...n, className: undefined, zIndex: 2 };
    // Match exact id or suffix entity id (Symptom:wm-s01 / wm-s01)
    const onPath =
      hNodes.has(n.id) ||
      hNodes.has(String((n.data as any)?.raw?.entity_id || '')) ||
      [...hNodes].some((hid) => hid === n.id || hid.endsWith(`:${n.id}`) || n.id.endsWith(`:${hid}`) || n.id.includes(hid));
    const col: string = (n.data as any).typeColor ?? '#64748b';
    return {
      ...n,
      className: onPath ? 'node-on-path' : 'node-off-path',
      zIndex: onPath ? 20 : 1,
      style: {
        ...n.style,
        // Dynamic-color glow must stay inline; CSS class handles opacity.
        boxShadow: onPath
          ? `0 0 0 4px ${col}55, 0 0 22px ${col}44, 0 4px 12px rgba(0,0,0,0.45)`
          : undefined,
        opacity: onPath ? 1 : 0.28,
      },
    };
  });

  const edges = baseEdges.map(e => {
    if (!hasH) return e;
    const onPath = edgeOnDiagnosisPath(e, hEdges);
    return {
      ...e,
      animated: onPath,
      style: onPath
        ? { stroke: '#10b981', strokeWidth: 3, filter: 'drop-shadow(0 0 5px rgba(16,185,129,0.8))' }
        : { stroke: 'rgba(100,116,139,0.12)', strokeWidth: 1 },
      labelStyle: onPath
        ? { fill: '#6ee7b7', fontSize: 10, fontWeight: 700 }
        : { fill: 'transparent', fontSize: 0 },
      labelBgStyle: onPath
        ? { fill: '#064e3b', rx: 4, ry: 4, fillOpacity: 0.9 }
        : { fillOpacity: 0 },
    };
  });

  return { nodes, edges };
}

/** Hover / focus tooltip with numbered steps (Admin Control Room). */
function HelpTip({
  title,
  steps,
  where,
  align = 'left',
}: {
  title: string;
  steps: string[];
  where?: string;
  align?: 'left' | 'right';
}) {
  return (
    <span className="help-tip" tabIndex={0} aria-label={`Help: ${title}`}>
      <span className="help-tip-trigger" aria-hidden>
        <HelpCircle className="w-3 h-3" />
      </span>
      <span className={`help-tip-panel ${align === 'right' ? 'help-tip-right' : ''}`} role="tooltip">
        <div className="help-tip-title">{title}</div>
        <ol>
          {steps.map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ol>
        {where ? <div className="help-tip-where">Writes / reads: {where}</div> : null}
      </span>
    </span>
  );
}

/** Step tooltips for classic admin gates + KG pipelines. */
const ADMIN_ACTION_TIPS: Record<string, { title: string; steps: string[]; where: string }> = {
  onboard: {
    title: 'Add to Staging Catalog',
    steps: [
      'POST product_id, name, family to /admin/onboard-product',
      'Product is staged for the next ETL/review cycle (not live diagnosis yet)',
      'Refresh Review to see staged product counts',
    ],
    where: 'API staging / catalog path (not Neo4j until Promote)',
  },
  dry_run: {
    title: 'Dry-Run ETL (Fetch & Preview)',
    steps: [
      'Call enterprise connectors (PIM/CRM/FSM/Claims) or fixtures',
      'Build a lineage preview with record counts — no Neo4j MERGE',
      'LAST LINEAGE card updates for human review',
    ],
    where: 'Review state + data/lineage (preview); graph untouched',
  },
  smoke: {
    title: 'Run Smoke Validation',
    steps: [
      'Run canned diagnosis scenarios against the current knowledge base',
      'Set Smoke OK = true only if scenarios pass',
      'Required before classic PROMOTE is unlocked',
    ],
    where: 'In-memory review gate + diagnosis against Neo4j production',
  },
  refresh_review: {
    title: 'Refresh Review',
    steps: ['Reload staged change summary and smoke/approval flags from the API'],
    where: 'GET /admin/pipeline/review',
  },
  approve: {
    title: 'Approve Changes (Human Gate)',
    steps: [
      'Operator asserts they reviewed source counts / new products',
      'Sets Human Reviewed = true (change-control gate)',
      'Together with Smoke OK unlocks PROMOTE',
    ],
    where: 'In-memory ADMIN_REVIEW_STATE (demo; production would be signed audit)',
  },
  promote_classic: {
    title: 'PROMOTE to Live Knowledge Base',
    steps: [
      'Blocked unless Smoke OK and Human Reviewed',
      'MERGE enterprise catalog into production Neo4j (:7687)',
      'Invalidate caches so diagnose/explorer see new data',
      'Reset approval gate after success',
    ],
    where: 'Neo4j production · Redis caches cleared',
  },
  bootstrap_all: {
    title: 'bootstrap_all (first-time chain)',
    steps: [
      'structured_extract → semi_structured_ingest → unstructured_extract',
      'preprocess_normalize (dedupe / quality)',
      'knowledge_materialize (catalog JSON)',
      'smoke_validate (scenarios)',
      'Does NOT auto-promote to Neo4j — run Promote graph after review',
    ],
    where: 'data/pipeline_staging/* · data/lineage/pipeline_runs/* · catalog JSON',
  },
  incremental_sync: {
    title: 'incremental_sync (live deltas)',
    steps: [
      'Read files under semi_structured/incremental/ (+ structured APIs)',
      'preprocess → materialize catalog updates',
      'No auto-promote — operator promotes after smoke/review',
    ],
    where: 'data/pipeline_sources/**/incremental · staging JSON · catalog',
  },
  promote_graph: {
    title: 'Promote graph',
    steps: [
      'Load data/enterprise_knowledge_catalog.json',
      'MERGE into Target env (staging :7688 or production :7687)',
      'Invalidate ontology / subgraph / diagnose caches',
      'Prefer staging first, then production after smoke',
    ],
    where: 'Neo4j target_env · Redis cache invalidate',
  },
  structured_extract: {
    title: 'structured_extract',
    steps: [
      'Pull PIM/CRM/FSM/Claims via connectors or enterprise fixtures',
      'Summarize record counts into a staging JSON artifact',
      'Dry-run skips hard catalog write where supported',
    ],
    where: 'data/pipeline_staging/*-structured.json · enterprise connectors',
  },
  semi_structured_ingest: {
    title: 'semi_structured_ingest',
    steps: [
      'Scan data/pipeline_sources/semi_structured/{mode}/*.csv|jsonl',
      'Schema-on-read normalize rows (product_id, parts, work orders)',
      'Write *-semi.json staging artifact',
    ],
    where: 'data/pipeline_sources/semi_structured/** → data/pipeline_staging/*-semi.json',
  },
  unstructured_extract: {
    title: 'unstructured_extract',
    steps: [
      'Read manuals/tickets under unstructured/bootstrap (txt/md)',
      'Regex/heuristic extract provisional symptoms & error codes',
      'Write *-unstructured.json (provisional — not full ontology merge)',
    ],
    where: 'data/pipeline_sources/unstructured/** → data/pipeline_staging/*-unstructured.json',
  },
  preprocess_normalize: {
    title: 'preprocess_normalize',
    steps: [
      'Load latest semi + unstructured (+ structured) staging bundles',
      'Validate required fields, dedupe, quality score',
      'Write *-preprocessed.json quality report',
    ],
    where: 'data/pipeline_staging/*-preprocessed.json',
  },
  knowledge_materialize: {
    title: 'knowledge_materialize',
    steps: [
      'Run OntologyBuilder / knowledge ETL into enterprise catalog',
      'Optionally annotate catalog with pipeline_ingest metadata',
      'Catalog is what Promote MERGEs into Neo4j',
    ],
    where: 'data/enterprise_knowledge_catalog.json',
  },
  smoke_validate: {
    title: 'smoke_validate',
    steps: [
      'Run enterprise diagnosis scenarios',
      'Fail closed if scenarios break (blocks safe promote practice)',
      'Skipped when Dry-run is checked',
    ],
    where: 'lineage run report · review Smoke OK flag',
  },
  refresh_inventory: {
    title: 'Refresh source inventory',
    steps: [
      'List files under pipeline_sources (and enterprise fixtures)',
      'Parse samples (JSONL/CSV headers/txt snippets) without running pipelines',
      'Populate on-screen inventory so you can add files then re-scan',
    ],
    where: 'GET /admin/kg-pipelines/sources/inventory (read-only)',
  },
};

export default function WarrantyGraphModern() {
  const [activeView, setActiveView] = useState<View>('chat');
  const [role, setRole] = useState<Role>('customer');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Select the customer and their registered appliance, then describe the issue. Diagnosis is scoped to that product in the knowledge graph — with warranty from the asset."
    }
  ]);
  const [input, setInput] = useState('');
  /** Customer session (default) vs anonymous demo (product pick / text detect only). */
  const [sessionMode, setSessionMode] = useState<'customer' | 'anonymous'>('customer');
  const [selectedCustomerId, setSelectedCustomerId] = useState('CUST-10042');
  const [customerAssets, setCustomerAssets] = useState<any[]>([]);
  const [selectedAssetRecord, setSelectedAssetRecord] = useState<any | null>(null);
  /** Collapse bulky appliance grid after pick so chat + composer stay visible */
  const [assetPickerExpanded, setAssetPickerExpanded] = useState(true);
  /** Anonymous mode only — product pick (not used when asset is bound). */
  const [anonymousProductId, setAnonymousProductId] = useState('wm-001');
  const [pendingMismatch, setPendingMismatch] = useState<{
    message: string;
    diagnosis: any;
    full: any;
  } | null>(null);
  const [currentDiagnosis, setCurrentDiagnosis] = useState<any>(null);
  const [isListening, setIsListening] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const chatMessagesEndRef = useRef<HTMLDivElement | null>(null);
  const chatMessagesScrollRef = useRef<HTMLDivElement | null>(null);
  // Chat product scope (derived) + independent explorer product picker
  const chatProductId =
    sessionMode === 'customer'
      ? (selectedAssetRecord?.product_id || 'wm-001')
      : anonymousProductId;
  const [explorerProductId, setExplorerProductId] = useState('wm-001');
  const selectedProduct = activeView === 'explorer' ? explorerProductId : chatProductId;

  // Admin state
  const [adminStatus, setAdminStatus] = useState<any>(null);
  const [onboardForm, setOnboardForm] = useState({ product_id: 'new-wm-2026', name: 'New Front-Load Washer 2026', family: 'washer' });
  const [kgPipelines, setKgPipelines] = useState<any[]>([]);
  const [kgRuns, setKgRuns] = useState<any[]>([]);
  const [kgArtifacts, setKgArtifacts] = useState<any>(null);
  const [lastKgRun, setLastKgRun] = useState<any>(null);
  const [kgRunBusy, setKgRunBusy] = useState(false);
  const [kgMode, setKgMode] = useState<'bootstrap' | 'incremental' | 'on_demand'>('on_demand');
  /** Default false so Materialize actually writes catalog (dry-run looked like a no-op). */
  const [kgDryRun, setKgDryRun] = useState(false);
  const [kgTargetEnv, setKgTargetEnv] = useState<'staging' | 'production'>('staging');
  /** Last promote outcome — used to disable the promote button after success for same scope+target */
  const [promoteResult, setPromoteResult] = useState<{
    ok: boolean;
    target: 'staging' | 'production';
    productIds: string[];
    scopeKey: string;
    message: string;
    at: string;
    runId?: string | null;
  } | null>(null);
  const [promoteBusy, setPromoteBusy] = useState(false);
  const [kgInventory, setKgInventory] = useState<any>(null);
  const [kgInventoryBusy, setKgInventoryBusy] = useState(false);
  const [selectedSourcePath, setSelectedSourcePath] = useState<string | null>(null);
  const [sourcePreview, setSourcePreview] = useState<any>(null);
  /** Guided onboarding: change-set vs live graph + step progress */
  const [changePreview, setChangePreview] = useState<any>(null);
  const [adminJourney, setAdminJourney] = useState<any[]>([]);
  const [adminWizardStep, setAdminWizardStep] = useState(1);
  /** Steps explicitly completed in the strict wizard (in addition to derived gates) */
  const [wizardStepDone, setWizardStepDone] = useState<Record<number, boolean>>({});
  /** Locked product scope after step 3 — survives change-preview refresh clearing checkboxes */
  const [lockedSelectionIds, setLockedSelectionIds] = useState<string[]>([]);
  const [showSourceInventory, setShowSourceInventory] = useState(false);
  const [showAdvancedControlRoom, setShowAdvancedControlRoom] = useState(false);
  const [showManualOnboard, setShowManualOnboard] = useState(false);
  const [fetchBusy, setFetchBusy] = useState(false);
  /** Always-visible last Admin action result (toasts alone are easy to miss) */
  const [adminLastAction, setAdminLastAction] = useState<{
    action: string;
    ok: boolean;
    title: string;
    message: string;
    details?: any;
    at: string;
  } | null>(null);
  const [ontologyValidation, setOntologyValidation] = useState<any>(null);
  const [ontologyBusy, setOntologyBusy] = useState(false);
  /** Server ingest plan: detected changes + recommended next actions */
  const [ingestPlan, setIngestPlan] = useState<any>(null);
  /** Durable + session audit (GET /admin/audit/history) */
  const [auditHistory, setAuditHistory] = useState<any>(null);
  const [auditBusy, setAuditBusy] = useState(false);
  const [showAuditPanel, setShowAuditPanel] = useState(true);
  /** Entity-level ABox delta (catalog vs Neo4j) for selected products */
  const [entityDelta, setEntityDelta] = useState<any>(null);
  const [entityDeltaBusy, setEntityDeltaBusy] = useState(false);
  const [neo4jVerify, setNeo4jVerify] = useState<any>(null);
  const [showRdfPreview, setShowRdfPreview] = useState(false);
  const [rdfPreview, setRdfPreview] = useState<any>(null);
  /** new_only | full_abox | schema */
  const [rdfViewMode, setRdfViewMode] = useState<'new_only' | 'full_abox' | 'schema'>('new_only');
  const adminResultRef = useRef<HTMLDivElement | null>(null);
  const changePreviewRef = useRef<HTMLDivElement | null>(null);

  const qc = useQueryClient();

  // Classic gate flags (API may put these under review_state)
  const smokePassed = Boolean(
    adminStatus?.smoke_passed ?? adminStatus?.review_state?.last_smoke_ok ?? adminStatus?.review_state?.smoke_ok
  );
  const humanReviewed = Boolean(adminStatus?.reviewed ?? adminStatus?.review_state?.reviewed);
  const canPromote = Boolean(adminStatus?.can_promote ?? (smokePassed && humanReviewed));
  const readyForCustomerTest = Boolean(
    adminStatus?.ready_for_customer_test ?? adminStatus?.review_state?.ready_for_customer_test
  );
  const hasFetched = Boolean(
    adminStatus?.onboarding_progress?.fetched ||
      adminStatus?.review_state?.last_fetch_at ||
      adminStatus?.review_state?.last_report ||
      changePreview
  );
  const diffSummary = changePreview?.diff_vs_production?.summary || {};
  const selectionSummary = changePreview?.diff_vs_production?.selection_summary || {};
  const newProducts = changePreview?.diff_vs_production?.new_products || [];
  const updatedProducts = changePreview?.diff_vs_production?.updated_products || [];
  const unchangedProducts = changePreview?.diff_vs_production?.unchanged_products || [];
  const unchangedCount = Number(diffSummary.unchanged_count || unchangedProducts.length || 0);
  const selectedFromPreview: string[] =
    selectionSummary.selected_product_ids || changePreview?.selected_product_ids || [];
  /** Prefer locked scope (after Confirm selection) over transient preview checkboxes */
  const activeSelectionIds: string[] =
    lockedSelectionIds.length > 0 ? lockedSelectionIds : selectedFromPreview;
  const selectedTotal = activeSelectionIds.length;
  const selectedNewCount = Number(selectionSummary.selected_new_count ?? 0);
  const selectedUpdatedCount = Number(selectionSummary.selected_updated_count ?? 0);

  // Live data with loading/error
  const { data: health, isLoading: healthLoading } = useQuery({ queryKey: ['health'], queryFn: api.health, refetchInterval: 15000 });
  const { data: claimsData, isLoading: claimsLoading, error: claimsError } = useQuery({ queryKey: ['claims'], queryFn: () => api.listClaims(20) });
  const { data: batchesData, isLoading: batchesLoading } = useQuery({ queryKey: ['batches'], queryFn: () => api.listBatches(8) });
  const { data: statusData } = useQuery({ queryKey: ['status'], queryFn: api.integrationsStatus });
  const { data: ontologyData } = useQuery({ queryKey: ['ontology'], queryFn: api.getOntology });
  const { data: productsData } = useQuery({ queryKey: ['products'], queryFn: api.listProducts });
  const { data: customersData } = useQuery({
    queryKey: ['crm-customers'],
    queryFn: api.listCustomers,
  });
  const { data: customerAssetsData, isFetching: assetsLoading } = useQuery({
    queryKey: ['crm-assets', selectedCustomerId],
    queryFn: () => api.listCustomerAssets(selectedCustomerId),
    enabled: sessionMode === 'customer' && !!selectedCustomerId,
  });

  const productsList = (productsData?.products || [
    { product_id: 'wm-001', name: 'Washer wm-001' },
    { product_id: 'dw-001', name: 'Dishwasher dw-001' },
    { product_id: 'mw-001', name: 'Microwave mw-001' }
  ]) as Array<{product_id: string, name: string}>;
  const customersList = customersData?.customers || [];

  // Sync assets when customer loads
  useEffect(() => {
    if (sessionMode !== 'customer') return;
    const assets = customerAssetsData?.registered_assets || [];
    setCustomerAssets(assets);
    if (!assets.length) {
      setSelectedAssetRecord(null);
      return;
    }
    // Keep selection if still owned; else pick first
    setSelectedAssetRecord((prev: any) => {
      if (prev && assets.some((a: any) => a.asset_id === prev.asset_id)) {
        return assets.find((a: any) => a.asset_id === prev.asset_id) || assets[0];
      }
      // New customer / first load: pick first asset and collapse picker so chat fits
      setAssetPickerExpanded(assets.length <= 3);
      return assets[0];
    });
  }, [customerAssetsData, sessionMode]);

  const productNameFor = (productId?: string) =>
    productsList.find((p) => p.product_id === productId)?.name || productId || '—';

  const buildDiagnoseBody = (message: string, forceKeep = false) => {
    if (sessionMode === 'customer' && selectedAssetRecord) {
      return {
        message,
        customer_id: selectedCustomerId,
        asset_id: selectedAssetRecord.asset_id,
        force_keep_context: forceKeep,
        // product derived server-side from asset — do not send conflicting product_id
      };
    }
    return {
      message,
      product_id: anonymousProductId,
      force_keep_context: forceKeep,
    };
  };

  // Send diagnosis
  const diagnoseMutation = useMutation({
    mutationFn: (body: any) => api.diagnose(body),
    onSuccess: (res: any, variables: any) => {
      const diag = res.diagnosis;
      setCurrentDiagnosis(diag);
      setLastDiagnosis({ ...res, product_id: diag?.product_id || chatProductId });
      if (diag?.product_id) setExplorerProductId(diag.product_id);

      const soft = diag?.context_blocked && String(diag?.context_block_code || '').startsWith('soft_');
      if (soft) {
        setPendingMismatch({
          message: variables?.message || input,
          diagnosis: diag,
          full: res,
        });
        toast.message('Confirm appliance', {
          description: 'Description may not match the registered unit.',
        });
      } else {
        setPendingMismatch(null);
      }

      const assistantMsg: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: res.response,
        diagnosis: diag,
        full: res,
      };
      setMessages(prev => [...prev, assistantMsg]);

      if (soft) {
        /* banner handles UX */
      } else if (diag?.context_blocked) {
        toast.error('Binding conflict', { description: diag.context_block_code });
      } else if (res.escalated) {
        toast.warning('Case escalated for human review', { description: res.case_id });
      } else {
        toast.success('Diagnosis complete', { description: `${diag?.ranked_failure_modes?.[0]?.name || 'Ready'}` });
      }
    },
    onError: (e: any) => toast.error('Diagnosis failed', { description: e.message }),
  });

  // Keep latest message visible above the pinned composer
  useEffect(() => {
    if (activeView !== 'chat') return;
    chatMessagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, diagnoseMutation.isPending, activeView, pendingMismatch]);

  const handleSend = (forceKeep = false) => {
    if (!input.trim() && !forceKeep) return;
    if (sessionMode === 'customer' && !selectedAssetRecord) {
      toast.error('Select a registered appliance first');
      return;
    }
    const text = forceKeep && pendingMismatch ? pendingMismatch.message : input.trim();
    if (!text) return;

    if (!forceKeep) {
      const userMsg: ChatMessage = {
        id: 'u' + Date.now(),
        role: 'user',
        content: text,
      };
      setMessages(prev => [...prev, userMsg]);
      setInput('');
    }

    diagnoseMutation.mutate(buildDiagnoseBody(text, forceKeep));
  };

  const handleForceKeepAppliance = () => {
    if (!pendingMismatch) return;
    const text = pendingMismatch.message;
    setPendingMismatch(null);
    diagnoseMutation.mutate(buildDiagnoseBody(text, true));
  };

  const handleSwitchToSuggestedProduct = () => {
    if (!pendingMismatch) return;
    const msg = pendingMismatch.message;
    const suggested =
      pendingMismatch.diagnosis?.resolution_meta?.suggested_product_id ||
      pendingMismatch.diagnosis?.resolution_meta?.message_product_id;
    if (!suggested) {
      toast.error('No suggested appliance from description');
      return;
    }
    if (sessionMode === 'customer') {
      const match = customerAssets.find((a) => a.product_id === suggested);
      if (match) {
        setSelectedAssetRecord(match);
        setPendingMismatch(null);
        toast.success('Switched appliance', { description: match.asset_id });
        diagnoseMutation.mutate({
          message: msg,
          customer_id: selectedCustomerId,
          asset_id: match.asset_id,
          force_keep_context: false,
        });
      } else {
        toast.error('This customer has no registered asset for that product', {
          description: `Need product ${suggested} on the account — switch customer or use Anonymous demo.`,
        });
      }
    } else {
      setAnonymousProductId(suggested);
      setPendingMismatch(null);
      diagnoseMutation.mutate({
        message: msg,
        product_id: suggested,
        force_keep_context: false,
      });
    }
  };

  // Voice input (Web Speech API) - 2026 natural input trend
  const toggleVoice = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      toast.error("Voice not supported in this browser");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript);
      setIsListening(false);
      setTimeout(() => {
        if (sessionMode === 'customer' && !selectedAssetRecord) {
          toast.error('Select a registered appliance first');
          return;
        }
        const userMsg: ChatMessage = { id: 'u' + Date.now(), role: 'user', content: transcript };
        setMessages(prev => [...prev, userMsg]);
        diagnoseMutation.mutate(buildDiagnoseBody(transcript, false));
      }, 300);
    };
    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);

    if (!isListening) {
      setIsListening(true);
      recognition.start();
    } else {
      recognition.stop();
    }
  };

  // Simple Command Palette (cmdk) - modern power user feature
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setCommandOpen(v => !v);
      }
      if (e.key === 'Escape') setCommandOpen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const runCommand = (cmd: string) => {
    setCommandOpen(false);
    if (cmd === 'chat') setActiveView('chat');
    if (cmd === 'cases') setActiveView('cases');
    if (cmd === 'explorer') {
      setActiveView('explorer');
      if (!explorerData) loadExplorer(explorerProductId, false);
    }
    if (cmd === 'ops') setActiveView('ops');
    if (cmd === 'admin') setActiveView('admin');
    if (cmd === 'voice') toggleVoice();
    if (cmd === 'example') {
      const ex = examplePrompts[0];
      setInput(ex);
      setActiveView('chat');
    }
  };

  // ===== ADMIN HANDLERS (Enterprise gated pipeline) =====
  const ADMIN_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
  // Include the admin token header when configured (required by the API in
  // non-local deployments; omitted for the open local demo).
  const adminHeaders = (extra: Record<string, string> = {}): Record<string, string> => {
    const token = process.env.NEXT_PUBLIC_ADMIN_TOKEN;
    return token ? { ...extra, 'X-Admin-Token': token } : extra;
  };

  /** Fetch Admin API with HTTP error surfacing (avoids opaque "Load failed"). */
  const adminFetch = async (path: string, init: RequestInit = {}): Promise<any> => {
    const url = path.startsWith('http') ? path : `${ADMIN_BASE}${path}`;
    const method = (init.method || 'GET').toUpperCase();
    const headers: Record<string, string> = {
      ...adminHeaders(),
      ...(init.headers as Record<string, string> | undefined),
    };
    // Always set JSON content-type for POST/PUT with body or bare POST (FastAPI-friendly)
    if ((method === 'POST' || method === 'PUT' || method === 'PATCH') && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }
    let res: Response;
    try {
      res = await fetch(url, {
        ...init,
        method,
        headers,
        body: init.body ?? (method === 'POST' && !init.body ? '{}' : init.body),
      });
    } catch (e: any) {
      const msg = e?.message || 'Network error';
      // Safari/Chrome often report failed POST as "Load failed" / "Failed to fetch"
      throw new Error(
        msg === 'Load failed' || msg === 'Failed to fetch'
          ? `Cannot reach API at ${ADMIN_BASE}. Is uvicorn running on :8080? (${msg})`
          : msg
      );
    }
    const text = await res.text();
    let data: any = null;
    if (text) {
      try {
        data = JSON.parse(text);
      } catch {
        data = { detail: text.slice(0, 400) };
      }
    }
    if (!res.ok) {
      const detail =
        (typeof data?.detail === 'string' && data.detail) ||
        (Array.isArray(data?.detail) && JSON.stringify(data.detail).slice(0, 300)) ||
        data?.error ||
        data?.message ||
        text.slice(0, 300) ||
        res.statusText;
      throw new Error(`HTTP ${res.status}: ${detail}`);
    }
    return data ?? {};
  };

  const recordAdminAction = (
    action: string,
    ok: boolean,
    title: string,
    message: string,
    details?: any
  ) => {
    setAdminLastAction({
      action,
      ok,
      title,
      message,
      details,
      at: new Date().toISOString(),
    });
    // Scroll result into view so "nothing on screen" never happens after a click
    requestAnimationFrame(() => {
      adminResultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
  };

  const applyChangePreviewPayload = (payload: any) => {
    if (payload?.change_preview) setChangePreview(payload.change_preview);
    if (Array.isArray(payload?.journey)) setAdminJourney(payload.journey);
    if (payload?.ontology_validation) setOntologyValidation(payload.ontology_validation);
    if (payload?.ingest_plan) setIngestPlan(payload.ingest_plan);
    if (Array.isArray(payload?.locked_selection_ids) && payload.locked_selection_ids.length) {
      setLockedSelectionIds(payload.locked_selection_ids);
    }
  };

  /**
   * Refresh plan = recompute recommended actions from current catalog vs production Neo4j
   * + session gates (selection, smoke, approve, materialize). Does NOT fetch sources or write Neo4j.
   */
  const refreshIngestPlan = async (opts?: {
    quiet?: boolean;
    withStatus?: boolean;
    /** Prevent recursion when called from resetWizardForNextCycle */
    skipIdleReset?: boolean;
  }) => {
    // quiet default true for internal calls; user click passes quiet: false
    const quiet = opts?.quiet ?? true;
    const withStatus = Boolean(opts?.withStatus);
    try {
      if (!quiet) {
        recordAdminAction('plan', true, 'Refreshing plan…', 'Re-diff catalog vs production + recompute next steps (no Neo4j write)');
      }
      // Always re-diff so Pending UPDATE / in-sync counts move after promotes
      const previewRes = await adminFetch('/admin/pipeline/change-preview?refresh=true');
      applyChangePreviewPayload(previewRes);
      const res = await adminFetch('/admin/pipeline/plan?refresh=true');
      applyChangePreviewPayload(res);
      if (res?.ingest_plan) setIngestPlan(res.ingest_plan);
      if (Array.isArray(res?.locked_selection_ids) && res.locked_selection_ids.length) {
        setLockedSelectionIds(res.locked_selection_ids);
      }

      const plan = res?.ingest_plan || {};
      const diff = (res?.change_preview || previewRes?.change_preview)?.diff_vs_production || {};
      const summary = diff.summary || plan.detected?.summary || {};
      // Single source of truth: prefer plan.detected (same as on-screen tiles)
      const n = Number(plan.detected?.new_product?.count ?? summary.new_count ?? 0);
      const u = Number(plan.detected?.product_update?.count ?? summary.updated_count ?? 0);
      const un = Number(
        plan.scope?.unchanged_count ?? summary.unchanged_count ?? 0
      );
      const nextAction = plan.next_action || res?.next_action || null;
      const nextTitle = nextAction?.title || null;
      // Toast must match on-screen plan.headline (was building a different string)
      const headline =
        plan.headline ||
        `${n} NEW · ${u} pending UPDATE · ${un} already in sync`;
      const msg = nextTitle ? `${headline}` : `${headline} · No next action (batch complete or idle)`;

      if (withStatus) {
        const scope =
          lockedSelectionIds.length > 0
            ? lockedSelectionIds
            : plan.scope?.selected_product_ids ||
              (res?.change_preview || previewRes?.change_preview)?.selected_product_ids ||
              [];
        if (scope.length) {
          await refreshEntityDelta(scope);
          await refreshNeo4jVerify(scope);
        }
      }

      // Fleet fully idle after a finished batch → unlock wizard for next cycle
      const batchFinished = Boolean(
        wizardStepDone[8] || promoteResult?.ok || readyForCustomerTest
      );
      if (!opts?.skipIdleReset && n === 0 && u === 0 && batchFinished) {
        await resetWizardForNextCycle({
          quiet: true,
          reason: 'Fleet fully in sync — session reset for next plan.',
        });
        if (!quiet) {
          toast.success('Plan refreshed', {
            description: `${un} already in sync · Wizard ready for next plan (no pending work)`,
          });
          recordAdminAction('plan', true, 'Plan refreshed — ready for next cycle', msg, {
            new_count: n,
            updated_count: u,
            unchanged_count: un,
            idle_reset: true,
          });
        }
        return plan;
      }

      if (!quiet) {
        recordAdminAction('plan', true, 'Plan refreshed', msg, {
          new_count: n,
          updated_count: u,
          unchanged_count: un,
          next_action: nextAction?.action_id,
          gates: plan.gates || res?.gates,
          headline,
        });
        toast.success('Plan refreshed', {
          description: msg,
        });
      }
      return plan;
    } catch (e: any) {
      if (!quiet) {
        recordAdminAction('plan', false, 'Plan refresh failed', e?.message || 'Error');
        toast.error('Plan refresh failed', { description: e?.message });
      }
      return null;
    }
  };

  const refreshChangePreview = async (refresh = true) => {
    try {
      const res = await adminFetch(
        `/admin/pipeline/change-preview?refresh=${refresh ? 'true' : 'false'}`
      );
      applyChangePreviewPayload(res);
      return res;
    } catch (e: any) {
      toast.error('Change preview failed', { description: e?.message });
      return null;
    }
  };

  /**
   * After a finished promote (or when fleet is fully in sync), clear selection +
   * wizard locks so Admin is ready for a brand-new plan cycle. Does not touch Neo4j.
   */
  const resetWizardForNextCycle = async (opts?: {
    quiet?: boolean;
    clearFetch?: boolean;
    reason?: string;
  }) => {
    const quiet = Boolean(opts?.quiet);
    try {
      const res = await adminFetch('/admin/pipeline/session/reset-for-next-cycle', {
        method: 'POST',
        body: JSON.stringify({
          keep_journey: true,
          clear_fetch: Boolean(opts?.clearFetch),
        }),
      });
      applyChangePreviewPayload(res);
      setLockedSelectionIds([]);
      setWizardStepDone({});
      setAdminWizardStep(1);
      setEntityDelta(null);
      setNeo4jVerify(null);
      setPromoteResult(null);
      setOntologyValidation(null);
      setLastKgRun(null);
      // refresh gates from server (smoke/approve cleared)
      await refreshAdminStatus();
      await refreshIngestPlan({ quiet: true, skipIdleReset: true });
      const idle = Boolean(res?.idle);
      const fs = res?.fleet_summary || {};
      const msg =
        res?.message ||
        opts?.reason ||
        (idle
          ? 'Fleet fully in sync — wizard reset. Ready when new sources arrive.'
          : 'Wizard reset — select the next NEW/UPDATE batch.');
      if (!quiet) {
        recordAdminAction('session', true, 'Ready for next plan', msg, {
          idle,
          fleet_summary: fs,
        });
        toast.success(idle ? 'Ready for next plan' : 'Wizard reset', {
          description: msg,
        });
      }
      return res;
    } catch (e: any) {
      if (!quiet) {
        toast.error('Reset failed', { description: e?.message });
      }
      return null;
    }
  };

  /** Select/deselect products in the change-set (does not auto-run pipelines). */
  const handleProductSelection = async (body: Record<string, unknown>) => {
    try {
      const res = await adminFetch('/admin/pipeline/selection', {
        method: 'POST',
        body: JSON.stringify(body),
      });
      applyChangePreviewPayload(res);
      if (Array.isArray(res?.locked_selection_ids)) {
        setLockedSelectionIds(res.locked_selection_ids);
      } else if (Array.isArray(res?.selected_product_ids)) {
        // Keep locked scope aligned when pruning selection
        if (body.drop_in_sync || body.keep_actionable_only) {
          setLockedSelectionIds(res.selected_product_ids);
        }
      }
      if (res?.selection_summary || res?.message) {
        const dropped = (res.dropped_in_sync || []).length;
        toast.success(
          dropped
            ? `Dropped ${dropped} IN SYNC · ${(res.selected_product_ids || []).length} remain`
            : res.message ||
                `Selected ${res.selection_summary?.selected_total ?? 0} product(s) for KG`,
          dropped ? { description: res.message } : undefined
        );
      }
      return res;
    } catch (e: any) {
      toast.error('Selection failed', { description: e?.message });
      return null;
    }
  };

  /** Drop products that entity-delta marks IN SYNC — works even after step 3 is locked. */
  const handleDropInSyncFromSelection = async () => {
    const fromDelta = (entityDelta?.products || [])
      .map((p: any) => p?.product_id)
      .filter(Boolean) as string[];
    const fromSummary = (entityDelta?.summary?.in_sync_product_ids || []) as string[];
    const scope = Array.from(
      new Set([
        ...fromDelta,
        ...fromSummary,
        ...lockedSelectionIds,
        ...selectedFromPreview,
        ...activeSelectionIds,
      ])
    );
    if (!scope.length) {
      toast.error('Nothing to prune', { description: 'No products in selection or entity delta.' });
      return null;
    }
    const res = await handleProductSelection({
      drop_in_sync: true,
      product_ids: scope,
      entity_delta_product_ids: fromDelta,
    });
    if (res) {
      const kept = (res.selected_product_ids || res.locked_selection_ids || []) as string[];
      setLockedSelectionIds(kept);
      // Always recompute entity delta for the pruned scope (clears stale 20-product panel)
      await refreshEntityDelta(kept);
      await refreshNeo4jVerify(kept);
      await refreshIngestPlan({ quiet: true });
    }
    return res;
  };

  const refreshAdminStatus = async () => {
    try {
      const [status, review] = await Promise.all([
        adminFetch('/admin/pipeline/status'),
        adminFetch('/admin/pipeline/review').catch(() => ({})),
      ]);
      // Merge so Smoke Passed / Human Reviewed resolve from review_state + review payload
      setAdminStatus({
        ...status,
        ...review,
        smoke_passed: Boolean(
          review?.smoke_passed ?? status?.review_state?.last_smoke_ok ?? status?.smoke_passed
        ),
        reviewed: Boolean(review?.reviewed ?? status?.review_state?.reviewed),
        can_promote: Boolean(
          review?.can_promote ??
            ((review?.smoke_passed ?? status?.review_state?.last_smoke_ok) &&
              (review?.reviewed ?? status?.review_state?.reviewed))
        ),
        ready_for_customer_test: Boolean(
          review?.ready_for_customer_test ?? status?.review_state?.ready_for_customer_test
        ),
      });
      if (status?.change_preview) setChangePreview(status.change_preview);
      else if (review?.change_preview) setChangePreview(review.change_preview);
      if (status?.ingest_plan) setIngestPlan(status.ingest_plan);
      if (Array.isArray(status?.locked_selection_ids) && status.locked_selection_ids.length) {
        setLockedSelectionIds(status.locked_selection_ids);
      }
      const journey = status?.journey || review?.journey;
      if (Array.isArray(journey)) setAdminJourney(journey);
    } catch (e: any) {
      toast.error('Failed to fetch admin status', { description: e?.message });
    }
  };

  const refreshAuditHistory = async () => {
    setAuditBusy(true);
    try {
      const res = await adminFetch('/admin/audit/history?limit=50');
      setAuditHistory(res);
      if (Array.isArray(res?.session_journey) && res.session_journey.length) {
        setAdminJourney(res.session_journey);
      }
      return res;
    } catch (e: any) {
      // Non-fatal — older API may not have the route until restart
      console.warn('audit history', e?.message);
      return null;
    } finally {
      setAuditBusy(false);
    }
  };

  const refreshEntityDelta = async (productIds?: string[]) => {
    const ids =
      productIds && productIds.length
        ? productIds
        : lockedSelectionIds.length
          ? lockedSelectionIds
          : activeSelectionIds;
    if (!ids.length) {
      setEntityDelta(null);
      return null;
    }
    setEntityDeltaBusy(true);
    try {
      const q = new URLSearchParams({
        product_ids: ids.join(','),
        compare_env: 'production',
      });
      const res = await adminFetch(`/admin/pipeline/entity-delta?${q}`);
      setEntityDelta(res);
      return res;
    } catch (e: any) {
      console.warn('entity delta', e?.message);
      return null;
    } finally {
      setEntityDeltaBusy(false);
    }
  };

  const refreshNeo4jVerify = async (productIds?: string[]) => {
    const ids =
      productIds && productIds.length
        ? productIds
        : lockedSelectionIds.length
          ? lockedSelectionIds
          : activeSelectionIds;
    if (!ids.length) {
      setNeo4jVerify(null);
      return null;
    }
    try {
      const res = await adminFetch(
        `/admin/pipeline/neo4j-verify?product_ids=${encodeURIComponent(ids.join(','))}`
      );
      setNeo4jVerify(res);
      return res;
    } catch (e: any) {
      console.warn('neo4j verify', e?.message);
      return null;
    }
  };

  const loadRdfForSelection = async (productId: string) => {
    try {
      // Prefer delta payload (highlights NEW ABox); also fetch full ABox (no schema noise)
      let highlight =
        (entityDelta?.products || []).find((p: any) => p.product_id === productId)?.rdf_highlight || null;
      if (!highlight) {
        const deltaRes = await adminFetch(
          `/admin/pipeline/entity-delta?product_ids=${encodeURIComponent(productId)}&compare_env=production`
        );
        setEntityDelta(deltaRes);
        highlight =
          (deltaRes?.products || []).find((p: any) => p.product_id === productId)?.rdf_highlight || null;
      }
      const abox = await api.getRdfProduct(productId, false);
      setRdfPreview({
        productId,
        highlight,
        turtle_abox: abox.turtle || '',
        turtle_new_only: highlight?.turtle_new_only || '',
        ontology_hits: highlight?.ontology_hits || [],
        tbox_changed: Boolean(highlight?.tbox_changed),
        abox_changed: Boolean(highlight?.abox_changed),
        tbox_summary: highlight?.tbox_summary,
        how_to_read: highlight?.how_to_read || [],
        new_entity_ids: highlight?.new_entity_ids || [],
      });
      setRdfViewMode(highlight?.abox_changed ? 'new_only' : 'full_abox');
      setShowRdfPreview(true);
    } catch (e: any) {
      toast.error('RDF load failed', { description: e?.message });
    }
  };

  /** Render Turtle with NEW entity lines highlighted */
  const renderHighlightedTurtle = (text: string, highlightIds: string[] = []) => {
    const tokens = highlightIds.filter(Boolean);
    const lines = String(text || '').split('\n');
    return (
      <pre className="text-[10px] font-mono max-h-72 overflow-auto whitespace-pre-wrap leading-relaxed">
        {lines.map((line, i) => {
          const isNew =
            tokens.length > 0 &&
            tokens.some((t) => line.includes(t)) &&
            !line.trim().startsWith('#');
          const isComment = line.trim().startsWith('#');
          return (
            <div
              key={i}
              className={
                isNew
                  ? 'bg-amber-400/25 text-amber-100 border-l-2 border-amber-400 pl-1'
                  : isComment
                    ? 'text-violet-300/70'
                    : 'text-white/55'
              }
            >
              {line || ' '}
            </div>
          );
        })}
      </pre>
    );
  };

  const fetchReview = async () => {
    try {
      const res = await adminFetch('/admin/pipeline/review');
      setAdminStatus((prev: any) => ({
        ...prev,
        ...res,
        smoke_passed: Boolean(res?.smoke_passed ?? prev?.review_state?.last_smoke_ok),
        reviewed: Boolean(res?.reviewed),
        can_promote: Boolean(res?.can_promote),
        ready_for_customer_test: Boolean(res?.ready_for_customer_test),
      }));
      applyChangePreviewPayload(res);
    } catch (e: any) {
      toast.error('Failed to load review', { description: e?.message });
    }
  };

  const handleOnboardProduct = async () => {
    try {
      const res = await adminFetch('/admin/onboard-product', {
        method: 'POST',
        body: JSON.stringify(onboardForm),
      });
      toast.success(res.message || 'Product staged');
      applyChangePreviewPayload(res);
      refreshAdminStatus();
      setAdminWizardStep(2);
    } catch (e: any) {
      toast.error('Onboard failed', { description: e?.message });
    }
  };

  const handleDryRunETL = async () => {
    setFetchBusy(true);
    recordAdminAction(
      'fetch',
      true,
      'Fetch running…',
      'Re-diff catalog/sources vs production Neo4j (dry-run — no Neo4j write). Prior promotes stay in the graph; in-sync products leave the UPDATE list.'
    );
    try {
      const res = await adminFetch('/admin/pipeline/dry-run-etl', { method: 'POST' });
      applyChangePreviewPayload(res);
      // Fetch recomputes the fleet — clear prior wizard selection so you re-pick scope intentionally
      setLockedSelectionIds([]);
      setWizardStepDone((prev) => {
        const next: Record<number, boolean> = { ...prev, 2: true };
        // downstream steps need re-validation for a new change-set
        for (const k of [3, 4, 5, 6, 7, 8]) delete next[k];
        return next;
      });
      setEntityDelta(null);
      setNeo4jVerify(null);
      setPromoteResult(null);
      const n = res?.change_preview?.diff_vs_production?.summary?.new_count ?? 0;
      const u = res?.change_preview?.diff_vs_production?.summary?.updated_count ?? 0;
      const un =
        res?.change_preview?.diff_vs_production?.summary?.unchanged_count ??
        (res?.change_preview?.diff_vs_production?.unchanged_products || []).length ??
        0;
      const ui = res?.ui_result || {};
      const msg =
        res.message ||
        ui.headline ||
        `Fetch complete — ${n} NEW, ${u} pending UPDATE(s), ${un} already in sync with production`;
      recordAdminAction('fetch', true, ui.title || 'Fetch complete', msg, {
        sources: res.sources || ui.sources,
        product_count: res.product_count,
        new_count: n,
        updated_count: u,
        unchanged_count: un,
        ontology: res.ontology_validation?.headline || ui.ontology_headline,
        next_step: ui.next_step,
        batch_id: res.batch_id,
        note: 'Promoted ABox remains in Neo4j. Fetch only refreshes the pending list.',
      });
      toast.success('Fetch preview ready', {
        description: `${u} still pending · ${un} already in sync (promotes persist in Neo4j)`,
      });
      await refreshAdminStatus();
      setAdminWizardStep(3);
      requestAnimationFrame(() => {
        changePreviewRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        adminResultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      });
    } catch (e: any) {
      recordAdminAction('fetch', false, 'Fetch failed', e?.message || 'Dry-run ETL error');
      toast.error('Fetch failed', { description: e?.message || 'Dry-run ETL error' });
    } finally {
      setFetchBusy(false);
    }
  };

  const handleOntologyValidate = async (): Promise<boolean> => {
    setOntologyBusy(true);
    recordAdminAction('ontology', true, 'Ontology validation running…', 'Checking selected ABox against TBox shapes');
    try {
      // Prefer explicit selection; fall back to all NEW
      const body =
        selectedTotal > 0
          ? {}
          : { all_new: true };
      const res = await adminFetch('/admin/ontology/validate-selection', {
        method: 'POST',
        body: JSON.stringify(body),
      });
      setOntologyValidation(res);
      applyChangePreviewPayload(res);
      const ok = Boolean(res.ok || (res.failed_count === 0 && (res.passed_count || 0) > 0));
      recordAdminAction(
        'ontology',
        ok,
        'Ontology validation (TBox → ABox)',
        res.message || res.headline || 'Validation finished',
        {
          passed: res.passed_product_ids,
          failed: res.failed_product_ids,
          passed_count: res.passed_count,
          failed_count: res.failed_count,
          sample_errors: (res.reports || [])
            .filter((r: any) => !r.ok)
            .slice(0, 3)
            .flatMap((r: any) => r.errors || []),
        }
      );
      toast[ok ? 'success' : 'error'](res.message || res.headline);
      if (ok) {
        setWizardStepDone((prev) => ({ ...prev, 4: true }));
        setAdminWizardStep(5);
      }
      return ok;
    } catch (e: any) {
      recordAdminAction('ontology', false, 'Ontology validation failed', e?.message || 'Error');
      toast.error('Ontology validation failed', { description: e?.message });
      return false;
    } finally {
      setOntologyBusy(false);
    }
  };

  const handleValidate = async () => {
    recordAdminAction('smoke', true, 'Smoke validation running…', 'Running diagnosis scenarios');
    try {
      const res = await adminFetch('/admin/pipeline/validate', { method: 'POST' });
      toast[res.ok ? 'success' : 'error'](res.message || (res.ok ? 'Smoke passed' : 'Smoke failed'));
      applyChangePreviewPayload(res);
      const failLines = (res.details || []).filter((l: string) => String(l).includes('[FAIL]')).slice(0, 5);
      recordAdminAction(
        'smoke',
        Boolean(res.ok),
        res.ok ? 'Smoke passed' : 'Smoke failed',
        res.message || (res.ok ? 'All smoke scenarios passed' : 'See failure details'),
        {
          passed: res.passed,
          failed: res.failed,
          failures: failLines,
          details: (res.details || []).slice(-8),
        }
      );
      await refreshAdminStatus();
      if (res.ok) {
        setWizardStepDone((prev) => ({ ...prev, 6: true }));
        setAdminWizardStep(7);
      }
    } catch (e: any) {
      recordAdminAction('smoke', false, 'Smoke validation failed', e?.message || 'Error');
      toast.error('Smoke validation failed', { description: e?.message });
    }
  };

  const handleReview = async () => {
    await fetchReview();
    recordAdminAction('review', true, 'Review refreshed', 'Check What’s coming + ontology results, then Approve');
    toast.info("Review loaded. Check What's coming, then Approve if OK.");
  };

  const handleApprove = async () => {
    try {
      const res = await adminFetch('/admin/pipeline/approve-review', { method: 'POST' });
      applyChangePreviewPayload(res);
      await refreshAdminStatus();
      recordAdminAction('approve', true, 'Changes approved', res.message || 'Promotion unlocked');
      toast.success(res.message || 'Review approved — promotion unlocked');
      setAdminWizardStep(8);
    } catch (e: any) {
      recordAdminAction('approve', false, 'Approve failed', e?.message || 'Error');
      toast.error('Approve failed', { description: e?.message });
    }
  };

  /** Single promote path: control-plane promote_graph with target env (staging | production). */
  const handlePromoteSelection = async (target: 'staging' | 'production' = kgTargetEnv) => {
    const scopeIds: string[] =
      lockedSelectionIds.length > 0
        ? lockedSelectionIds
        : selectionSummary.selected_product_ids ||
          changePreview?.selected_product_ids ||
          [];
    if (!scopeIds.length) {
      toast.error('No products selected', { description: 'Lock a selection before promote.' });
      return;
    }
    if (target === 'production' && !(smokePassed && humanReviewed)) {
      toast.error('Production promote blocked', {
        description: 'Smoke must pass and Approve must be done before production.',
      });
      return;
    }

    const scopeKey = `${target}|${[...scopeIds].sort().join(',')}`;
    setPromoteBusy(true);
    setKgRunBusy(true);
    recordAdminAction(
      'promote',
      true,
      `Promoting to ${target}…`,
      `MERGE ${scopeIds.join(', ')} → Neo4j ${target}`
    );
    try {
      const q = new URLSearchParams({
        mode: kgMode,
        dry_run: 'false',
        target_env: target,
        use_selection: 'true',
        product_ids: scopeIds.join(','),
      });
      const res = await adminFetch(`/admin/kg-pipelines/promote_graph/run?${q}`, {
        method: 'POST',
      });
      setLastKgRun({ ...res, dry_run: false, pipeline_id: res.pipeline_id || 'promote_graph' });
      applyChangePreviewPayload(res);
      const ok = res.status === 'success' || res.status === 'partial';
      const err0 = (res.errors && res.errors[0]) || '';
      const msg =
        res.message ||
        (ok
          ? `Promotion successful → ${target} · ${scopeIds.join(', ')}`
          : `Promote failed: ${err0 || res.status}`);

      setPromoteResult({
        ok,
        target,
        productIds: scopeIds,
        scopeKey,
        message: msg,
        at: new Date().toISOString(),
        runId: res.run_id,
      });

      if (ok) {
        toast.success(
          target === 'production'
            ? 'Production promote successful — ready for Diagnosis Chat'
            : 'Staging promote successful'
        );
        recordAdminAction('promote', true, `✓ Promoted to ${target}`, msg, {
          product_ids: scopeIds,
          target_env: target,
          run_id: res.run_id,
        });
        setWizardStepDone((prev) => ({ ...prev, 8: true }));
        // Refresh all fleet + selection displays so counts/badges match Neo4j
        const previewAfter = await refreshChangePreview(true);
        await refreshIngestPlan({ quiet: true });
        await refreshEntityDelta(scopeIds);
        await refreshNeo4jVerify(scopeIds);
        await refreshAdminStatus();
        refreshAuditHistory();
        if (target === 'production') {
          qc.invalidateQueries({ queryKey: ['products'] });
          qc.invalidateQueries({ queryKey: ['crm-assets', selectedCustomerId] });
          // If the whole fleet is now in sync, reset wizard for a clean next cycle
          const sum =
            previewAfter?.change_preview?.diff_vs_production?.summary ||
            previewAfter?.diff_vs_production?.summary ||
            {};
          const n = Number(sum.new_count || 0);
          const u = Number(sum.updated_count || 0);
          if (n === 0 && u === 0) {
            await resetWizardForNextCycle({
              quiet: false,
              reason:
                'Production promote complete and fleet fully in sync — wizard reset for the next plan.',
            });
          }
        }
      } else {
        toast.error('Promote failed', { description: err0 || res.status });
        recordAdminAction('promote', false, `Promote to ${target} failed`, err0 || msg);
      }

      refreshKgControlRoom();
      await refreshAdminStatus();
      refreshAuditHistory();
    } catch (e: any) {
      setPromoteResult({
        ok: false,
        target,
        productIds: scopeIds,
        scopeKey,
        message: e?.message || 'Promote failed',
        at: new Date().toISOString(),
      });
      recordAdminAction('promote', false, 'Promote failed', e?.message || 'Error');
      toast.error('Promote failed', { description: e?.message });
    } finally {
      setPromoteBusy(false);
      setKgRunBusy(false);
    }
  };

  const refreshKgControlRoom = async () => {
    try {
      const [pipes, runs, arts] = await Promise.all([
        adminFetch('/admin/kg-pipelines'),
        adminFetch('/admin/kg-pipelines/runs?limit=12'),
        adminFetch('/admin/kg-pipelines/artifacts'),
      ]);
      setKgPipelines(pipes.pipelines || []);
      setKgRuns(runs.runs || []);
      setKgArtifacts(arts);
    } catch {
      /* Control room optional if API old */
    }
  };

  const refreshSourceInventory = async (modeOverride?: string) => {
    setKgInventoryBusy(true);
    try {
      const mode = modeOverride || (kgMode === 'on_demand' ? 'all' : kgMode);
      const res = await adminFetch(
        `/admin/kg-pipelines/sources/inventory?mode=${encodeURIComponent(mode)}`
      );
      setKgInventory(res);
      // Keep selection if still present
      const paths = (res.files || []).map((f: any) => f.path);
      if (selectedSourcePath && !paths.includes(selectedSourcePath)) {
        setSelectedSourcePath(null);
        setSourcePreview(null);
      }
    } catch (e: any) {
      toast.error('Failed to load source inventory', { description: e?.message });
    } finally {
      setKgInventoryBusy(false);
    }
  };

  const openSourcePreview = async (path: string) => {
    setSelectedSourcePath(path);
    try {
      const res = await adminFetch(
        `/admin/kg-pipelines/sources/preview?path=${encodeURIComponent(path)}`
      );
      setSourcePreview(res);
    } catch (e: any) {
      toast.error('Could not preview file', { description: e?.message });
      setSourcePreview(null);
    }
  };

  const handleRunKgPipeline = async (pipelineId: string, opts?: { dryRun?: boolean; targetEnv?: string }) => {
    setKgRunBusy(true);
    const scopeIds: string[] =
      lockedSelectionIds.length > 0
        ? lockedSelectionIds
        : selectionSummary.selected_product_ids ||
          changePreview?.selected_product_ids ||
          [];
    recordAdminAction(
      'pipeline',
      true,
      `${pipelineId} running…`,
      `mode=${kgMode} dry_run=${opts?.dryRun ?? kgDryRun} scope=${scopeIds.join(',') || 'none'}`
    );
    try {
      const dry = opts?.dryRun ?? kgDryRun;
      const target = opts?.targetEnv ?? kgTargetEnv;
      const q = new URLSearchParams({
        mode: kgMode,
        dry_run: String(dry),
        target_env: target,
        use_selection: 'true',
      });
      // Explicit scope — never rely on server default to process everything
      if (scopeIds.length) {
        q.set('product_ids', scopeIds.join(','));
      }
      const res = await adminFetch(`/admin/kg-pipelines/${pipelineId}/run?${q}`, {
        method: 'POST',
      });
      setLastKgRun({ ...res, dry_run: dry, pipeline_id: res.pipeline_id || pipelineId });
      applyChangePreviewPayload(res);
      // Re-apply locked selection after preview refresh (server may reset checkboxes)
      if (scopeIds.length) {
        setLockedSelectionIds(scopeIds);
        try {
          await adminFetch('/admin/pipeline/selection', {
            method: 'POST',
            body: JSON.stringify({
              selections: Object.fromEntries(scopeIds.map((id) => [id, true])),
            }),
          }).then((r) => applyChangePreviewPayload(r));
        } catch {
          /* non-fatal */
        }
      }
      const ok = res.status === 'success' || res.status === 'partial';
      const err0 = (res.errors && res.errors[0]) || '';
      const msg =
        res.message ||
        `${pipelineId}: ${res.status}${err0 ? ' — ' + err0 : ''}${scopeIds.length ? ' · ' + scopeIds.join(',') : ''}`;
      toast[ok ? 'success' : 'error'](msg);
      recordAdminAction('pipeline', ok, `${pipelineId} ${res.status || 'failed'}`, msg, {
        run_id: res.run_id,
        stages: (res.stages || []).map((s: any) => `${s.status}: ${s.name}`),
        dry_run: dry,
        target_env: target,
        product_ids: res.product_ids_filter || scopeIds,
      });
      refreshKgControlRoom();
      refreshSourceInventory();
      await refreshAdminStatus();
      refreshAuditHistory();
      // Materialize step only — do not use bootstrap_all (smoke is step 6)
      if (ok && !dry && (pipelineId === 'knowledge_materialize' || pipelineId === 'incremental_sync')) {
        setWizardStepDone((prev) => ({ ...prev, 5: true }));
        setAdminWizardStep(6);
      }
      // bootstrap_all may fail on smoke even if materialize succeeded — still advance materialize if chain got past materialize
      if (pipelineId === 'bootstrap_all') {
        const stages = res.stages || [];
        const matOk = stages.some(
          (s: any) =>
            String(s.name || '').includes('knowledge_materialize') &&
            (s.status === 'success' || s.status === 'partial')
        );
        const smokeOk = stages.some(
          (s: any) => String(s.name || '').includes('smoke') && s.status === 'success'
        );
        if (matOk && !dry) {
          setWizardStepDone((prev) => ({ ...prev, 5: true }));
          setAdminWizardStep(smokeOk ? 7 : 6);
        }
        if (smokeOk) {
          setWizardStepDone((prev) => ({ ...prev, 6: true }));
        }
      }
      if (ok && pipelineId === 'smoke_validate') {
        setWizardStepDone((prev) => ({ ...prev, 6: true }));
        setAdminWizardStep(7);
      }
      if (ok && pipelineId === 'promote_graph') {
        setWizardStepDone((prev) => ({ ...prev, 8: true }));
        const scope = (res.product_ids_filter || scopeIds || []) as string[];
        setPromoteResult({
          ok: true,
          target: (target as 'staging' | 'production') || 'staging',
          productIds: scope,
          scopeKey: `${target}|${[...scope].sort().join(',')}`,
          message: msg,
          at: new Date().toISOString(),
          runId: res.run_id,
        });
      }
      if (!ok && err0) {
        toast.error('Pipeline blocked', { description: err0 });
      }
    } catch (e: any) {
      recordAdminAction('pipeline', false, `${pipelineId} failed`, e?.message || 'Pipeline run failed');
      toast.error(`${pipelineId} failed`, { description: e?.message || 'Pipeline run failed' });
    } finally {
      setKgRunBusy(false);
    }
  };

  // Auto-refresh admin / ops when entering those views
  useEffect(() => {
    if (activeView === 'admin') {
      refreshAdminStatus();
      refreshChangePreview(true).then(() => {
        refreshIngestPlan({ quiet: true, withStatus: true });
      });
      refreshKgControlRoom();
      refreshSourceInventory();
      refreshAuditHistory();
    }
    if (activeView === 'ops') {
      refreshKgControlRoom();
      qc.invalidateQueries({ queryKey: ['status'] });
      qc.invalidateQueries({ queryKey: ['health'] });
      qc.invalidateQueries({ queryKey: ['batches'] });
    }
  }, [activeView]);

  // Re-scan inventory when mode changes (bootstrap vs incremental packs)
  useEffect(() => {
    if (activeView === 'admin') {
      refreshSourceInventory();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kgMode]);

  // Helper: map recommendation strength to badge class
  const strengthBadge = (s?: string) =>
    s === 'Strong' ? 'badge-ok' : s === 'Moderate' ? 'badge-warn' : s === 'Weak' ? 'badge-error' : 'badge-info';

  // Helper: map symptom match score to badge class
  const matchBadge = (score: number) =>
    score >= 0.6 ? 'badge-ok' : score >= 0.35 ? 'badge-warn' : 'badge-error';

  const examplePrompts = [
    "My washing machine won't spin and water stays in the drum",
    "Dishwasher leaves dishes wet and cold after the cycle",
    "Microwave runs but food stays cold, and I see arcing inside",
  ];

  // Professional React Flow transformer - colors by real node types from Neo4j
  // Supports highlighting the exact diagnosis reasoning path
  // Uses Dagre for automatic hierarchical layout (best practice for path/reasoning graphs per React Flow examples and yFiles KG viz guide)
  const getLayoutedElements = (nodes: Node[], edges: Edge[], direction = 'TB') => {
    const dagreGraph = new dagre.graphlib.Graph();
    dagreGraph.setDefaultEdgeLabel(() => ({}));

    // Tighter packing so whole product subgraph fits in one viewport more often
    dagreGraph.setGraph({
      rankdir: direction,
      nodesep: direction === 'LR' ? 48 : 56,
      ranksep: direction === 'LR' ? 90 : 80,
      edgesep: 24,
      marginx: 24,
      marginy: 24,
    });

    nodes.forEach((node) => {
      const nodeWithDimensions = node as any;
      dagreGraph.setNode(node.id, {
        width: nodeWithDimensions.width || 160,
        height: nodeWithDimensions.height || 44,
      });
    });

    edges.forEach((edge) => {
      dagreGraph.setEdge(edge.source, edge.target);
    });

    dagre.layout(dagreGraph);

    const layoutedNodes = nodes.map((node) => {
      const nodeWithPosition = dagreGraph.node(node.id);
      const w = nodeWithPosition?.width || 160;
      const h = nodeWithPosition?.height || 44;
      return {
        ...node,
        position: {
          x: (nodeWithPosition?.x || 0) - w / 2,
          y: (nodeWithPosition?.y || 0) - h / 2,
        },
      };
    });

    return { nodes: layoutedNodes, edges };
  };

  const buildFlow = (
    g?: any,
    currentTheme: 'dark' | 'light' = 'dark',
    layoutDir: 'TB' | 'LR' = 'TB',
  ): { nodes: Node[]; edges: Edge[] } => {
    if (!g?.nodes?.length) return { nodes: [], edges: [] };

    const typeColors: Record<string, string> = {
      Product:             '#10b981',
      Symptom:             '#3b82f6',
      FailureMode:         '#f59e0b',
      Part:                '#8b5cf6',
      Component:           '#ec4899',
      DiagnosticStep:      '#14b8a6',
      HistoricalResolution:'#64748b',
      Resolution:          '#64748b',
      ErrorCode:           '#f43f5e',
      Model:               '#06b6d4',
      SKU:                 '#a78bfa',
      Asset:               '#84cc16',
      default:             '#64748b',
    };

    const isDark = currentTheme === 'dark';
    const baseTextColor     = isDark ? '#f1f1f3' : '#111113';
    const baseNodeBg        = isDark ? 0.88 : 0.22;
    const baseNodeBorder    = isDark ? 0.9 : 1;

    const initialNodes: Node[] = (g.nodes || []).map((n: any) => {
      let label = n.title || n.name || n.description || n.label || n.id || 'Node';
      if (typeof label === 'string') label = label.split('\n')[0].trim();
      if (label.length > 28) label = label.substring(0, 25) + '...';

      const nodeType = n.type || n.label || 'default';
      const color    = typeColors[nodeType] || typeColors.default;

      const hexToRgb = (hex: string) => {
        const r = parseInt(hex.slice(1,3),16);
        const g = parseInt(hex.slice(3,5),16);
        const b = parseInt(hex.slice(5,7),16);
        return `${r},${g},${b}`;
      };
      const rgb = hexToRgb(color);

      return {
        id: n.id,
        data: {
          label,
          fullLabel: n.title || n.name || n.description || n.id,
          type: nodeType,
          typeColor: color,
          raw: n,
        },
        position: { x: 0, y: 0 },
        width: 160,
        height: 44,
        style: {
          background: `rgba(${rgb},${baseNodeBg})`,
          border: `${isDark ? '1.5px' : '2px'} solid rgba(${rgb},${baseNodeBorder})`,
          color: baseTextColor,
          borderRadius: '10px',
          padding: '8px 12px',
          fontSize: '11px',
          fontWeight: 500,
          width: 160,
          minHeight: 40,
          cursor: 'pointer',
          boxShadow: isDark ? '0 2px 8px rgba(0,0,0,0.35)' : '0 1px 4px rgba(0,0,0,0.08)',
        },
      };
    });

    const edgeBg = isDark ? 'rgba(15,23,42,0.92)' : 'rgba(255,255,255,0.95)';
    const edgeFg = isDark ? '#94a3b8' : '#475569';
    const initialEdges: Edge[] = (g.edges || []).map((e: any, i: number) => ({
      id: e.id || `e${i}`,
      source: e.source,
      target: e.target,
      label: e.label || e.type || '',
      data: { type: e.type || e.label },
      style: { stroke: isDark ? 'rgba(148,163,184,0.55)' : 'rgba(100,116,139,0.65)', strokeWidth: 1.5 },
      animated: false,
      labelBgStyle: { fill: edgeBg, rx: 3, ry: 3, fillOpacity: 0.95 },
      labelStyle: { fill: edgeFg, fontSize: 9, fontWeight: 500 },
    }));

    return getLayoutedElements(initialNodes, initialEdges, layoutDir);
  };

  const [explorerData, setExplorerData] = useState<any>(null);
  const [isLoadingExplorer, setIsLoadingExplorer] = useState(false);
  const [rfInstance, setRfInstance] = useState<any>(null);
  const [lastDiagnosis, setLastDiagnosis] = useState<any>(null);
  const [highlightPath, setHighlightPath] = useState<{ nodes: string[]; edges: string[] } | null>(null);
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [graphLayoutDir, setGraphLayoutDir] = useState<'TB' | 'LR'>('TB');
  const [explorerSearch, setExplorerSearch] = useState('');
  /** Default: full ontology (true Neo4j product neighborhood). Persona = optional preset. */
  const [explorerScope, setExplorerScope] = useState<'full' | 'persona'>('full');
  const [typeFilter, setTypeFilter] = useState<Record<string, boolean>>(() => {
    const init: Record<string, boolean> = {};
    FULL_ONTOLOGY_TYPES.forEach((t) => { init[t] = true; });
    return init;
  });
  const [showEdgeLabels, setShowEdgeLabels] = useState(true);
  const [pathOnlyMode, setPathOnlyMode] = useState(false);
  /** W3C OWL/RDF definition for selected node (and full product diagram) */
  const [rdfEntity, setRdfEntity] = useState<any>(null);
  const [rdfEntityLoading, setRdfEntityLoading] = useState(false);
  const [rdfTab, setRdfTab] = useState<'class' | 'instance' | 'combined'>('combined');
  const [productTurtle, setProductTurtle] = useState<string | null>(null);
  const [productTurtleOpen, setProductTurtleOpen] = useState(false);
  /** When true, skip the generic auto-load that would wipe a pending diagnosis path highlight */
  const skipExplorerAutoLoadRef = useRef(false);
  /** Cypher + hop traversal for the active diagnosis path (Explorer explain panel) */
  const [pathExplain, setPathExplain] = useState<{
    cypher_queries?: any[];
    traversal?: any[];
    params?: any;
    product_id?: string;
    case_label?: string;
  } | null>(null);
  const [pathExplainTab, setPathExplainTab] = useState<'traversal' | 'cypher'>('traversal');
  const [pathExplainOpen, setPathExplainOpen] = useState(true);

  // Only read current theme class on mount (set by inline script in layout)
  // We deliberately avoid writing to <html> here to prevent hydration mismatches.
  useEffect(() => {
    const isDark = document.documentElement.classList.contains('dark');
    setTheme(isDark ? 'dark' : 'light');
  }, []);

  const toggleTheme = () => {
    const root = document.documentElement;
    const isCurrentlyDark = root.classList.contains('dark');
    const newTheme = isCurrentlyDark ? 'light' : 'dark';

    if (newTheme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }

    localStorage.setItem('theme', newTheme);
    setTheme(newTheme);  // update state for button icon
  };

  /**
   * Load product subgraph and optionally overlay a diagnosis path highlight.
   * @param diagnosisOverride — specific chat case diagnosis (do not rely only on lastDiagnosis)
   * @param clearHighlight — false when reloading graph while re-applying a path
   */
  const loadExplorer = async (
    pid = selectedProduct,
    highlight = false,
    diagnosisOverride?: any,
    clearHighlight = true,
  ) => {
    const diagnosis = diagnosisOverride || lastDiagnosis?.diagnosis;
    const productId = pid || diagnosis?.product_id || explorerProductId;

    // ── HIGHLIGHT PATH (from Diagnosis Chat → Explorer Exact Path) ─────────
    // Keep the full product neighborhood; only dim nodes not on the path.
    // Does NOT wipe explorerData first (avoids race with auto-load clearing highlight).
    if (highlight) {
      if (!diagnosis || diagnosis.context_blocked) {
        toast.error('No diagnosis path available for this case');
        return;
      }
      skipExplorerAutoLoadRef.current = true;
      setIsLoadingExplorer(true);
      try {
        if (productId) setExplorerProductId(productId);

        const symptomIds: string[] =
          (diagnosis.traversed_symptom_ids?.length
            ? diagnosis.traversed_symptom_ids
            : (diagnosis.matched_symptoms || []).map((s: any) => s.symptom_id)
          ).filter(Boolean);
        const fmId =
          diagnosis.traversed_fm_id ||
          diagnosis.ranked_failure_modes?.[0]?.failure_mode_id ||
          undefined;

        // Always load the product graph for this diagnosis product (correct product scope)
        let graphData = await api.getProductGraph(productId);
        if (!graphData?.nodes?.length) {
          graphData = await api.getOntology();
        }
        setExplorerData(graphData);

        // Prefer API diagnosis subgraph; fall back to embedded graph_subgraph from diagnose response
        let pathNodes: string[] = [];
        let pathEdges: string[] = [];
        let explain: any = null;
        try {
          const pathData = await api.getDiagnosisSubgraph(productId, symptomIds, fmId);
          pathNodes = (pathData.nodes || []).map((n: any) => n.id as string);
          pathEdges = (pathData.edges || []).map(
            (e: any) => (e.id as string) || `${e.source}|${e.target}`,
          );
          explain = {
            cypher_queries: pathData.cypher_queries,
            traversal: pathData.traversal,
            params: pathData.params || {
              product_id: productId,
              symptom_ids: symptomIds,
              failure_mode_id: fmId,
            },
            product_id: productId,
            case_label: diagnosis.product_name || productId,
          };
        } catch {
          /* fall through */
        }
        if (!pathNodes.length && diagnosis.graph_subgraph?.nodes?.length) {
          const gs = diagnosis.graph_subgraph;
          pathNodes = (gs.nodes || [])
            .filter((n: any) => n.highlight !== false)
            .map((n: any) => n.id as string);
          pathEdges = (gs.edges || [])
            .filter((e: any) => e.highlight)
            .map((e: any) => (e.id as string) || `${e.source}|${e.target}`);
          if (!pathNodes.length) {
            pathNodes = (gs.nodes || []).map((n: any) => n.id as string);
          }
          if (!explain && (gs.cypher_queries || gs.traversal)) {
            explain = {
              cypher_queries: gs.cypher_queries,
              traversal: gs.traversal,
              params: gs.params,
              product_id: productId,
              case_label: diagnosis.product_name || productId,
            };
          }
        }
        // Last resort: build path ids from diagnosis fields
        if (!pathNodes.length) {
          pathNodes = [
            `Product:${productId}`,
            ...symptomIds.map((s: string) => (s.includes(':') ? s : `Symptom:${s}`)),
            ...(fmId ? [fmId.includes(':') ? fmId : `FailureMode:${fmId}`] : []),
          ];
        }

        // Always attach traversal/cypher explain for the case (even if API omitted fields, rebuild client-side summary)
        if (!explain?.traversal?.length) {
          const top = (diagnosis.ranked_failure_modes || [])[0];
          const hops: any[] = [
            { hop: 1, label: 'Start at product', to: `Product:${productId}`, detail: diagnosis.product_name || productId },
          ];
          symptomIds.forEach((sid: string, i: number) => {
            const ms = (diagnosis.matched_symptoms || []).find((s: any) => s.symptom_id === sid);
            hops.push({
              hop: hops.length + 1,
              from: `Product:${productId}`,
              rel: 'HAS_SYMPTOM',
              to: `Symptom:${sid}`,
              label: 'Observe symptom',
              detail: ms?.description || sid,
            });
          });
          if (fmId) {
            hops.push({
              hop: hops.length + 1,
              from: `Product:${productId}`,
              rel: 'CAN_HAVE',
              to: `FailureMode:${fmId}`,
              label: 'Top failure mode',
              detail: top?.name || fmId,
            });
            symptomIds.forEach((sid: string) => {
              hops.push({
                hop: hops.length + 1,
                from: `Symptom:${sid}`,
                rel: 'INDICATES',
                to: `FailureMode:${fmId}`,
                label: 'Graph likelihood edge',
                detail: 'INDICATES',
              });
            });
          }
          explain = {
            ...(explain || {}),
            product_id: productId,
            case_label: diagnosis.product_name || productId,
            params: { product_id: productId, symptom_ids: symptomIds, failure_mode_id: fmId },
            traversal: hops,
            cypher_queries: explain?.cypher_queries || [],
          };
        }
        setPathExplain(explain);
        setPathExplainOpen(true);
        setPathExplainTab('traversal');

        if (pathNodes.length > 0) {
          setHighlightPath({ nodes: pathNodes, edges: pathEdges });
          setPathOnlyMode(false); // full graph with path glow (original UX)
          toast.success('Diagnosis path highlighted', {
            description: `${pathNodes.length} nodes on path · product ${productId}`,
          });
          setTimeout(() => {
            try {
              // Prefer fitting path nodes when React Flow has them
              const pathSet = new Set(pathNodes);
              const rfNodes = (rfInstance?.getNodes?.() || []).filter((n: any) => pathSet.has(n.id));
              if (rfNodes.length && rfInstance?.fitView) {
                rfInstance.fitView({ nodes: rfNodes, padding: 0.35, duration: 320, maxZoom: 1.2 });
              } else {
                rfInstance?.fitView?.({ padding: 0.2, duration: 300 });
              }
            } catch {
              /* ignore */
            }
          }, 220);
        } else {
          toast.message('Graph loaded', { description: 'Could not resolve path IDs — showing full product graph' });
        }
      } catch (e: any) {
        toast.error('Failed to highlight diagnosis path', { description: e?.message });
      } finally {
        setIsLoadingExplorer(false);
        // Allow auto-load again only after a tick (avoid wipe)
        setTimeout(() => {
          skipExplorerAutoLoadRef.current = false;
        }, 400);
      }
      return;
    }

    // ── FULL GRAPH LOAD (no path) ──────────────────────────────────────────
    // Clears highlight only when intentionally loading a plain product view.
    setIsLoadingExplorer(true);
    if (clearHighlight) {
      setHighlightPath(null);
      setPathExplain(null);
    }
    try {
      const data = await api.getProductGraph(productId);
      if (data?.nodes?.length) {
        setExplorerData(data);
        setTimeout(() => rfInstance?.fitView?.({ padding: 0.18, duration: 250 }), 150);
        return;
      }
      const o = await api.getOntology();
      setExplorerData(o);
    } catch {
      try {
        const o = await api.getOntology();
        setExplorerData(o);
      } catch {
        setExplorerData({ nodes: [{ id: 'p', label: 'Product' }], edges: [] });
      }
    } finally {
      setIsLoadingExplorer(false);
    }
  };

  /**
   * Diagnosis Chat → Explorer: open product graph with this case's path highlighted.
   * Preserves RDF inspector and full-ontology features; only restores path UX.
   */
  const openExplorerWithDiagnosisPath = (diagnosis: any, fullResponse?: any) => {
    if (!diagnosis || diagnosis.context_blocked) {
      toast.error('No graph path for this response');
      return;
    }
    const pid = diagnosis.product_id || explorerProductId || chatProductId;
    // Keep case-specific diagnosis as source of truth for path extraction
    setLastDiagnosis({
      ...(fullResponse || {}),
      diagnosis,
      product_id: pid,
    });
    skipExplorerAutoLoadRef.current = true;
    setExplorerProductId(pid);
    setActiveView('explorer');
    // Defer so view switch + product id settle without auto-load clearing the path
    setTimeout(() => {
      loadExplorer(pid, true, diagnosis, false);
    }, 50);
  };

  // Auto load product subgraph when entering explorer — never wipe a pending path highlight
  useEffect(() => {
    if (activeView !== 'explorer') return;
    if (skipExplorerAutoLoadRef.current) return;
    if (!explorerData) {
      loadExplorer(explorerProductId, false, undefined, true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeView, explorerProductId]);

  // When switching to persona scope, apply that role's type preset; full = all ontology types
  useEffect(() => {
    if (explorerScope === 'full') {
      const next: Record<string, boolean> = {};
      FULL_ONTOLOGY_TYPES.forEach((t) => { next[t] = true; });
      setTypeFilter(next);
      return;
    }
    const allowed = PERSONA_NODE_TYPES[role] || PERSONA_NODE_TYPES.analyst;
    const next: Record<string, boolean> = {};
    FULL_ONTOLOGY_TYPES.forEach((t) => { next[t] = allowed.includes(t); });
    setTypeFilter(next);
  }, [role, explorerScope]);

  const fitGraph = (padding = 0.18) => {
    if (!rfInstance) return;
    try {
      rfInstance.fitView({ padding, duration: 280, minZoom: 0.08, maxZoom: 1.5 });
    } catch { /* ignore */ }
  };

  const loadRdfForNode = async (node: any, productId?: string) => {
    const raw = node?.data?.raw || {};
    const label = (node?.data?.type || raw.label || raw.type || 'Product') as string;
    const entityId = (raw.entity_id || String(node?.id || '').split(':').slice(-1)[0] || '') as string;
    if (!entityId) {
      setRdfEntity(null);
      return;
    }
    setRdfEntityLoading(true);
    try {
      const data = await api.getRdfEntity(label, entityId, productId || explorerProductId);
      setRdfEntity(data);
      setRdfTab('combined');
    } catch (e: any) {
      setRdfEntity({ ok: false, error: e?.message || 'RDF load failed' });
    } finally {
      setRdfEntityLoading(false);
    }
  };

  const loadProductTurtle = async () => {
    try {
      const data = await api.getRdfProduct(explorerProductId, true);
      setProductTurtle(data.turtle || '');
      setProductTurtleOpen(true);
      toast.success('Loaded full product OWL/RDF diagram');
    } catch (e: any) {
      toast.error('Could not load product Turtle', { description: e?.message });
    }
  };

  const onNodeClick = (_event: any, node: any) => {
    setSelectedNode(node);
    loadRdfForNode(node, explorerProductId);
    // Focus selected node without losing overall context
    if (rfInstance && node?.position) {
      try {
        const w = (node.width as number) || 160;
        const h = (node.height as number) || 44;
        rfInstance.setCenter(node.position.x + w / 2, node.position.y + h / 2, {
          zoom: Math.max(rfInstance.getZoom(), 0.85),
          duration: 280,
        });
      } catch { /* ignore */ }
    }
  };

  // Keyboard: arrows pan, f fit, +/- zoom, Escape clear selection
  useEffect(() => {
    if (activeView !== 'explorer') return;
    const handleKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      if (!rfInstance) return;
      const step = e.shiftKey ? 220 : 90;
      const vp = rfInstance.getViewport();
      const moves: Record<string, { x: number; y: number }> = {
        ArrowLeft:  { x: vp.x + step, y: vp.y },
        ArrowRight: { x: vp.x - step, y: vp.y },
        ArrowUp:    { x: vp.x, y: vp.y + step },
        ArrowDown:  { x: vp.x, y: vp.y - step },
      };
      if (moves[e.key]) {
        e.preventDefault();
        rfInstance.setViewport({ ...moves[e.key], zoom: vp.zoom }, { duration: 100 });
      } else if (e.key === 'f' || e.key === 'F') {
        e.preventDefault();
        fitGraph();
      } else if (e.key === '=' || e.key === '+') {
        e.preventDefault();
        rfInstance.zoomIn?.({ duration: 120 });
      } else if (e.key === '-' || e.key === '_') {
        e.preventDefault();
        rfInstance.zoomOut?.({ duration: 120 });
      } else if (e.key === 'Escape') {
        setSelectedNode(null);
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [activeView, rfInstance]);

  // Stable layout — data / theme / direction
  const baseFlow = useMemo(
    () => buildFlow(explorerData || ontologyData, theme, graphLayoutDir),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [explorerData, ontologyData, theme, graphLayoutDir],
  );

  // Type filters + search + optional path-only (default scope = full ontology)
  const filteredFlow = useMemo(() => {
    const activeTypes = new Set(
      Object.entries(typeFilter).filter(([, on]) => on).map(([t]) => t),
    );
    // If filter map empty, show everything present in the graph
    const filterActive = activeTypes.size > 0;

    let nodes = baseFlow.nodes.filter((n) => {
      const t = (n.data as any)?.type || 'default';
      if (!filterActive) return true;
      // Always keep unknown types visible (schema evolution)
      if (!FULL_ONTOLOGY_TYPES.includes(t as any) && t !== 'default') return true;
      return activeTypes.has(t);
    });

    if (pathOnlyMode && highlightPath?.nodes?.length) {
      const pathSet = new Set(highlightPath.nodes);
      nodes = nodes.filter((n) => pathSet.has(n.id));
    }

    const q = explorerSearch.trim().toLowerCase();
    if (q) {
      nodes = nodes.filter((n) => {
        const d = n.data as any;
        const hay = `${d?.label || ''} ${d?.fullLabel || ''} ${n.id} ${d?.type || ''}`.toLowerCase();
        return hay.includes(q);
      });
    }

    const ids = new Set(nodes.map((n) => n.id));
    let edges = baseFlow.edges.filter((e) => ids.has(e.source) && ids.has(e.target));
    if (pathOnlyMode && highlightPath?.edges?.length) {
      const pe = new Set(highlightPath.edges);
      edges = edges.filter((e) => pe.has(e.id) || pe.has(`${e.source}|${e.target}`));
    }
    if (!showEdgeLabels) {
      edges = edges.map((e) => ({ ...e, label: undefined }));
    }
    // Re-layout the visible subset so filters/path-only still fill the viewport cleanly
    if (nodes.length && nodes.length < baseFlow.nodes.length) {
      return getLayoutedElements(nodes, edges, graphLayoutDir);
    }
    return { nodes, edges };
  }, [baseFlow, role, typeFilter, pathOnlyMode, highlightPath, explorerSearch, showEdgeLabels, graphLayoutDir]);

  const flow = useMemo(
    () => applyHighlight(filteredFlow.nodes, filteredFlow.edges, highlightPath),
    [filteredFlow, highlightPath],
  );

  // Refit when layout/data/filters change so the whole graph is visible
  // When a diagnosis path is active, fit to path nodes instead of wiping the highlight UX
  useEffect(() => {
    if (activeView !== 'explorer' || !rfInstance || flow.nodes.length === 0) return;
    const t = setTimeout(() => {
      if (highlightPath?.nodes?.length) {
        const pathSet = new Set(highlightPath.nodes);
        const pathNodes = flow.nodes.filter(
          (n) => pathSet.has(n.id) || [...pathSet].some((hid) => n.id.includes(hid) || hid.includes(n.id)),
        );
        try {
          if (pathNodes.length) {
            rfInstance.fitView({ nodes: pathNodes, padding: 0.35, duration: 320, maxZoom: 1.15 });
            return;
          }
        } catch { /* fall through */ }
      }
      fitGraph(0.2);
    }, 100);
    return () => clearTimeout(t);
  }, [activeView, flow.nodes.length, graphLayoutDir, explorerData, pathOnlyMode, role, highlightPath]);

  // Apply theme class when state changes (toggle calls it directly for immediate effect)

  // Cases / Agent view data
  const escalations = (claimsData?.claims || []).slice(0, 6); // reuse claims as proxy for demo

  return (
    <div className="flex h-screen overflow-hidden bg-white text-[#111111] dark:bg-[#050505] dark:text-[#f1f1f3]">
      {/* Modern Glass Sidebar */}
      <div className="w-72 border-r border-white/10 flex flex-col glass">
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-emerald-400 to-violet-500 flex items-center justify-center">
              <Zap className="w-5 h-5 text-black" />
            </div>
            <div>
              <div className="font-semibold tracking-tight text-xl">WarrantyGraph</div>
              <div className="text-[10px] text-white/50 -mt-0.5">ENTERPRISE AI DIAGNOSTICS · 2026</div>
            </div>
          </div>
        </div>

        {/* Role Switcher — 2026 role-based adaptive UX */}
        <div className="p-4 border-b border-white/10">
          <div className="text-[10px] uppercase tracking-[1px] text-white/40 mb-2 px-1">VIEW AS</div>
          <div className="flex gap-1">
            {(['customer', 'agent', 'analyst'] as const).map(r => (
              <button
                key={r}
                onClick={() => setRole(r)}
                className={`flex-1 rounded-lg py-1.5 text-xs font-medium transition ${role === r ? 'bg-white text-black dark:bg-gray-800 dark:text-white' : 'glass hover:bg-white/5 dark:hover:bg-white/10'}`}
              >
                {r === 'customer' && 'Customer'}
                {r === 'agent' && 'Agent'}
                {r === 'analyst' && 'Analyst'}
              </button>
            ))}
          </div>
        </div>

        {/* Nav — Clean, modern, purposeful */}
        <div className="p-3 space-y-1 text-sm">
          {[
            { id: 'chat', label: 'Diagnosis Chat', icon: MessageCircle, desc: 'Explainable diagnosis' },
            { id: 'cases', label: 'Agent Cases', icon: Users, desc: 'Escalations & claims' },
            { id: 'explorer', label: 'Knowledge Explorer', icon: GitBranch, desc: 'Interactive graph' },
            { id: 'ops', label: 'Enterprise Ops', icon: Activity, desc: 'Pipelines & lineage' },
            { id: 'admin', label: 'Admin', icon: Shield, desc: 'ETL, Onboard & Promote' },
          ].map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveView(item.id as View)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition group ${isActive ? 'bg-white/10 text-white dark:bg-white/10 dark:text-white' : 'hover:bg-white/5 text-white/80 dark:hover:bg-white/10 dark:text-white/80'}`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-[13px]">{item.label}</div>
                  <div className="text-[10px] text-white/40 truncate">{item.desc}</div>
                </div>
                {isActive && <ChevronRight className="w-3.5 h-3.5 text-white/40" />}
              </button>
            );
          })}
          <Link
            href="/study"
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition hover:bg-emerald-500/10 text-emerald-200/90 border border-emerald-500/20 mt-2"
          >
            <GraduationCap className="w-4 h-4 shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="font-medium text-[13px]">Study Lab</div>
              <div className="text-[10px] text-white/40 truncate">RDF · OWL · Cypher · agents</div>
            </div>
            <ChevronRight className="w-3.5 h-3.5 text-emerald-400/50" />
          </Link>
        </div>

        <div className="mt-auto p-4 text-[10px] text-white/40 dark:text-white/40 border-t border-white/10 dark:border-white/10">
          GraphRAG + FMEA + Provenance<br />
          Neo4j · LangGraph · FastAPI
        </div>
      </div>

      {/* Main Area */}
      <div className="flex-1 flex flex-col min-w-0 min-h-0">
        {/* Glass Topbar */}
        <div className="h-14 shrink-0 border-b border-white/10 glass flex items-center justify-between px-5 text-sm z-50">
          <div className="flex items-center gap-3">
            <div className="font-mono text-xs px-2 py-px rounded bg-white/5 dark:bg-white/5 border border-white/10 dark:border-white/10">
              {role.toUpperCase()}
            </div>
            <div className="text-white/60 text-xs flex items-center gap-1.5">
              <div className={`w-1.5 h-1.5 rounded-full ${health?.status === 'ok' ? 'bg-emerald-400' : 'bg-amber-400'}`} />
              {health?.status === 'ok' ? 'SYSTEM HEALTHY' : 'CHECKING...'}
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <div className="glass px-3 py-1 rounded-full flex items-center gap-2 border border-white/10">
              <Shield className="w-3.5 h-3.5" /> Graph-native • No LLM required
            </div>
            <button
              onClick={toggleTheme}
              className="btn btn-ghost px-3 py-1 text-xs flex items-center gap-1 border border-white/10 dark:border-white/10 border-black/10 text-current"
              title="Toggle dark / light theme"
            >
              {theme === 'dark' ? '☀️ Light' : '🌙 Dark'}
            </button>
            <button onClick={() => window.location.reload()} className="btn btn-ghost px-3 py-1 text-xs">
              <RefreshCw className="w-3.5 h-3.5" /> Reload
            </button>
          </div>
        </div>

        {/* View Content — chat & explorer are full-viewport; other views scroll */}
        <div
          className={
            activeView === 'chat' || activeView === 'explorer'
              ? 'flex-1 min-h-0 overflow-hidden flex flex-col'
              : 'flex-1 min-h-0 overflow-auto p-6'
          }
        >
          <AnimatePresence mode="wait">
            {/* ==================== CHAT — AI-NATIVE CONVERSATIONAL ==================== */}
            {activeView === 'chat' && (
              <div className="flex-1 min-h-0 flex flex-col w-full max-w-[1200px] mx-auto px-6 pt-4">
                {/* Header + asset-first context — stays compact so transcript/composer remain visible */}
                <div className="shrink-0 space-y-2 pb-2">
                  <div className="flex flex-wrap items-end justify-between gap-2">
                    <div className="min-w-0">
                      <div className="text-2xl md:text-3xl font-semibold tracking-tighter">Diagnosis Chat</div>
                      <p className="text-white/55 text-xs md:text-sm mt-0.5">
                        Bind registered appliance first — diagnosis is scoped to that product only.
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-1.5 items-center">
                      <button
                        type="button"
                        className={`btn text-xs py-1 ${sessionMode === 'customer' ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => setSessionMode('customer')}
                      >
                        Customer session
                      </button>
                      <button
                        type="button"
                        className={`btn text-xs py-1 ${sessionMode === 'anonymous' ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => setSessionMode('anonymous')}
                      >
                        Anonymous demo
                      </button>
                    </div>
                  </div>

                  {sessionMode === 'customer' ? (
                    <div className="space-y-2">
                      <div className="glass flex flex-wrap items-center gap-2 px-3 py-2 rounded-xl text-sm">
                        <div className="font-medium shrink-0 text-xs text-white/60">Customer</div>
                        <select
                          className="input w-56 text-sm py-1.5"
                          value={selectedCustomerId}
                          onChange={(e) => {
                            setSelectedCustomerId(e.target.value);
                            setAssetPickerExpanded(true);
                          }}
                          title="CRM customer"
                        >
                          {customersList.map((c: any) => (
                            <option key={c.customer_id} value={c.customer_id}>
                              {c.name} ({c.customer_id})
                            </option>
                          ))}
                        </select>
                        {assetsLoading && <span className="text-xs text-white/40">Loading assets…</span>}
                        <span className="text-[11px] text-white/35 ml-auto hidden sm:inline">
                          {customerAssets.length} registered appliance{customerAssets.length === 1 ? '' : 's'}
                        </span>
                      </div>

                      {/* Compact bound-asset bar (always when selected) */}
                      {selectedAssetRecord && (
                        <div className="glass rounded-xl px-3 py-2 text-xs flex flex-wrap gap-x-3 gap-y-1 items-center border border-emerald-500/25">
                          <span className="text-[10px] uppercase tracking-wide text-emerald-300/80">Bound</span>
                          <span className="font-medium truncate max-w-[14rem]">
                            {productNameFor(selectedAssetRecord.product_id)}
                          </span>
                          <span className="font-mono text-white/55">{selectedAssetRecord.product_id}</span>
                          <span className="text-white/40 truncate max-w-[10rem]">
                            {selectedAssetRecord.asset_id}
                          </span>
                          <span
                            className={`badge text-[10px] ${
                              String(selectedAssetRecord.warranty_status || '').toLowerCase() === 'active'
                                ? 'badge-ok'
                                : 'badge-warn'
                            }`}
                          >
                            Warranty {selectedAssetRecord.warranty_status || 'unknown'}
                          </span>
                          <button
                            type="button"
                            className="btn btn-secondary text-[11px] py-0.5 px-2 ml-auto"
                            onClick={() => setAssetPickerExpanded((v) => !v)}
                          >
                            {assetPickerExpanded ? 'Hide list' : `Change appliance (${customerAssets.length})`}
                            {assetPickerExpanded ? (
                              <ChevronDown className="w-3 h-3" />
                            ) : (
                              <ChevronRight className="w-3 h-3" />
                            )}
                          </button>
                        </div>
                      )}

                      {/* Scrollable compact list — only when expanded or nothing selected */}
                      {(assetPickerExpanded || !selectedAssetRecord) && (
                        <div className="asset-picker-panel">
                          <div className="flex items-center justify-between px-1 mb-1">
                            <div className="text-[10px] uppercase tracking-widest text-white/40">
                              Registered appliances — select one
                            </div>
                            {selectedAssetRecord && customerAssets.length > 3 && (
                              <button
                                type="button"
                                className="text-[11px] text-white/45 hover:text-white/70"
                                onClick={() => setAssetPickerExpanded(false)}
                              >
                                Collapse
                              </button>
                            )}
                          </div>
                          {/* Native select for dense switch when many assets */}
                          {customerAssets.length > 4 && (
                            <select
                              className="input w-full text-sm py-1.5 mb-2"
                              value={selectedAssetRecord?.asset_id || ''}
                              onChange={(e) => {
                                const next = customerAssets.find((a: any) => a.asset_id === e.target.value);
                                if (next) {
                                  setSelectedAssetRecord(next);
                                  setAssetPickerExpanded(false);
                                }
                              }}
                              title="Quick select appliance"
                            >
                              {customerAssets.map((a: any) => (
                                <option key={a.asset_id} value={a.asset_id}>
                                  {productNameFor(a.product_id)} · {a.asset_id} · {a.product_id}
                                </option>
                              ))}
                            </select>
                          )}
                          <div className="asset-picker-scroll grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-1.5">
                            {customerAssets.map((a: any) => {
                              const active = selectedAssetRecord?.asset_id === a.asset_id;
                              const warrantyOk = String(a.warranty_status || '').toLowerCase() === 'active';
                              return (
                                <button
                                  key={a.asset_id}
                                  type="button"
                                  onClick={() => {
                                    setSelectedAssetRecord(a);
                                    setAssetPickerExpanded(false);
                                  }}
                                  className={`text-left rounded-lg px-2.5 py-2 border transition ${
                                    active
                                      ? 'border-emerald-500/50 bg-emerald-500/10'
                                      : 'border-white/10 bg-white/5 hover:border-white/25'
                                  }`}
                                >
                                  <div className="flex items-start justify-between gap-2">
                                    <div className="min-w-0">
                                      <div className="font-medium text-xs truncate">
                                        {productNameFor(a.product_id)}
                                      </div>
                                      <div className="text-[10px] font-mono text-white/45 truncate">
                                        {a.asset_id} · {a.product_id}
                                      </div>
                                    </div>
                                    <span className={`badge text-[9px] shrink-0 ${warrantyOk ? 'badge-ok' : 'badge-warn'}`}>
                                      {a.warranty_status || '?'}
                                    </span>
                                  </div>
                                </button>
                              );
                            })}
                            {!customerAssets.length && !assetsLoading && (
                              <div className="text-sm text-white/40 col-span-full p-2">
                                No registered assets for this customer.
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="glass flex flex-wrap items-center gap-2 px-3 py-2 rounded-xl text-sm">
                      <div className="font-medium text-xs text-white/60">Appliance type</div>
                      <select
                        className="input w-56 text-sm py-1.5"
                        value={anonymousProductId}
                        onChange={(e) => setAnonymousProductId(e.target.value)}
                      >
                        {productsList.map((p: any) => (
                          <option key={p.product_id} value={p.product_id}>{p.name}</option>
                        ))}
                      </select>
                      <div className="text-[11px] text-white/40">No CRM asset — product pick only.</div>
                    </div>
                  )}

                  {/* Soft mismatch confirm */}
                  {pendingMismatch && (
                    <div className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-3 space-y-2">
                      <div className="font-semibold text-amber-200 flex items-center gap-2 text-sm">
                        <AlertTriangle className="w-4 h-4" />
                        Confirm appliance
                      </div>
                      <p className="text-xs text-white/70">
                        {(pendingMismatch.diagnosis?.warnings || [])[0]?.replace(/\*\*/g, '') ||
                          'Your description may refer to a different appliance than the one selected.'}
                      </p>
                      <div className="flex flex-wrap gap-2">
                        <button type="button" className="btn btn-primary text-xs" onClick={handleSwitchToSuggestedProduct}>
                          Switch to matching appliance
                        </button>
                        <button type="button" className="btn btn-secondary text-xs" onClick={handleForceKeepAppliance}>
                          Keep this appliance &amp; diagnose
                        </button>
                        <button type="button" className="btn btn-ghost text-xs" onClick={() => setPendingMismatch(null)}>
                          Dismiss
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Messages — only this region scrolls; composer stays put below */}
                <div ref={chatMessagesScrollRef} className="flex-1 min-h-0 overflow-y-auto space-y-6 pr-1 pb-2 chat-messages-scroll">
                  {messages.map((msg, idx) => (
                    <div key={idx} className={msg.role === 'user' ? 'flex justify-end' : ''}>
                      <div className={`max-w-[820px] ${msg.role === 'user' ? 'bg-white/5 rounded-3xl px-5 py-3' : ''}`}>
                        {msg.role === 'user' ? (
                          <div className="text-sm bg-white/5 px-5 py-3 rounded-3xl">{msg.content}</div>
                        ) : (
                          <div>
                            {/* Show raw response only if no rich diagnosis data; otherwise use structured card for enterprise presentation */}
                            {!msg.diagnosis && msg.content && (
                              <div className="text-sm text-white/70 mb-3 whitespace-pre-wrap">{msg.content}</div>
                            )}

                            {msg.diagnosis && (
                              <div className="diagnosis-card">
                                {/* Hard context block — no failure modes claimed */}
                                {msg.diagnosis.context_blocked && (
                                  <div className={`rounded-xl border p-4 mb-2 ${
                                    String(msg.diagnosis.context_block_code || '').startsWith('soft_')
                                      ? 'border-amber-500/40 bg-amber-500/10'
                                      : 'border-rose-500/40 bg-rose-500/10'
                                  }`}>
                                    <div className={`font-semibold flex items-center gap-2 ${
                                      String(msg.diagnosis.context_block_code || '').startsWith('soft_')
                                        ? 'text-amber-200'
                                        : 'text-rose-300'
                                    }`}>
                                      <AlertTriangle className="w-4 h-4" />
                                      {String(msg.diagnosis.context_block_code || '').startsWith('soft_')
                                        ? 'Confirm appliance before diagnosing'
                                        : 'Diagnosis withheld — binding conflict'}
                                    </div>
                                    <div className="text-xs opacity-70 mt-1 font-mono">
                                      {msg.diagnosis.context_block_code || 'context_blocked'}
                                    </div>
                                    <ul className="mt-2 text-sm text-white/70 space-y-1 list-disc pl-4">
                                      {(msg.diagnosis.warnings || []).map((w: string, wi: number) => (
                                        <li key={wi}>{w.replace(/\*\*/g, '')}</li>
                                      ))}
                                    </ul>
                                    {String(msg.diagnosis.context_block_code || '').startsWith('soft_') && (
                                      <div className="text-xs text-white/50 mt-3">
                                        Use the amber panel above to switch appliance or keep this unit.
                                      </div>
                                    )}
                                  </div>
                                )}

                                {/* Header: product + recommendation strength */}
                                <div className="flex items-start justify-between gap-4">
                                  <div className="flex-1">
                                    <div className="font-semibold text-xl">{msg.diagnosis.product_name || msg.diagnosis.product_id || 'Unknown appliance'}</div>
                                    {msg.diagnosis.asset_id && (
                                      <div className="text-xs text-white/50 mt-0.5">
                                        {msg.diagnosis.asset_id} · {msg.diagnosis.model_number} {msg.diagnosis.sku_id}
                                      </div>
                                    )}
                                  </div>
                                  {/* Recommendation strength (primary) + posterior (secondary) */}
                                  <div className="text-right shrink-0">
                                    {msg.diagnosis.recommendation_strength ? (
                                      <>
                                        <div
                                          className={`inline-block px-2.5 py-1 rounded-lg text-xs font-bold uppercase tracking-wider mb-1 ${strengthBadge(msg.diagnosis.recommendation_strength)}`}
                                        >
                                          {msg.diagnosis.recommendation_strength}
                                        </div>
                                        <div className="text-[10px] text-white/40 mt-0.5">recommendation</div>
                                      </>
                                    ) : (
                                      <>
                                        <div className="text-[10px] text-white/50">CONFIDENCE</div>
                                        <div className="text-4xl font-semibold tabular-nums tracking-[-2px] text-emerald-400">
                                          {((msg.diagnosis.confidence || 0) * 100).toFixed(0)}%
                                        </div>
                                      </>
                                    )}
                                  </div>
                                </div>

                                  {!msg.diagnosis.context_blocked && (
                                  <div className="grid grid-cols-3 gap-2 text-center">
                                    <div className="score-tile">
                                      <div className="text-[9px] uppercase tracking-widest text-white/40 mb-0.5">POSTERIOR</div>
                                      <div className="font-mono text-base font-semibold text-emerald-400">
                                        {((msg.diagnosis.confidence || 0) * 100).toFixed(0)}%
                                      </div>
                                      <div className="text-[9px] text-white/30">Bayesian P(fm|symptoms)</div>
                                    </div>
                                    <div className="score-tile">
                                      <div className="text-[9px] uppercase tracking-widest text-white/40 mb-0.5">GRAPH LINK</div>
                                      <div className="font-mono text-base font-semibold text-blue-400">
                                        {((msg.diagnosis.graph_confidence || 0) * 100).toFixed(0)}%
                                      </div>
                                      <div className="text-[9px] text-white/30">INDICATES edge P(s|fm)</div>
                                    </div>
                                    <div className="score-tile">
                                      <div className="text-[9px] uppercase tracking-widest text-white/40 mb-0.5">TEXT MATCH</div>
                                      <div className="font-mono text-base font-semibold text-amber-400">
                                        {((msg.diagnosis.language_confidence || 0) * 100).toFixed(0)}%
                                      </div>
                                      <div className="text-[9px] text-white/30">Query→catalog lexical</div>
                                    </div>
                                  </div>
                                  )}

                                {/* No product identified — helpful message */}
                                {!msg.diagnosis.product_id && (
                                  <div className="no-product-panel">
                                    <div className="font-medium text-amber-400 mb-1">⚠ No appliance identified</div>
                                    <div className="text-xs node-panel-muted">
                                      The query did not match any product in the knowledge graph.
                                      Try describing a specific appliance type (e.g. &quot;washing machine&quot;, &quot;dishwasher&quot;, &quot;microwave&quot;) and symptoms.
                                    </div>
                                  </div>
                                )}

                                {/* Matched Symptoms */}
                                {msg.diagnosis.matched_symptoms && msg.diagnosis.matched_symptoms.length > 0 && (
                                  <div>
                                    <div className="text-xs uppercase tracking-widest mb-1.5 text-white/50">
                                      MATCHED SYMPTOMS
                                      <span className="normal-case tracking-normal font-normal text-white/30 ml-2">
                                        (text match score = how closely your words match catalog symptom descriptions)
                                      </span>
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                      {msg.diagnosis.matched_symptoms.map((s: any, si: number) => (
                                        <div key={s.symptom_id || si} className={`badge ${matchBadge(s.match_score)}`}>
                                          {s.description}
                                          <span className="ml-1.5 opacity-70">{(s.match_score*100).toFixed(0)}% match</span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Failure Mode Differential */}
                                {msg.diagnosis.ranked_failure_modes && msg.diagnosis.ranked_failure_modes.length > 0 && (
                                  <div>
                                    <div className="text-xs uppercase tracking-widest mb-2 text-white/50">
                                      DIFFERENTIAL DIAGNOSIS
                                      <span className="normal-case tracking-normal font-normal text-white/30 ml-2">
                                        (Bayesian posterior — probability this failure mode given matched symptoms)
                                      </span>
                                    </div>
                                    <div className="space-y-2">
                                      {(msg.diagnosis.ranked_failure_modes || []).slice(0, 3).map((fm: any, fi: number) => {
                                        const pct = Math.round((fm.posterior || 0) * 100);
                                        const isTop = fi === 0;
                                        const barColor = isTop ? '#10b981' : '#64748b';
                                        return (
                                          <div key={fm.failure_mode_id || fi} className={`failure-mode ${isTop ? 'ring-1 ring-emerald-500/30' : ''}`}>
                                            <div className="flex items-center gap-3 mb-2">
                                              <div className="flex-1">
                                                <div className="font-medium flex items-center gap-2">
                                                  {fm.name}
                                                  {isTop && <span className="badge badge-ok text-[9px]">TOP</span>}
                                                </div>
                                                <div className="text-xs text-white/50 line-clamp-1 mt-0.5">{fm.description}</div>
                                              </div>
                                              <div className="text-right shrink-0">
                                                <div className="font-mono font-bold text-base text-emerald-400">{pct}%</div>
                                                <div className="text-[9px] text-white/40">posterior</div>
                                              </div>
                                            </div>
                                            {/* Progress bar for posterior */}
                                            <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
                                              <div
                                                className="h-full rounded-full"
                                                style={{ width: `${pct}%`, background: barColor }}
                                              />
                                            </div>
                                            <div className="flex gap-3 mt-2 text-[10px] text-white/40">
                                              <span>RPN {fm.rpn || '—'}</span>
                                              <span>AP {fm.action_priority || '—'}</span>
                                              {fm.safety_notes && (
                                                <span className="text-amber-400/80 truncate max-w-[280px]">⚠ {fm.safety_notes}</span>
                                              )}
                                            </div>
                                          </div>
                                        );
                                      })}
                                    </div>
                                  </div>
                                )}

                                {/* Diagnostic / troubleshooting steps (from graph DiagnosticStep nodes) */}
                                {(msg.diagnosis.diagnostic_steps || []).length > 0 && (
                                  <div>
                                    <div className="text-xs uppercase tracking-widest mb-2 text-white/50">
                                      DIAGNOSTIC STEPS
                                      <span className="normal-case tracking-normal font-normal text-white/30 ml-2">
                                        (targeted for top failure mode · from knowledge graph)
                                      </span>
                                    </div>
                                    <ol className="space-y-2">
                                      {(msg.diagnosis.diagnostic_steps || []).slice(0, 6).map((step: any, si: number) => (
                                        <li
                                          key={step.step_id || si}
                                          className="flex gap-3 rounded-xl border border-teal-500/20 bg-teal-500/5 px-3 py-2"
                                        >
                                          <span className="shrink-0 flex h-6 w-6 items-center justify-center rounded-full bg-teal-500/20 text-teal-300 text-xs font-bold font-mono">
                                            {si + 1}
                                          </span>
                                          <div className="min-w-0 flex-1">
                                            <div className="text-sm text-white/90 leading-snug">{step.description}</div>
                                            {step.expected_outcome && (
                                              <div className="text-[11px] text-white/45 mt-1">
                                                Expected: {step.expected_outcome}
                                              </div>
                                            )}
                                            <div className="flex flex-wrap gap-2 mt-1 text-[10px] text-white/35 font-mono">
                                              {step.step_id && <span>{step.step_id}</span>}
                                              {step.source_system && <span>· {step.source_system}</span>}
                                            </div>
                                          </div>
                                        </li>
                                      ))}
                                    </ol>
                                  </div>
                                )}

                                {/* Predicted Parts */}
                                {(msg.diagnosis.predicted_parts || []).length > 0 && (
                                  <div>
                                    <div className="text-xs uppercase tracking-widest mb-1 text-white/50">PREDICTED PARTS</div>
                                    <div className="flex flex-wrap gap-2 text-xs">
                                      {(msg.diagnosis.predicted_parts || []).slice(0,3).map((p:any) => (
                                        <span key={p.part_id || p.name} className="badge">{p.name || p.part_id} · {p.part_number}</span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Similar past resolutions */}
                                {(msg.diagnosis.historical_resolutions || []).length > 0 && (
                                  <div>
                                    <div className="text-xs uppercase tracking-widest mb-1 text-white/50">SIMILAR PAST RESOLUTIONS</div>
                                    <ul className="space-y-1 text-xs text-white/60">
                                      {(msg.diagnosis.historical_resolutions || []).slice(0, 3).map((hr: any, hi: number) => (
                                        <li key={hr.resolution_id || hr.work_order_id || hi} className="flex gap-2">
                                          <span className="text-white/30">·</span>
                                          <span>
                                            {hr.description || hr.resolution_summary || hr.summary || hr.action || hr.resolution_id || 'Prior resolution'}
                                            {hr.resolution_date || hr.resolved_at || hr.date ? (
                                              <span className="text-white/35 ml-1">
                                                ({String(hr.resolution_date || hr.resolved_at || hr.date).slice(0, 10)})
                                              </span>
                                            ) : null}
                                          </span>
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}

                                {/* Provenance Trail */}
                                {msg.full?.provenance_trail && msg.full.provenance_trail.length > 0 && (
                                  <div>
                                    <div className="text-xs uppercase tracking-widest mb-1 text-white/50">PROVENANCE TRAIL</div>
                                    <div className="space-y-1 text-[11px]">
                                      {msg.full.provenance_trail.slice(0, 8).map((p:any, i:number) => (
                                        <div key={i} className="provenance-item">
                                          {p.entity_type || p.source_system} → {p.source_record_id || p.entity_id}
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Action buttons */}
                                <div className="flex items-center gap-3 text-xs pt-1 flex-wrap">
                                  <button
                                    type="button"
                                    onClick={() => {
                                      // Always try path highlight for a successful diagnosis (not only when traversed_* present)
                                      const d = msg.diagnosis;
                                      if (!d?.context_blocked && d?.product_id && (d.matched_symptoms?.length || d.traversed_symptom_ids?.length || d.ranked_failure_modes?.length)) {
                                        openExplorerWithDiagnosisPath(d, msg.full);
                                      } else if (d?.product_id) {
                                        skipExplorerAutoLoadRef.current = true;
                                        setExplorerProductId(d.product_id);
                                        setActiveView('explorer');
                                        setTimeout(() => loadExplorer(d.product_id, false), 50);
                                      } else {
                                        setActiveView('explorer');
                                      }
                                    }}
                                    className="btn btn-secondary text-xs"
                                    title="Open Knowledge Explorer with this case's diagnosis path highlighted on the product graph"
                                    disabled={!!msg.diagnosis?.context_blocked}
                                  >
                                    {(msg.diagnosis?.traversed_fm_id || msg.diagnosis?.ranked_failure_modes?.length)
                                      ? '🔍 Explore Exact Path'
                                      : 'Explore Graph'}
                                  </button>
                                  <button
                                    onClick={() => {
                                      if (!msg.full) return;
                                      api.submitClaim({ message: messages.find(m => m.role==='user')?.content || '', asset_id: selectedAssetRecord?.asset_id || '' }).then(() => {
                                        toast.success('Claim submitted from diagnosis');
                                        qc.invalidateQueries({ queryKey: ['claims'] });
                                      });
                                    }}
                                    className="btn btn-primary text-xs"
                                    disabled={!msg.diagnosis.product_id}
                                  >
                                    <FileText className="w-3.5 h-3.5" /> Submit Claim
                                  </button>
                                  {msg.full?.escalated && (
                                    <div className="text-rose-400 flex items-center gap-1">
                                      <AlertTriangle className="w-3.5 h-3.5"/> Escalated to agent
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  <div ref={chatMessagesEndRef} className="h-px w-full shrink-0" aria-hidden />
                </div>

                {/* Composer — pinned to bottom of chat column (not sticky-over-content) */}
                <div className="shrink-0 chat-composer pt-3 pb-4 border-t border-white/10 mt-1">
                  <div className="glass rounded-3xl p-2 flex gap-2 items-end shadow-lg shadow-black/20">
                    <div className="flex-1 min-w-0 px-1">
                      <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                        placeholder="Describe the problem (e.g. washing machine won't spin...)"
                        className="input resize-none min-h-[52px] max-h-32 overflow-y-auto bg-transparent border-0 focus:ring-0 w-full"
                        rows={2}
                      />
                      <div className="flex gap-1.5 mt-1 px-1 flex-wrap items-center">
                        {examplePrompts.map((p, i) => (
                          <button key={i} type="button" onClick={() => { setInput(p); }} className="text-[10px] px-2.5 py-px rounded-full glass border border-white/10 hover:border-white/30">{p.slice(0,42)}…</button>
                        ))}
                        <button type="button" onClick={toggleVoice} className={`text-[10px] px-2.5 py-px rounded-full border transition ${isListening ? 'bg-rose-500/20 border-rose-500/40' : 'glass border-white/10 hover:border-white/30'}`}>
                          🎤 {isListening ? 'Listening...' : 'Voice'}
                        </button>
                        <span className="ml-auto text-[10px] text-white/30">⌘K for commands</span>
                      </div>
                    </div>
                    <button type="button" onClick={() => handleSend(false)} disabled={!input.trim() || diagnoseMutation.isPending} className="btn btn-primary h-12 w-12 rounded-2xl shrink-0">
                      {diagnoseMutation.isPending ? <RefreshCw className="animate-spin w-4 h-4"/> : <Send className="w-4 h-4" />}
                    </button>
                  </div>
                  <div className="text-[10px] text-center mt-2 text-white/30">Graph-backed • Full provenance trail attached • FMEA + Bayesian posteriors</div>
                </div>

                {/* Command Palette (⌘K) */}
                <AnimatePresence>
                  {commandOpen && (
                    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[20vh] bg-black/60 backdrop-blur" onClick={() => setCommandOpen(false)}>
                      <div className="w-full max-w-md glass rounded-2xl p-2" onClick={e => e.stopPropagation()}>
                        <div className="p-2 text-xs text-white/50">Quick commands</div>
                        {[
                          { label: 'Go to Chat', cmd: 'chat' },
                          { label: 'Agent Cases', cmd: 'cases' },
                          { label: 'Knowledge Explorer', cmd: 'explorer' },
                          { label: 'Enterprise Ops', cmd: 'ops' },
                          { label: 'Use Voice Input', cmd: 'voice' },
                          { label: 'Try Example Symptom', cmd: 'example' },
                        ].map(item => (
                          <button key={item.cmd} onClick={() => runCommand(item.cmd)} className="w-full text-left px-3 py-2 rounded-xl hover:bg-white/5 flex justify-between text-sm">
                            {item.label} <span className="text-white/40 text-xs">⌘K</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </AnimatePresence>
              </div>
            )}

            {/* ==================== AGENT CASES ==================== */}
            {activeView === 'cases' && (
              <div className="max-w-5xl mx-auto">
                <div className="mb-6">
                  <div className="text-3xl font-semibold tracking-tight">Agent Workspace</div>
                  <div className="text-white/60">Review escalated cases. Update status. Drive claims to resolution.</div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
                  <div className="lg:col-span-3 space-y-3">
                    <div className="uppercase text-xs tracking-widest text-white/40 px-1">Open / Recent Cases</div>
                    {(claimsData?.claims || []).map((c: any, idx: number) => (
                      <div key={idx} className="card p-4 flex justify-between items-center group">
                        <div>
                          <div className="font-medium">{c.claim_id} — {c.failure_mode_name || 'Unknown'}</div>
                          <div className="text-xs text-white/50">{c.asset_id} · {c.customer_id}</div>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="badge bg-white/5 border border-white/10">{c.status}</span>
                          <button onClick={() => api.updateClaimStatus(c.claim_id, 'approved').then(() => { toast.success('Claim approved'); qc.invalidateQueries({ queryKey: ['claims'] }); })} className="btn btn-secondary text-xs">Approve</button>
                        </div>
                      </div>
                    ))}
                    {claimsLoading && <div className="text-sm text-white/50">Loading cases...</div>}
                    {claimsError && <div className="text-sm text-rose-400">Error loading claims. Check backend.</div>}
                    {(!claimsData?.claims?.length && !claimsLoading) && <div className="text-sm text-white/50">No cases yet. Run a diagnosis that escalates, or use Admin to populate data.</div>}
                  </div>

                  <div className="lg:col-span-2 glass p-5 rounded-3xl space-y-4">
                    <div className="font-medium">Case Actions</div>
                    <p className="text-sm text-white/60">Full provenance and diagnosis evidence is attached to each case for rapid, defensible decisions.</p>
                    <div className="text-xs text-white/40">Use the Chat view to generate new escalated cases.</div>
                  </div>
                </div>
              </div>
            )}

            {/* ==================== KNOWLEDGE EXPLORER — full-viewport graph ==================== */}
            {activeView === 'explorer' && (
              <div className="flex-1 min-h-0 flex flex-col w-full">
                {/* Toolbar */}
                <div className="shrink-0 px-4 pt-3 pb-2 border-b border-white/10 space-y-2">
                  <div className="flex flex-wrap items-center gap-2 justify-between">
                    <div className="min-w-0">
                      <div className="text-xl font-semibold tracking-tight flex items-center gap-2">
                        <GitBranch className="w-5 h-5 text-emerald-400 shrink-0" />
                        Knowledge Explorer
                        <span className={`text-[10px] px-1.5 py-px rounded font-medium ${health?.neo4j ? 'badge-ok' : 'badge-error'}`}>
                          {health?.neo4j ? 'Neo4j' : 'Offline'}
                        </span>
                        <span className="text-[10px] px-1.5 py-px rounded badge-info uppercase">{role}</span>
                      </div>
                      <div className="text-[11px] text-white/45 mt-0.5">
                        Full product neighborhood from Neo4j (symptoms, FMs, steps, parts, codes, assets, policies).
                        Persona presets only change type chips — they do not hide the graph by default.
                      </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <div className="flex items-center gap-0.5 border border-white/10 rounded-lg p-0.5">
                        <button
                          type="button"
                          className={`btn text-[10px] px-2 py-1 ${explorerScope === 'full' ? 'btn-primary' : 'btn-ghost'}`}
                          onClick={() => setExplorerScope('full')}
                          title="All ontology types for this product"
                        >
                          Full ontology
                        </button>
                        <button
                          type="button"
                          className={`btn text-[10px] px-2 py-1 ${explorerScope === 'persona' ? 'btn-primary' : 'btn-ghost'}`}
                          onClick={() => setExplorerScope('persona')}
                          title={`Preset for ${role} persona`}
                        >
                          {role} preset
                        </button>
                      </div>
                      <select
                        title="Product subgraph"
                        value={explorerProductId}
                        onChange={(e) => {
                          setExplorerProductId(e.target.value);
                          setSelectedNode(null);
                          setHighlightPath(null);
                          loadExplorer(e.target.value);
                        }}
                        className="input w-52 py-1.5 text-sm"
                      >
                        {productsList.map((p: any) => (
                          <option key={p.product_id} value={p.product_id}>{p.name}</option>
                        ))}
                      </select>
                      <button
                        type="button"
                        className="btn btn-primary text-xs"
                        disabled={isLoadingExplorer}
                        onClick={() => {
                          setSelectedNode(null);
                          setExplorerScope('full');
                          loadExplorer(explorerProductId);
                        }}
                      >
                        {isLoadingExplorer ? 'Loading…' : 'Reload full graph'}
                      </button>
                      {lastDiagnosis?.diagnosis?.product_id === explorerProductId && (
                        <button
                          type="button"
                          className="btn btn-secondary text-xs"
                          onClick={() => { loadExplorer(explorerProductId, true); setSelectedNode(null); }}
                          title="Highlight last diagnosis path"
                        >
                          <Crosshair className="w-3.5 h-3.5" /> Diagnosis path
                        </button>
                      )}
                      <button
                        type="button"
                        className="btn btn-secondary text-xs"
                        onClick={loadProductTurtle}
                        title="W3C Turtle: full OWL TBox + product ABox for this product"
                      >
                        Full OWL/RDF (.ttl)
                      </button>
                      {highlightPath && (
                        <button
                          type="button"
                          className="btn btn-ghost text-xs"
                          onClick={() => {
                            setHighlightPath(null);
                            setPathOnlyMode(false);
                            setPathExplain(null);
                            fitGraph();
                          }}
                        >
                          Clear path
                        </button>
                      )}
                      {(pathExplain || highlightPath) && (
                        <button
                          type="button"
                          className={`btn text-xs ${pathExplainOpen ? 'btn-primary' : 'btn-secondary'}`}
                          onClick={() => setPathExplainOpen((v) => !v)}
                          title="Show Cypher used and hop-by-hop graph traversal for this case"
                        >
                          Cypher &amp; traversal
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Secondary toolbar: search, layout, filters, nav */}
                  <div className="flex flex-wrap items-center gap-2">
                    <div className="relative">
                      <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-white/35" />
                      <input
                        className="input pl-8 py-1.5 text-xs w-48"
                        placeholder="Search nodes…"
                        value={explorerSearch}
                        onChange={(e) => setExplorerSearch(e.target.value)}
                      />
                    </div>
                    <div className="flex items-center gap-1 border border-white/10 rounded-lg p-0.5">
                      <button type="button" className={`btn text-[10px] px-2 py-1 ${graphLayoutDir === 'TB' ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setGraphLayoutDir('TB')}>Top→Down</button>
                      <button type="button" className={`btn text-[10px] px-2 py-1 ${graphLayoutDir === 'LR' ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setGraphLayoutDir('LR')}>Left→Right</button>
                    </div>
                    <button type="button" className="btn btn-secondary text-xs" onClick={() => fitGraph(0.15)} title="Fit entire graph (F)">
                      <Maximize2 className="w-3.5 h-3.5" /> Fit all
                    </button>
                    <button type="button" className="btn btn-ghost text-xs" onClick={() => rfInstance?.zoomIn?.({ duration: 120 })} title="Zoom in (+)">
                      <ZoomIn className="w-3.5 h-3.5" />
                    </button>
                    <button type="button" className="btn btn-ghost text-xs" onClick={() => rfInstance?.zoomOut?.({ duration: 120 })} title="Zoom out (-)">
                      <ZoomOut className="w-3.5 h-3.5" />
                    </button>
                    <label className="flex items-center gap-1.5 text-[11px] text-white/55 px-2">
                      <input type="checkbox" checked={showEdgeLabels} onChange={(e) => setShowEdgeLabels(e.target.checked)} />
                      Edge labels
                    </label>
                    {highlightPath && (
                      <label className="flex items-center gap-1.5 text-[11px] text-emerald-300/80 px-2">
                        <input type="checkbox" checked={pathOnlyMode} onChange={(e) => setPathOnlyMode(e.target.checked)} />
                        Path only
                      </label>
                    )}
                    <div className="flex flex-wrap gap-1 ml-auto max-w-2xl justify-end">
                      <span className="text-[10px] text-white/35 self-center mr-1 flex items-center gap-1"><Layers className="w-3 h-3" /> Types</span>
                      {(explorerScope === 'full' ? [...FULL_ONTOLOGY_TYPES] : (PERSONA_NODE_TYPES[role] || [...FULL_ONTOLOGY_TYPES])).map((t) => (
                        <button
                          key={t}
                          type="button"
                          className={`text-[10px] px-2 py-0.5 rounded-full border transition ${
                            typeFilter[t] !== false
                              ? 'border-white/25 bg-white/10 text-white/80'
                              : 'border-white/10 text-white/30'
                          }`}
                          onClick={() => setTypeFilter((prev) => ({ ...prev, [t]: !(prev[t] !== false) }))}
                        >
                          {t}
                        </button>
                      ))}
                      <button
                        type="button"
                        className="text-[10px] px-2 py-0.5 rounded-full border border-emerald-500/30 text-emerald-300/90"
                        onClick={() => {
                          const next: Record<string, boolean> = {};
                          FULL_ONTOLOGY_TYPES.forEach((t) => { next[t] = true; });
                          setTypeFilter(next);
                          setExplorerScope('full');
                        }}
                      >
                        Show all
                      </button>
                    </div>
                  </div>
                  <div className="text-[10px] text-white/35 flex flex-wrap gap-x-3 gap-y-0.5">
                    <span>Drag empty space to pan · Scroll to zoom · Pinch · Arrow keys pan · <kbd className="font-mono">F</kbd> fit · <kbd className="font-mono">+/-</kbd> zoom · Click node to inspect</span>
                    <span className="text-white/50">{flow.nodes.length} nodes · {flow.edges.length} edges{highlightPath ? ' · path on' : ''}</span>
                  </div>

                  {/* Diagnosis case: Cypher + traversal (from Explore Exact Path) */}
                  {pathExplainOpen && pathExplain && (
                    <div className="mt-2 rounded-xl border border-emerald-500/25 bg-emerald-500/5 p-3 space-y-2">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="text-xs font-medium text-emerald-200/90">
                          Case graph traversal
                          {pathExplain.case_label ? ` · ${pathExplain.case_label}` : ''}
                          {pathExplain.params?.failure_mode_id
                            ? ` · FM ${pathExplain.params.failure_mode_id}`
                            : ''}
                        </div>
                        <div className="flex gap-1 items-center">
                          <button
                            type="button"
                            className={`text-[10px] px-2 py-0.5 rounded-full border ${
                              pathExplainTab === 'traversal'
                                ? 'border-emerald-400/50 bg-emerald-500/20 text-emerald-100'
                                : 'border-white/10 text-white/45'
                            }`}
                            onClick={() => setPathExplainTab('traversal')}
                          >
                            Traversal hops
                          </button>
                          <button
                            type="button"
                            className={`text-[10px] px-2 py-0.5 rounded-full border ${
                              pathExplainTab === 'cypher'
                                ? 'border-emerald-400/50 bg-emerald-500/20 text-emerald-100'
                                : 'border-white/10 text-white/45'
                            }`}
                            onClick={() => setPathExplainTab('cypher')}
                          >
                            Cypher used
                          </button>
                          <button
                            type="button"
                            className="text-[10px] px-2 py-0.5 rounded-full border border-white/10 text-white/40"
                            onClick={() => setPathExplainOpen(false)}
                          >
                            Hide
                          </button>
                        </div>
                      </div>

                      {pathExplainTab === 'traversal' && (
                        <div className="max-h-40 overflow-y-auto space-y-1.5 pr-1">
                          {(pathExplain.traversal || []).map((h: any, i: number) => (
                            <div
                              key={i}
                              className="flex gap-2 text-[11px] items-start border-b border-white/5 pb-1.5"
                            >
                              <span className="shrink-0 w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-300 flex items-center justify-center text-[10px] font-bold">
                                {h.hop ?? i + 1}
                              </span>
                              <div className="min-w-0 flex-1">
                                <div className="font-medium text-white/80">{h.label}</div>
                                <div className="font-mono text-[10px] text-white/45 truncate">
                                  {h.from && <span>{h.from}</span>}
                                  {h.rel && (
                                    <span className="text-emerald-400/80">{` -[:${h.rel}]-> `}</span>
                                  )}
                                  {h.to && <span>{h.to}</span>}
                                </div>
                                {h.detail && (
                                  <div className="text-[10px] text-white/50 mt-0.5 leading-snug">{h.detail}</div>
                                )}
                              </div>
                            </div>
                          ))}
                          {!(pathExplain.traversal || []).length && (
                            <div className="text-[11px] text-white/40">No traversal hops recorded for this case.</div>
                          )}
                        </div>
                      )}

                      {pathExplainTab === 'cypher' && (
                        <div className="max-h-48 overflow-y-auto space-y-3 pr-1">
                          {(pathExplain.cypher_queries || []).map((q: any, i: number) => (
                            <div key={i} className="rounded-lg border border-white/10 bg-black/25 p-2">
                              <div className="flex items-center justify-between gap-2 mb-1">
                                <div className="text-[11px] font-medium text-white/80">
                                  {q.step != null ? `${q.step}. ` : ''}{q.name || `Query ${i + 1}`}
                                </div>
                                <button
                                  type="button"
                                  className="text-[10px] text-white/40 hover:text-white/70"
                                  onClick={() => {
                                    navigator.clipboard?.writeText(q.cypher || '');
                                    toast.success('Cypher copied');
                                  }}
                                >
                                  Copy
                                </button>
                              </div>
                              {q.purpose && (
                                <div className="text-[10px] text-white/45 mb-1.5">{q.purpose}</div>
                              )}
                              <pre className="text-[10px] font-mono text-emerald-100/80 whitespace-pre-wrap leading-relaxed overflow-x-auto">
                                {q.cypher}
                              </pre>
                              {q.params && (
                                <div className="mt-1.5 text-[10px] font-mono text-white/35 break-all">
                                  params: {JSON.stringify(q.params)}
                                </div>
                              )}
                            </div>
                          ))}
                          {!(pathExplain.cypher_queries || []).length && (
                            <div className="text-[11px] text-white/40">
                              Cypher plan unavailable — re-run <b>Explore Exact Path</b> from Diagnosis Chat after API refresh.
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Graph stage + inspector — fills remaining viewport */}
                <div className="flex-1 min-h-0 flex">
                  <div className="graph-container relative flex-1 min-w-0 min-h-0 rounded-none border-0">
                    <ReactFlow
                      nodes={flow.nodes}
                      edges={flow.edges}
                      fitView
                      fitViewOptions={{ padding: 0.2, minZoom: 0.08, maxZoom: 1.4 }}
                      minZoom={0.05}
                      maxZoom={2.5}
                      defaultViewport={{ x: 0, y: 0, zoom: 0.6 }}
                      panOnDrag
                      panOnScroll
                      panOnScrollMode={"free" as any}
                      zoomOnScroll
                      zoomOnPinch
                      zoomOnDoubleClick={false}
                      selectionOnDrag={false}
                      selectNodesOnDrag={false}
                      nodesDraggable={false}
                      nodesConnectable={false}
                      elementsSelectable
                      onNodeClick={onNodeClick}
                      onPaneClick={() => { setSelectedNode(null); setRdfEntity(null); }}
                      onInit={(inst) => {
                        setRfInstance(inst);
                        setTimeout(() => {
                          try { inst.fitView({ padding: 0.2, duration: 200, minZoom: 0.08, maxZoom: 1.4 }); } catch { /* */ }
                        }, 50);
                      }}
                      proOptions={{ hideAttribution: true }}
                      style={{ width: '100%', height: '100%', cursor: 'grab' }}
                      className="explorer-flow"
                    >
                      <Background
                        gap={20}
                        color={theme === 'dark' ? '#1c2433' : '#d1d5db'}
                        size={1}
                      />
                      <Controls
                        showInteractive={false}
                        position="bottom-left"
                        className="explorer-controls"
                      />
                      <MiniMap
                        pannable
                        zoomable
                        nodeColor={(n) => {
                          if ((n.className as string)?.includes('node-on-path')) return '#10b981';
                          return (n.data as any)?.typeColor ?? (theme === 'dark' ? '#334155' : '#94a3b8');
                        }}
                        style={{
                          background: theme === 'dark' ? '#0a0a12' : '#f1f5f9',
                          border: `1px solid ${theme === 'dark' ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.12)'}`,
                          borderRadius: '8px',
                          width: 140,
                          height: 100,
                        }}
                        maskColor={theme === 'dark' ? 'rgba(0,0,0,0.55)' : 'rgba(255,255,255,0.55)'}
                      />
                      <Panel position="top-right" className="!m-2">
                        <div className="glass rounded-lg px-2 py-1.5 text-[10px] text-white/50 max-w-[220px] leading-snug">
                          Scope: <b className="text-white/70">{explorerScope === 'full' ? 'full ontology' : `${role} preset`}</b>.
                          Parts & DiagnosticSteps are graph nodes — use Fit all if denser after reload.
                        </div>
                      </Panel>
                    </ReactFlow>

                    {flow.nodes.length === 0 && !isLoadingExplorer && (
                      <div className="graph-empty-overlay">
                        <GitBranch className="w-10 h-10 mb-3 opacity-30" />
                        <p className="text-sm mb-1">No graph data in view.</p>
                        <p className="text-xs mb-4 max-w-sm">
                          Load a product subgraph, clear filters, or turn off Path only.
                        </p>
                        <button type="button" onClick={() => { setExplorerSearch(''); setPathOnlyMode(false); loadExplorer(explorerProductId); }} className="btn btn-secondary">
                          Load {explorerProductId}
                        </button>
                      </div>
                    )}
                    {isLoadingExplorer && (
                      <div className="graph-loading-overlay">
                        <div className="text-sm">Fetching graph from Neo4j…</div>
                      </div>
                    )}
                  </div>

                  {/* Inspector — Neo4j neighbors + W3C OWL/RDF definition */}
                  <aside className="w-[22rem] shrink-0 border-l border-white/10 flex flex-col min-h-0 bg-[var(--surface-1)]">
                    {selectedNode ? (() => {
                      const raw   = selectedNode.data?.raw || {};
                      const ntype = selectedNode.data?.type || 'Node';
                      const title = selectedNode.data?.fullLabel || selectedNode.data?.label || selectedNode.id;
                      const isOnPath = !!(highlightPath?.nodes?.includes(selectedNode.id));
                      const connEdges = flow.edges.filter(
                        (e: any) => e.source === selectedNode.id || e.target === selectedNode.id
                      );
                      const typeColorMap: Record<string,string> = {
                        Product:'#10b981', Symptom:'#3b82f6', FailureMode:'#f59e0b', Part:'#8b5cf6',
                        Component:'#ec4899', DiagnosticStep:'#14b8a6', HistoricalResolution:'#64748b',
                        ErrorCode:'#f43f5e', Model:'#06b6d4', SKU:'#a78bfa', Asset:'#84cc16',
                        WarrantyPolicy:'#0d9488',
                      };
                      const accentColor = typeColorMap[ntype] || '#64748b';
                      const ttlText =
                        rdfTab === 'class'
                          ? (rdfEntity?.turtle?.class_definition || '')
                          : rdfTab === 'instance'
                            ? (rdfEntity?.turtle?.instance_definition || '')
                            : (rdfEntity?.turtle?.combined || '');

                      return (
                        <>
                          <div className="px-4 py-3 flex items-start justify-between gap-2 shrink-0" style={{ background: accentColor, color: '#fff' }}>
                            <div className="min-w-0">
                              <div className="text-[10px] font-bold uppercase tracking-widest opacity-80">{ntype}</div>
                              <div className="text-sm font-semibold break-words">{String(title).split('\n')[0]}</div>
                              <div className="text-[10px] opacity-75 mt-0.5">Neo4j KG · OWL/RDF definition</div>
                            </div>
                            <button
                              type="button"
                              onClick={() => { setSelectedNode(null); setRdfEntity(null); }}
                              className="opacity-80 hover:opacity-100 text-lg leading-none shrink-0"
                            >
                              ×
                            </button>
                          </div>
                          <div className="p-3 space-y-3 text-xs overflow-y-auto flex-1 min-h-0 node-panel-body">
                            <div>
                              <div className="uppercase tracking-widest text-[9px] mb-1 node-panel-label">Neo4j node</div>
                              <code className="text-[11px] font-mono break-all node-panel-value">
                                {raw.entity_id ? `${ntype}:${raw.entity_id}` : selectedNode.id}
                              </code>
                            </div>
                            {rdfEntity?.rdf?.instance_iri && (
                              <div>
                                <div className="uppercase tracking-widest text-[9px] mb-1 node-panel-label">RDF IRI (W3C)</div>
                                <code className="text-[10px] font-mono break-all text-sky-300/90">{rdfEntity.rdf.instance_iri}</code>
                                <div className="text-[10px] text-white/40 mt-0.5 font-mono">{rdfEntity.rdf.instance_curie}</div>
                              </div>
                            )}
                            {rdfEntity?.owl?.class && (
                              <div className="rounded-lg border border-white/10 bg-white/5 p-2 space-y-1">
                                <div className="text-[10px] uppercase tracking-widest text-white/40">OWL class (TBox)</div>
                                <div className="font-medium text-white/85">wd:{rdfEntity.owl.class}</div>
                                <div className="text-[11px] text-white/55 leading-snug">{rdfEntity.owl.comment}</div>
                                <div className="text-[10px] font-mono text-white/35 break-all">{rdfEntity.owl.class_iri}</div>
                              </div>
                            )}
                            {highlightPath && (
                              <div className={`rounded-md px-2.5 py-1.5 text-[10px] font-medium ${
                                isOnPath ? 'bg-emerald-900/40 text-emerald-300 border border-emerald-700/40' : 'border border-white/10 text-white/40'
                              }`}>
                                {isOnPath ? '● On active diagnosis path' : '○ Not on diagnosis path'}
                              </div>
                            )}
                            {raw.title && String(raw.title).includes('\n') && (
                              <div>
                                <div className="uppercase tracking-widest text-[9px] mb-1 node-panel-label">Details</div>
                                <div className="space-y-0.5 text-white/65">
                                  {String(raw.title).split('\n').slice(1).map((line: string, i: number) => (
                                    <div key={i}>{line}</div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* OWL / RDF Turtle */}
                            <div className="space-y-1.5">
                              <div className="flex items-center justify-between gap-1">
                                <div className="uppercase tracking-widest text-[9px] node-panel-label">
                                  OWL / RDF definition
                                </div>
                                {rdfEntityLoading && <span className="text-[10px] text-white/35">loading…</span>}
                              </div>
                              <div className="flex gap-1 flex-wrap">
                                {(['combined', 'class', 'instance'] as const).map((t) => (
                                  <button
                                    key={t}
                                    type="button"
                                    className={`text-[10px] px-2 py-0.5 rounded-full border ${
                                      rdfTab === t ? 'border-emerald-500/40 bg-emerald-500/15 text-emerald-200' : 'border-white/10 text-white/45'
                                    }`}
                                    onClick={() => setRdfTab(t)}
                                  >
                                    {t === 'combined' ? 'Full def' : t === 'class' ? 'OWL class' : 'RDF instance'}
                                  </button>
                                ))}
                                {ttlText && (
                                  <button
                                    type="button"
                                    className="text-[10px] px-2 py-0.5 rounded-full border border-white/15 text-white/50 ml-auto"
                                    onClick={() => {
                                      navigator.clipboard?.writeText(ttlText);
                                      toast.success('Turtle copied');
                                    }}
                                  >
                                    Copy .ttl
                                  </button>
                                )}
                              </div>
                              <pre className="source-preview-box max-h-52 text-[10px] leading-relaxed whitespace-pre-wrap break-all">
                                {rdfEntityLoading
                                  ? 'Loading W3C Turtle…'
                                  : rdfEntity?.error
                                    ? rdfEntity.error
                                    : (ttlText || 'No Turtle for this node')}
                              </pre>
                              <div className="text-[10px] text-white/35 leading-snug">
                                <b>OWL</b> = class/property vocabulary · <b>RDF</b> = triples about this individual ·{' '}
                                <b>Neo4j</b> = runtime knowledge graph for GraphRAG
                              </div>
                            </div>

                            <div>
                              <div className="uppercase tracking-widest text-[9px] mb-1.5 node-panel-label">
                                Graph neighbors ({connEdges.length})
                              </div>
                              <div className="space-y-1 max-h-36 overflow-y-auto">
                                {connEdges.map((e: any, i: number) => {
                                  const otherId = e.source === selectedNode.id ? e.target : e.source;
                                  const direction = e.source === selectedNode.id ? '→' : '←';
                                  const relType = (e.data?.type || e.label || '').replace(/_/g, ' ');
                                  return (
                                    <button
                                      key={i}
                                      type="button"
                                      className="node-panel-edge-row flex items-center gap-1.5 w-full text-left"
                                      onClick={() => {
                                        const targetNode = flow.nodes.find((n: any) => n.id === otherId)
                                          || baseFlow.nodes.find((n: any) => n.id === otherId);
                                        if (targetNode) onNodeClick(null as any, targetNode);
                                      }}
                                    >
                                      <span className="font-bold" style={{ color: accentColor }}>{direction}</span>
                                      <span className="font-mono text-[9px] truncate opacity-70">{relType}</span>
                                      <span className="truncate">{otherId.split(':').slice(-1)[0]}</span>
                                    </button>
                                  );
                                })}
                                {!connEdges.length && <div className="text-white/30">No edges in current filter view</div>}
                              </div>
                            </div>
                            {ntype === 'Product' && lastDiagnosis?.diagnosis?.product_id === explorerProductId && (
                              <button
                                type="button"
                                className="btn btn-primary w-full text-xs py-1.5"
                                onClick={() => loadExplorer(explorerProductId, true)}
                              >
                                Highlight diagnosis path
                              </button>
                            )}
                          </div>
                        </>
                      );
                    })() : (
                      <div className="p-5 text-sm text-white/45 space-y-3 overflow-y-auto">
                        <div className="font-medium text-white/70">Inspect a node</div>
                        <p className="text-xs leading-relaxed">
                          Click any node to load its <b>OWL class definition</b> and <b>RDF instance triples</b> (W3C Turtle),
                          plus Neo4j neighbors. Use <strong>Full OWL/RDF (.ttl)</strong> for the complete product diagram.
                        </p>
                        <ul className="text-[11px] space-y-1.5 text-white/40 list-disc pl-4">
                          <li><b>OWL TBox</b> — what Component / Product / INDICATES mean</li>
                          <li><b>RDF ABox</b> — facts about this specific individual</li>
                          <li><b>Knowledge graph</b> — Neo4j graph you are browsing</li>
                        </ul>
                        <button type="button" className="btn btn-secondary text-xs w-full" onClick={loadProductTurtle}>
                          Load full product Turtle
                        </button>
                        <div className="pt-2 flex flex-wrap gap-x-3 gap-y-1 text-[10px] graph-legend">
                          {[
                            ['#10b981','Product'], ['#3b82f6','Symptom'],
                            ['#f59e0b','FailureMode'], ['#8b5cf6','Part'],
                            ['#ec4899','Component'], ['#14b8a6','Step'],
                          ].map(([col, lbl]) => (
                            <span key={lbl} className="flex items-center gap-1">
                              <span style={{ color: col }}>●</span> {lbl}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </aside>
                </div>

                {/* Full product Turtle modal */}
                {productTurtleOpen && productTurtle && (
                  <div
                    className="fixed inset-0 z-[120] flex items-center justify-center bg-black/70 p-4"
                    onClick={() => setProductTurtleOpen(false)}
                  >
                    <div
                      className="w-full max-w-3xl max-h-[85vh] flex flex-col rounded-2xl border border-white/15 bg-[var(--surface-1)] shadow-2xl"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between gap-2 shrink-0">
                        <div>
                          <div className="font-semibold text-sm">Full OWL/RDF diagram — {explorerProductId}</div>
                          <div className="text-[11px] text-white/45">
                            W3C Turtle: ontology (TBox) + product individuals (ABox) · docs/ontology/*.ttl
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <button
                            type="button"
                            className="btn btn-secondary text-xs"
                            onClick={() => {
                              navigator.clipboard?.writeText(productTurtle);
                              toast.success('Full Turtle copied');
                            }}
                          >
                            Copy
                          </button>
                          <button type="button" className="btn btn-ghost text-xs" onClick={() => setProductTurtleOpen(false)}>
                            Close
                          </button>
                        </div>
                      </div>
                      <pre className="flex-1 min-h-0 overflow-auto p-4 text-[11px] font-mono text-white/75 whitespace-pre leading-relaxed">
                        {productTurtle}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ==================== ENTERPRISE OPS — platform status (current architecture) ==================== */}
            {activeView === 'ops' && (() => {
              const conn = statusData?.connectors || {};
              const caps = statusData?.capabilities || {};
              const kgPipes = statusData?.kg_pipelines || kgPipelines || [];
              const kgRecent = statusData?.kg_runs_recent || kgRuns || [];
              const neoDetail = statusData?.neo4j_detail || health?.neo4j_detail || {};
              const redis = statusData?.redis || health?.runtime?.redis || {};
              const runtime = health?.runtime || {};
              const connEntries = Object.entries(conn) as [string, any][];
              const chip = (ok: boolean | undefined, warn = false) =>
                ok ? 'badge-ok' : warn ? 'badge-warn' : 'badge-error';

              return (
                <div className="max-w-6xl mx-auto space-y-6 pb-8">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="text-3xl font-semibold tracking-tight">Enterprise Operations</div>
                      <p className="text-white/60 mt-1 max-w-2xl">
                        Live platform health for dual Neo4j, Redis, multi-source KG pipelines, diagnose cache, and connector modes.
                        Fixture fallback is expected when mock enterprise APIs are not running.
                      </p>
                    </div>
                    <button
                      type="button"
                      className="btn btn-secondary text-xs"
                      onClick={() => {
                        qc.invalidateQueries({ queryKey: ['status'] });
                        qc.invalidateQueries({ queryKey: ['health'] });
                        qc.invalidateQueries({ queryKey: ['batches'] });
                        refreshKgControlRoom();
                        toast.success('Ops status refreshed');
                      }}
                    >
                      <RefreshCw className="w-3.5 h-3.5" /> Refresh
                    </button>
                  </div>

                  {/* Platform KPI strip */}
                  <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-6 gap-3">
                    <div className="card p-3">
                      <div className="text-[10px] text-white/45 uppercase">Neo4j prod</div>
                      <div className={`text-sm font-semibold mt-1 ${neoDetail?.production?.connected || health?.neo4j ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {(neoDetail?.production?.connected ?? health?.neo4j) ? 'UP' : 'DOWN'}
                      </div>
                      <div className="text-[10px] font-mono text-white/35 truncate">{neoDetail?.production?.uri || 'bolt://…7687'}</div>
                    </div>
                    <div className="card p-3">
                      <div className="text-[10px] text-white/45 uppercase">Neo4j staging</div>
                      <div className={`text-sm font-semibold mt-1 ${neoDetail?.staging?.connected ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {neoDetail?.staging?.connected ? 'UP' : 'DOWN / same'}
                      </div>
                      <div className="text-[10px] font-mono text-white/35 truncate">{neoDetail?.staging?.uri || 'bolt://…7688'}</div>
                    </div>
                    <div className="card p-3">
                      <div className="text-[10px] text-white/45 uppercase">Redis</div>
                      <div className={`text-sm font-semibold mt-1 ${redis?.connected ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {redis?.connected ? 'UP' : (redis?.mode || 'memory')}
                      </div>
                      <div className="text-[10px] text-white/35">cache / rate / admission</div>
                    </div>
                    <div className="card p-3">
                      <div className="text-[10px] text-white/45 uppercase">Diagnose cache</div>
                      <div className="text-sm font-semibold mt-1">
                        {(statusData?.enable_diagnose_cache ?? runtime.enable_diagnose_cache) ? 'ON' : 'OFF'}
                      </div>
                      <div className="text-[10px] text-white/35">
                        TTL {statusData?.cache_ttl_diagnose_seconds ?? runtime.cache_ttl_diagnose_seconds ?? 90}s
                      </div>
                    </div>
                    <div className="card p-3">
                      <div className="text-[10px] text-white/45 uppercase">Context gate</div>
                      <div className="text-sm font-semibold mt-1">
                        {statusData?.strict_context_consistency !== false ? 'STRICT' : 'OFF'}
                      </div>
                      <div className="text-[10px] text-white/35">asset-first + soft mismatch</div>
                    </div>
                    <div className="card p-3">
                      <div className="text-[10px] text-white/45 uppercase">Demo mode</div>
                      <div className="text-sm font-semibold mt-1">
                        {statusData?.demo_mode ?? health?.demo_mode ? 'ON' : 'OFF'}
                      </div>
                      <div className="text-[10px] text-white/35">
                        fixtures {statusData?.fixture_fallback ? 'allowed' : 'off'}
                      </div>
                    </div>
                  </div>

                  {/* Capabilities */}
                  <div className="card p-4">
                    <div className="text-xs uppercase tracking-widest text-white/45 mb-3">Platform capabilities (current build)</div>
                    <div className="flex flex-wrap gap-2">
                      {[
                        ['asset_first_diagnose', 'Asset-first diagnose'],
                        ['dual_neo4j', 'Dual Neo4j (prod/staging)'],
                        ['diagnose_read_cache', 'Diagnose Redis cache'],
                        ['kg_control_plane', 'KG control plane'],
                        ['bulk_product_upsert', 'Bulk product upsert'],
                        ['warranty_asset_register', 'Warranty asset register'],
                        ['rdf_owl_export', 'RDF/OWL export'],
                        ['rdf_owl_import_reasoner', 'OWL import/reasoner'],
                        ['live_cdc_event_bus', 'Live CDC / event bus'],
                      ].map(([key, label]) => {
                        const on = caps[key];
                        return (
                          <span key={key} className={`badge text-[10px] ${on ? 'badge-ok' : 'badge-warn'}`}>
                            {on ? '✓' : '○'} {label}
                          </span>
                        );
                      })}
                    </div>
                    <p className="text-[11px] text-white/40 mt-3">
                      Open circles are intentional gaps (not bugs): RDF is export-only; no Kafka/CDC consumer yet.
                      Knowledge admin actions run from the <b>Admin</b> tab Control Room.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                    {/* Connectors as cards */}
                    <div className="card p-5 space-y-3">
                      <div className="text-xs uppercase tracking-widest text-white/45">Connectors</div>
                      <div className="space-y-2 max-h-80 overflow-y-auto">
                        {connEntries.map(([name, row]) => {
                          const reachable = !!row?.reachable;
                          const fixtureOk = row?.mode === 'fixture_fallback' || (statusData?.fixture_fallback && !reachable && row?.configured);
                          return (
                            <div key={name} className="glass rounded-xl px-3 py-2 flex items-start justify-between gap-2">
                              <div className="min-w-0">
                                <div className="text-sm font-medium flex items-center gap-2">
                                  {name}
                                  <span className={`badge text-[9px] ${chip(reachable, fixtureOk)}`}>
                                    {reachable ? 'reachable' : fixtureOk ? 'fixture' : row?.mode || 'down'}
                                  </span>
                                </div>
                                <div className="text-[10px] font-mono text-white/40 truncate">{row?.detail}</div>
                                {(row?.role || row?.note) && (
                                  <div className="text-[10px] text-white/45 mt-0.5">{row.role || row.note}</div>
                                )}
                              </div>
                            </div>
                          );
                        })}
                        {!connEntries.length && (
                          <div className="text-sm text-white/40">Loading connector status…</div>
                        )}
                      </div>
                      <div className="text-[10px] text-white/35 leading-relaxed">
                        CRM/PIM/Claims/FSM showing <b>fixture</b> is normal when <span className="font-mono">:8090</span> mock APIs are not started.
                        Pipelines still run from <span className="font-mono">data/enterprise_sources/</span> + <span className="font-mono">data/pipeline_sources/</span>.
                      </div>
                    </div>

                    {/* KG pipelines catalog */}
                    <div className="card p-5 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="text-xs uppercase tracking-widest text-white/45">KG ingestion pipelines</div>
                        <button type="button" className="btn btn-ghost text-[10px]" onClick={() => setActiveView('admin')}>
                          Open Admin Control Room →
                        </button>
                      </div>
                      <div className="space-y-1.5 max-h-80 overflow-y-auto">
                        {(kgPipes.length ? kgPipes : []).map((p: any) => (
                          <div key={p.id || p.name} className="flex items-center justify-between text-xs border-b border-white/5 py-1.5 gap-2">
                            <div className="min-w-0">
                              <div className="font-medium text-white/80">{p.id || p.name}</div>
                              <div className="text-[10px] text-white/40 truncate">
                                {p.source_kind || '—'} · {(p.modes || p.supported_modes || []).join(', ')}
                              </div>
                            </div>
                          </div>
                        ))}
                        {!kgPipes.length && (
                          <div className="text-sm text-white/40">
                            Pipeline catalog loads from <span className="font-mono">/admin/kg-pipelines</span>. Open Admin once or click Refresh.
                          </div>
                        )}
                      </div>
                      <div className="text-[10px] text-white/35">
                        bootstrap_all · incremental_sync · promote_graph · structured / semi / unstructured extract · smoke
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                    {/* Control plane runs */}
                    <div className="card p-5">
                      <div className="text-xs uppercase tracking-widest text-white/45 mb-3">Recent KG pipeline runs</div>
                      <div className="space-y-1 max-h-56 overflow-y-auto text-xs font-mono">
                        {(kgRecent.length ? kgRecent : kgRuns).slice(0, 14).map((r: any) => (
                          <div key={r.run_id || r.pipeline_id + r.finished_at} className="flex gap-2 text-white/60 border-b border-white/5 py-1">
                            <span className="text-white/30 w-36 shrink-0">{(r.finished_at || r.started_at || '').slice(0, 19)}</span>
                            <span className="truncate">{r.pipeline_id}</span>
                            <span className={r.status === 'success' ? 'text-emerald-400' : 'text-amber-300'}>{r.status}</span>
                            {r.target_env && <span className="text-white/30">{r.target_env}</span>}
                          </div>
                        ))}
                        {!(kgRecent.length || kgRuns.length) && (
                          <div className="text-white/40 font-sans">No control-plane runs yet — use Admin → bootstrap / promote.</div>
                        )}
                      </div>
                    </div>

                    {/* Classic ETL lineage */}
                    <div className="card p-5">
                      <div className="text-xs uppercase tracking-widest text-white/45 mb-3">ETL lineage batches</div>
                      {batchesLoading && <div className="text-sm text-white/50">Loading…</div>}
                      <div className="space-y-1 max-h-56 overflow-y-auto text-xs">
                        {(batchesData?.batches || []).slice(0, 12).map((b: any, i: number) => (
                          <div key={i} className="flex justify-between border-b border-white/5 py-1 gap-2">
                            <div className="font-mono text-white/70 truncate">
                              {b.batch_id || b.id} · <span className={b.status === 'success' ? 'text-emerald-400' : 'text-amber-300'}>{b.status}</span>
                            </div>
                            <div className="text-white/35 shrink-0">{(b.created_at || b.timestamp || '').toString().slice(0, 16)}</div>
                          </div>
                        ))}
                        {!batchesLoading && !(batchesData?.batches || []).length && (
                          <div className="text-white/40">No ETL batches logged yet.</div>
                        )}
                      </div>
                      <div className="text-[10px] text-white/35 mt-2">
                        Dry-run batches only preview sources; live promote writes Neo4j and invalidates caches.
                      </div>
                    </div>
                  </div>

                  {/* Runtime caches + ops links */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                    <div className="card p-5">
                      <div className="text-xs uppercase tracking-widest text-white/45 mb-3">Runtime caches</div>
                      <div className="space-y-1 text-xs font-mono">
                        {Object.entries(runtime.caches || statusData?.runtime_caches || {}).map(([name, st]: [string, any]) => (
                          <div key={name} className="flex justify-between border-b border-white/5 py-1 text-white/60">
                            <span>{name}</span>
                            <span className="text-white/40">
                              hit {(st?.hit_rate * 100 || 0).toFixed?.(0) ?? st?.hit_rate}% · {st?.backend || '—'}
                            </span>
                          </div>
                        ))}
                        {!Object.keys(runtime.caches || statusData?.runtime_caches || {}).length && (
                          <div className="text-white/40 font-sans">No cache stats yet (run diagnose / load explorer).</div>
                        )}
                      </div>
                    </div>
                    <div className="card p-5">
                      <div className="text-xs uppercase tracking-widest text-white/45 mb-3">How to operate</div>
                      <ol className="text-xs text-white/60 space-y-1.5 list-decimal pl-4">
                        <li><b>Admin</b> → Source inventory → bootstrap_all / incremental_sync</li>
                        <li>Smoke validate → human approve → promote graph (staging first)</li>
                        <li>Bulk products: <span className="font-mono">POST /admin/products/bulk-upsert</span></li>
                        <li>New warranty unit: <span className="font-mono">POST /admin/warranty/register-asset</span></li>
                        <li>RDF/OWL export: <span className="font-mono">python -m graph.rdf_ontology_export</span></li>
                        <li>Customer diagnose: bind CRM asset first (Diagnosis Chat)</li>
                      </ol>
                      <div className="mt-3 flex flex-wrap gap-2">
                        <button type="button" className="btn btn-primary text-xs" onClick={() => setActiveView('admin')}>Admin Control Room</button>
                        <button type="button" className="btn btn-secondary text-xs" onClick={() => setActiveView('explorer')}>Knowledge Explorer</button>
                        <button type="button" className="btn btn-ghost text-xs" onClick={() => setActiveView('chat')}>Diagnosis Chat</button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* ==================== ADMIN — Strict 1-by-1 wizard ==================== */}
            {activeView === 'admin' && (() => {
              const selIds: string[] = activeSelectionIds;
              const planUnlocks = ingestPlan?.wizard_unlocks || {};
              const planGates = ingestPlan?.gates || {};
              const nextPlanAction = ingestPlan?.next_action;
              const stepDone: Record<number, boolean> = {
                1: Boolean(kgInventory?.file_count) || Boolean(wizardStepDone[1]),
                2: hasFetched || Boolean(wizardStepDone[2]),
                3: (lockedSelectionIds.length > 0) || Boolean(wizardStepDone[3]),
                4: Boolean(ontologyValidation?.ok || (ontologyValidation?.passed_count > 0 && ontologyValidation?.failed_count === 0)) || Boolean(wizardStepDone[4]),
                // Materialize complete only when we explicitly marked it (not failed bootstrap_all)
                5: Boolean(wizardStepDone[5]) || Boolean(adminStatus?.review_state?.materialize_done),
                6: smokePassed || Boolean(wizardStepDone[6]),
                7: humanReviewed || Boolean(wizardStepDone[7]),
                8: readyForCustomerTest || Boolean(wizardStepDone[8]),
              };
              // Unlock from ingest plan when available; fall back to sequential done
              const canAccess = (n: number) => {
                if (n === 1 || n === 2) return true;
                if (ingestPlan?.wizard_unlocks && typeof planUnlocks[n] === 'boolean') {
                  // Also require prior steps marked done for UX sequence
                  for (let i = 1; i < n; i++) {
                    if (i >= 3 && !stepDone[i] && !planUnlocks[i]) return false;
                  }
                  return Boolean(planUnlocks[n]) || stepDone[n] || (n > 1 && stepDone[n - 1]);
                }
                if (n === 1) return true;
                for (let i = 1; i < n; i++) if (!stepDone[i]) return false;
                return true;
              };
              const current = adminWizardStep;
              const stepsMeta = [
                { id: 1, title: 'Sources', blurb: 'Confirm files on disk' },
                { id: 2, title: 'Fetch & preview', blurb: 'See NEW vs UPDATE vs live graph' },
                { id: 3, title: 'Select products', blurb: 'Check only what enters the KG' },
                { id: 4, title: 'Validate ABox', blurb: 'TBox shapes on selection' },
                { id: 5, title: 'Materialize', blurb: 'Write catalog for selection only' },
                { id: 6, title: 'Smoke', blurb: 'Diagnosis scenarios' },
                { id: 7, title: 'Approve', blurb: 'Human gate' },
                { id: 8, title: 'Promote', blurb: 'MERGE selection → Neo4j' },
              ];

              const markDone = (n: number) => {
                setWizardStepDone((prev) => ({ ...prev, [n]: true }));
                setAdminWizardStep(Math.min(8, n + 1));
              };

              /** Primary action for a step is locked after success (until Fetch or explicit re-run). */
              const stepActionLocked = (n: number) => Boolean(stepDone[n]);
              const onboardingComplete = Boolean(stepDone[8] || promoteResult?.ok);

              return (
              <div className="max-w-4xl mx-auto space-y-4 pb-12">
                <div>
                  <div className="flex items-center gap-2">
                    <Shield className="w-7 h-7 text-violet-400" />
                    <h1 className="text-2xl font-semibold tracking-tight">Admin · Onboard (step by step)</h1>
                  </div>
                  <p className="text-sm text-white/55 mt-1">
                    Extract → detect NEW / UPDATE / TBox-extension → system recommends next actions.
                    Materialize/Promote process <em>only</em> selected products (fail-closed).
                  </p>
                </div>

                {/* Ingest plan — system recommendations */}
                <div className="card p-4 border border-cyan-500/30 space-y-3">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <div className="text-[10px] uppercase tracking-widest text-cyan-300/80">Ingest plan (recommended)</div>
                      <div className="font-semibold text-sm mt-0.5">
                        {ingestPlan?.headline || 'Run Fetch to build a plan from sources vs live graph'}
                      </div>
                    </div>
                    <button
                      type="button"
                      className="btn btn-secondary text-[11px] py-0.5"
                      title="Re-diff catalog vs production Neo4j and recompute recommended steps. Does not re-fetch source files or write to Neo4j."
                      onClick={async () => {
                        await refreshIngestPlan({ quiet: false, withStatus: true });
                      }}
                    >
                      Refresh plan
                    </button>
                  </div>
                  <p className="text-[11px] text-white/40 leading-relaxed">
                    <b className="text-white/55">Refresh plan</b> re-reads the catalog vs production Neo4j and updates
                    NEW / pending UPDATE / in sync + the checklist below. It does <b>not</b> re-scan source files
                    (use <b>Fetch</b>) and does <b>not</b> promote (use step 8).
                  </p>
                  {nextPlanAction ? (
                    <div className="rounded-lg bg-violet-500/15 border border-violet-400/30 px-3 py-2 text-sm">
                      <span className="text-violet-200 font-medium">Next:</span>{' '}
                      {nextPlanAction.title}
                      <div className="text-[11px] text-white/50 mt-0.5">{nextPlanAction.reason}</div>
                    </div>
                  ) : (
                    <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/30 px-3 py-2 text-sm text-emerald-100/90 space-y-2">
                      <span className="font-medium">No next action for this session</span>
                      <div className="text-[11px] text-white/50">
                        {Number(diffSummary.new_count || 0) === 0 && Number(diffSummary.updated_count || 0) === 0
                          ? 'Fleet is fully in sync with production. Reset the wizard for a clean next cycle, or open Diagnosis Chat to test.'
                          : 'Recommended steps are all done (or idle). Fleet may still show pending UPDATEs — select more products or start the next batch.'}
                      </div>
                      {Number(diffSummary.new_count || 0) === 0 && Number(diffSummary.updated_count || 0) === 0 && (
                        <button
                          type="button"
                          className="btn btn-primary text-[11px] py-0.5"
                          onClick={() =>
                            resetWizardForNextCycle({
                              reason: 'Fleet idle — wizard reset for next plan.',
                            })
                          }
                        >
                          Reset wizard for next plan
                        </button>
                      )}
                    </div>
                  )}
                  {(ingestPlan?.recommended_actions || []).length > 0 && (
                    <ol className="space-y-1.5 text-xs">
                      {(ingestPlan.recommended_actions as any[]).map((a, i) => (
                        <li
                          key={a.action_id + i}
                          className={`flex gap-2 items-start rounded-lg px-2 py-1.5 border ${
                            a.status === 'done'
                              ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-100/90'
                              : a.blocking
                                ? 'border-amber-500/30 bg-amber-500/10'
                                : 'border-white/10 bg-white/[0.03]'
                          }`}
                        >
                          <span className="shrink-0 w-4">{a.status === 'done' ? '✓' : a.priority}</span>
                          <div className="min-w-0">
                            <div className="font-medium">{a.title}</div>
                            <div className="text-white/45 text-[11px]">{a.reason}</div>
                            {(a.product_ids || []).length > 0 && (
                              <div className="font-mono text-[10px] text-cyan-300/70 mt-0.5">
                                {(a.product_ids as string[]).slice(0, 10).join(', ')}
                                {a.product_ids.length > 10 ? '…' : ''}
                              </div>
                            )}
                          </div>
                        </li>
                      ))}
                    </ol>
                  )}
                  {ingestPlan?.detected && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[11px]">
                      <div className="glass rounded-lg p-2">
                        <div className="text-white/40">NEW</div>
                        <div className="text-lg font-semibold text-emerald-300">
                          {ingestPlan.detected.new_product?.count ?? 0}
                        </div>
                      </div>
                      <div className="glass rounded-lg p-2">
                        <div className="text-white/40">Pending UPDATE</div>
                        <div className="text-lg font-semibold text-amber-300">
                          {ingestPlan.detected.product_update?.count ?? 0}
                        </div>
                      </div>
                      <div className="glass rounded-lg p-2">
                        <div className="text-white/40">Already in sync</div>
                        <div className="text-lg font-semibold text-emerald-200/80">
                          {unchangedCount}
                        </div>
                      </div>
                      <div className="glass rounded-lg p-2">
                        <div className="text-white/40">TBox candidates</div>
                        <div className="text-lg font-semibold">
                          {ingestPlan.detected.tbox_extension?.count ?? 0}
                        </div>
                      </div>
                      <div className="glass rounded-lg p-2">
                        <div className="text-white/40">Materialize OK?</div>
                        <div className={`text-sm font-semibold ${planGates.allow_materialize ? 'text-emerald-300' : 'text-rose-300'}`}>
                          {String(!!planGates.allow_materialize)}
                        </div>
                        {planGates.block_reason && (
                          <div className="text-[10px] text-rose-300/80 mt-0.5">{planGates.block_reason}</div>
                        )}
                      </div>
                    </div>
                  )}
                  <div className="text-[11px] text-white/45 leading-relaxed border border-white/10 rounded-lg px-3 py-2 space-y-1">
                    <div className="text-[10px] uppercase tracking-widest text-white/40">Glossary</div>
                    <div>
                      <b className="text-amber-200">Pending UPDATE</b> — product already exists in production Neo4j, but the
                      <em> catalog still has more core ABox</em> (symptoms / failure modes / diagnostic steps / parts) than production.
                      That is work still to promote for that product.
                    </div>
                    <div>
                      <b className="text-emerald-200">Already in sync</b> — catalog core ABox counts match production Neo4j for that product
                      (typical after a successful promote). Not re-work; data remains in the graph.
                    </div>
                    <div>
                      <b className="text-emerald-300">NEW</b> — product id is not in production at all (first-time onboard).
                    </div>
                  </div>
                  {(ingestPlan?.detected?.tbox_extension?.candidates || []).length > 0 && (
                    <div className="text-[11px] text-amber-200/90 border border-amber-500/30 rounded-lg p-2 space-y-2">
                      <div>
                        Possible TBox extension keys:{' '}
                        {(ingestPlan.detected.tbox_extension.candidates as any[])
                          .map((c) => c.unknown_key)
                          .join(', ')}
                        . Review before materialize (governance).
                      </div>
                      {planGates.tbox_review_required && (
                        <button
                          type="button"
                          className="btn btn-secondary text-[11px] py-0.5"
                          onClick={async () => {
                            try {
                              const res = await adminFetch('/admin/pipeline/plan/acknowledge-tbox', {
                                method: 'POST',
                                body: JSON.stringify({}),
                              });
                              applyChangePreviewPayload(res);
                              recordAdminAction('tbox', true, 'TBox review acknowledged', res.message || 'OK');
                              toast.success('TBox review acknowledged — continue selection/validate');
                            } catch (e: any) {
                              toast.error(e?.message || 'Failed to acknowledge TBox review');
                            }
                          }}
                        >
                          Acknowledge TBox review &amp; continue ABox path
                        </button>
                      )}
                    </div>
                  )}
                </div>

                {/* Progress strip */}
                <div className="flex flex-wrap gap-1">
                  {stepsMeta.map((s) => {
                    const done = stepDone[s.id];
                    const active = current === s.id;
                    const locked = !canAccess(s.id);
                    return (
                      <button
                        key={s.id}
                        type="button"
                        disabled={locked}
                        onClick={() => !locked && setAdminWizardStep(s.id)}
                        className={`text-[11px] px-2 py-1.5 rounded-lg border transition ${
                          done ? 'border-emerald-500/40 bg-emerald-500/15 text-emerald-200'
                            : active ? 'border-violet-400/50 bg-violet-500/20 text-white'
                            : locked ? 'border-white/5 text-white/25 cursor-not-allowed'
                            : 'border-white/15 text-white/50'
                        }`}
                      >
                        {done ? '✓' : s.id}. {s.title}
                      </button>
                    );
                  })}
                </div>

                {/* Live scope banner */}
                <div className="glass rounded-xl px-3 py-2 text-xs flex flex-wrap gap-3 items-center">
                  <span>Selected for KG: <b className="text-cyan-300 font-mono">{selectedTotal ? selIds.join(', ') : 'none'}</b></span>
                  <button
                    type="button"
                    className="btn btn-ghost text-[10px] py-0.5 ml-auto"
                    disabled={entityDeltaBusy || !selIds.length}
                    onClick={async () => {
                      await refreshChangePreview(true);
                      await refreshIngestPlan();
                      await refreshEntityDelta(selIds);
                      await refreshNeo4jVerify(selIds);
                    }}
                  >
                    {entityDeltaBusy ? 'Refreshing…' : 'Refresh status'}
                  </button>
                </div>

                {/* ===== BATCH STATUS (this selection) vs FLEET ===== */}
                {selIds.length > 0 && (() => {
                  const batchDone =
                    Boolean(stepDone[8] || promoteResult?.ok) &&
                    Boolean(entityDelta?.summary?.all_fully_loaded_production || neo4jVerify?.ready_for_diagnosis_chat);
                  const batchPending =
                    Number(entityDelta?.summary?.total_core_entities_added || 0) > 0 &&
                    !entityDelta?.summary?.all_fully_loaded_production;
                  const fleetPending = Number(diffSummary.updated_count ?? 0);
                  return (
                    <div
                      className={`card p-4 space-y-2 border ${
                        batchDone
                          ? 'border-emerald-500/40 bg-emerald-500/10'
                          : batchPending
                            ? 'border-amber-500/40 bg-amber-500/10'
                            : 'border-white/15'
                      }`}
                    >
                      <div className="text-[10px] uppercase tracking-widest text-white/45">This batch (selection)</div>
                      {batchDone ? (
                        <>
                          <div className="font-semibold text-emerald-300 text-sm">
                            ✓ Batch complete — all selected products loaded on production Neo4j
                          </div>
                          <div className="text-xs text-white/60 font-mono">{selIds.join(', ')}</div>
                          <div className="text-[11px] text-white/50">
                            Diagnosis Chat can use this ABox. Fleet still has{' '}
                            <b className="text-amber-200">{fleetPending} pending UPDATE(s)</b> for other products —
                            that is remaining work, not a failure of this batch.
                          </div>
                        </>
                      ) : batchPending ? (
                        <>
                          <div className="font-semibold text-amber-200 text-sm">
                            Batch in progress / pending promote — catalog ahead of production for selection
                          </div>
                          <div className="text-xs text-white/60">
                            Finish Materialize → Smoke → Approve → Promote (production). Then this banner turns green.
                          </div>
                        </>
                      ) : (
                        <>
                          <div className="font-semibold text-white/80 text-sm">
                            Selection set — continue wizard steps, or refresh after promote
                          </div>
                          <div className="text-[11px] text-white/45">
                            Fleet: {fleetPending} pending UPDATE · {unchangedCount} already in sync (all products)
                          </div>
                        </>
                      )}
                    </div>
                  );
                })()}

                {/* ===== WHAT'S THE DELTA (entity-level) ===== */}
                {selIds.length > 0 && (
                  <div className={`card p-4 space-y-3 border ${
                    entityDelta?.summary?.all_fully_loaded_production
                      ? 'border-emerald-500/30'
                      : 'border-amber-500/30'
                  }`}>
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <div className="text-[10px] uppercase tracking-widest text-white/50">
                          Selection status (entity delta)
                        </div>
                        <div className="font-semibold text-sm mt-0.5">
                          {entityDeltaBusy
                            ? 'Computing catalog vs Neo4j…'
                            : entityDelta?.summary?.all_fully_loaded_production
                              ? `✓ ${selIds.length} selected product(s) in sync with production`
                              : entityDelta?.summary?.headline ||
                                'Refresh after promote to see IN SYNC vs still pending'}
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-1.5 text-[10px]">
                        <span className={`badge ${entityDelta?.summary?.all_fully_loaded_production ? 'badge-ok' : 'badge-warn'}`}>
                          prod Neo4j {entityDelta?.summary?.all_fully_loaded_production ? 'loaded' : 'missing ABox'}
                        </span>
                        <span className={`badge ${entityDelta?.summary?.all_fully_loaded_staging ? 'badge-ok' : 'badge-warn'}`}>
                          staging {entityDelta?.summary?.all_fully_loaded_staging ? 'loaded' : 'gap'}
                        </span>
                      </div>
                    </div>
                    <p className="text-[11px] text-white/45 leading-relaxed">
                      This panel is for your <b>selection only</b>. The plan header “Pending UPDATE: N” is the <b>whole fleet</b>
                      (other products not in this batch). After a successful production promote, selected products should show{' '}
                      <b className="text-emerald-300">IN SYNC</b> here.
                    </p>
                    {Number(entityDelta?.summary?.in_sync_count || 0) > 0 && (
                      <div className="flex flex-wrap items-center gap-2 rounded-lg border border-emerald-500/25 bg-emerald-500/10 px-3 py-2">
                        <div className="text-[11px] text-emerald-100/90 flex-1 min-w-[12rem]">
                          <b>{entityDelta.summary.in_sync_count}</b> selected product(s) already{' '}
                          <b>IN SYNC</b> on production
                          {Number(entityDelta?.summary?.actionable_count || 0) > 0
                            ? ` · ${entityDelta.summary.actionable_count} still need work`
                            : ' · nothing left to promote in this batch'}
                        </div>
                        <button
                          type="button"
                          className="btn btn-primary text-[11px] py-0.5"
                          disabled={entityDeltaBusy}
                          title="Remove products already IN SYNC on production from this batch (works after Confirm selection)"
                          onClick={() => handleDropInSyncFromSelection()}
                        >
                          Drop IN SYNC from selection
                        </button>
                      </div>
                    )}

                    {(entityDelta?.products || []).map((p: any) => {
                      const matrix = p.count_matrix || {};
                      const typeOrder = ['symptoms', 'failure_modes', 'diagnostic_steps', 'parts', 'components', 'error_codes'];
                      const typeLabel: Record<string, string> = {
                        symptoms: 'Symptoms',
                        failure_modes: 'Failure modes',
                        diagnostic_steps: 'Diagnostic steps',
                        parts: 'Parts',
                        components: 'Components',
                        error_codes: 'Error codes',
                      };
                      return (
                        <div key={p.product_id} className="rounded-xl border border-white/10 bg-white/[0.03] p-3 space-y-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-mono text-cyan-300 font-semibold">{p.product_id}</span>
                            <span className="text-white/70 text-sm">{p.product_name}</span>
                            {(() => {
                              const inSync =
                                p.change_kind === 'in_sync' ||
                                (p.neo4j?.production?.fully_loaded && !(p.totals?.core_added > 0));
                              const isNew = p.change_kind === 'new_product';
                              const missingCat = p.change_kind === 'missing_catalog';
                              return (
                            <span className={`badge text-[10px] ${
                              inSync || isNew ? 'badge-ok' : 'badge-warn'
                            }`}>
                              {inSync
                                ? 'IN SYNC'
                                : isNew
                                  ? 'NEW PRODUCT'
                                  : missingCat
                                    ? 'NEEDS MATERIALIZE'
                                    : 'PENDING UPDATE'}
                            </span>
                              );
                            })()}
                            {p.bulletin_id && (
                              <span className="text-[10px] font-mono text-violet-300/80">bulletin {p.bulletin_id}</span>
                            )}
                          </div>
                          <div className="text-xs text-white/70">{p.headline}</div>
                          {(p.change_kind === 'in_sync' ||
                            (p.neo4j?.production?.fully_loaded && !(p.totals?.core_added > 0))) && (
                            <div className="text-[11px] text-emerald-200/70">
                              Core ABox already on production — uncheck this product unless you
                              intentionally want a no-op promote. Plan header “Pending UPDATE” is the
                              fleet list; this panel is catalog ↔ Neo4j for your selection only.
                            </div>
                          )}
                          {p.change_kind === 'missing_catalog' && (
                            <div className="text-[11px] text-amber-200/80">
                              Product is not in enterprise catalog yet — run Materialize (step 5)
                              after Validate so entity counts appear here.
                            </div>
                          )}

                          {/* Count matrix */}
                          <div className="overflow-x-auto">
                            <table className="w-full text-[11px] text-left">
                              <thead className="text-white/40">
                                <tr>
                                  <th className="py-1 pr-2 font-normal">Entity</th>
                                  <th className="py-1 pr-2 font-normal">Catalog</th>
                                  <th className="py-1 pr-2 font-normal">Staging</th>
                                  <th className="py-1 pr-2 font-normal">Production</th>
                                  <th className="py-1 font-normal">Δ vs prod</th>
                                </tr>
                              </thead>
                              <tbody>
                                {typeOrder.map((k) => {
                                  const row = matrix[k] || {};
                                  const delta = Number(row.added_vs_compare || 0);
                                  return (
                                    <tr key={k} className="border-t border-white/5">
                                      <td className="py-1 pr-2 text-white/60">{typeLabel[k] || k}</td>
                                      <td className="py-1 pr-2 font-mono">{row.catalog ?? '—'}</td>
                                      <td className="py-1 pr-2 font-mono">{row.staging ?? '—'}</td>
                                      <td className="py-1 pr-2 font-mono">{row.production ?? '—'}</td>
                                      <td className={`py-1 font-mono ${delta > 0 ? 'text-amber-300' : 'text-emerald-400/80'}`}>
                                        {delta > 0 ? `+${delta} NEW` : '0'}
                                      </td>
                                    </tr>
                                  );
                                })}
                              </tbody>
                            </table>
                          </div>

                          {/* NEW entities list */}
                          {(p.human_summary || []).filter((h: string) => h.startsWith('+') && !h.includes('HistoricalResolution')).length > 0 && (
                            <div>
                              <div className="text-[10px] uppercase tracking-widest text-amber-200/70 mb-1">New in catalog (not yet on compare env)</div>
                              <ul className="space-y-1 max-h-36 overflow-y-auto text-[11px]">
                                {(p.human_summary as string[])
                                  .filter((h) => h.startsWith('+') && !h.includes('HistoricalResolution'))
                                  .slice(0, 16)
                                  .map((h: string, i: number) => (
                                    <li key={i} className="text-emerald-200/90 font-mono leading-snug">{h}</li>
                                  ))}
                              </ul>
                            </div>
                          )}

                          {/* Ontology / RDF map (always visible when delta has hits) */}
                          {(p.rdf_highlight?.ontology_hits || []).length > 0 && (
                            <div className="rounded-lg border border-amber-500/25 bg-amber-500/5 px-2 py-2 space-y-1.5">
                              <div className="text-[10px] uppercase tracking-widest text-amber-200/80">
                                Ontology map (TBox class → NEW ABox instance)
                              </div>
                              <div className="text-[10px] text-white/40">
                                TBox unchanged. Only these ABox IRIs / edges are new:
                              </div>
                              {(p.rdf_highlight.ontology_hits as any[]).slice(0, 8).map((h: any) => (
                                <div key={h.entity_id} className="font-mono text-[10px] text-amber-100/90 leading-snug border-l-2 border-amber-400/70 pl-2">
                                  <span className="text-cyan-300/90">{h.owl_class}</span>
                                  {' ← '}
                                  <span className="text-amber-200">{h.instance_iri}</span>
                                  <span className="text-white/35"> ({h.entity_id})</span>
                                  <div className="text-white/40">
                                    {h.product_link?.subject_iri} -[{h.product_link?.neo4j_rel}]→ {h.instance_iri}
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}

                          {(p.field_changes || []).length > 0 && (
                            <div className="text-[11px] text-white/50">
                              Field/count signals:{' '}
                              {(p.field_changes as any[]).slice(0, 6).map((f, i) => (
                                <span key={i} className="inline-block mr-2 font-mono text-amber-200/80">
                                  {f.field}: {String(f.from)}→{String(f.to)}
                                </span>
                              ))}
                            </div>
                          )}

                          <div className="flex flex-wrap gap-2 text-[10px] pt-1">
                            <span className={p.neo4j?.production?.fully_loaded ? 'text-emerald-400' : 'text-rose-300'}>
                              prod fully_loaded={String(!!p.neo4j?.production?.fully_loaded)}
                            </span>
                            <span className={p.neo4j?.staging?.fully_loaded ? 'text-emerald-400' : 'text-amber-300'}>
                              stg fully_loaded={String(!!p.neo4j?.staging?.fully_loaded)}
                            </span>
                            {(p.neo4j?.production?.missing_catalog_ids || []).length > 0 && (
                              <span className="text-rose-300/90 truncate max-w-full">
                                missing on prod: {(p.neo4j.production.missing_catalog_ids as string[]).slice(0, 6).join(', ')}
                              </span>
                            )}
                          </div>

                          <div className="flex flex-wrap gap-2">
                            <button
                              type="button"
                              className="btn btn-secondary text-[10px] py-0.5"
                              onClick={() => {
                                setExplorerProductId(p.product_id);
                                setActiveView('explorer');
                                setTimeout(() => loadExplorer(p.product_id, false), 50);
                              }}
                            >
                              Open graph
                            </button>
                            <button
                              type="button"
                              className="btn btn-secondary text-[10px] py-0.5"
                              onClick={() => loadRdfForSelection(p.product_id)}
                            >
                              View RDF/OWL
                            </button>
                          </div>
                        </div>
                      );
                    })}

                    {!entityDelta?.products?.length && !entityDeltaBusy && (
                      <div className="text-[11px] text-white/40">
                        No delta loaded yet — click <b>Refresh what’s changing</b> after locking a selection.
                      </div>
                    )}

                    {/* Neo4j / Docker verification strip */}
                    {neo4jVerify && (
                      <div className="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-[11px] space-y-1">
                        <div className="text-[10px] uppercase tracking-widest text-white/40">Neo4j / Docker verification</div>
                        <div className="flex flex-wrap gap-3">
                          <span>
                            production {neo4jVerify.connectivity?.production?.uri}{' '}
                            <b className={neo4jVerify.connectivity?.production?.connected ? 'text-emerald-400' : 'text-rose-400'}>
                              {neo4jVerify.connectivity?.production?.connected ? 'connected' : 'down'}
                            </b>
                          </span>
                          <span>
                            staging {neo4jVerify.connectivity?.staging?.uri}{' '}
                            <b className={neo4jVerify.connectivity?.staging?.connected ? 'text-emerald-400' : 'text-rose-400'}>
                              {neo4jVerify.connectivity?.staging?.connected ? 'connected' : 'down'}
                            </b>
                          </span>
                        </div>
                        <div className={neo4jVerify.ready_for_diagnosis_chat ? 'text-emerald-300' : 'text-amber-200'}>
                          {neo4jVerify.ready_for_diagnosis_chat
                            ? '✓ Selection fully loaded on production — Diagnosis Chat can use new ABox'
                            : '⚠ Not fully on production yet — promote to production or check missing ids above'}
                        </div>
                        <div className="text-white/35">{neo4jVerify.note}</div>
                      </div>
                    )}

                    {showRdfPreview && rdfPreview && (
                      <div className="rounded-lg border border-amber-500/40 bg-violet-500/5 p-3 space-y-3">
                        <div className="flex flex-wrap justify-between items-center gap-2">
                          <div>
                            <div className="text-[10px] uppercase tracking-widest text-amber-300/90">
                              Ontology + RDF delta · {rdfPreview.productId}
                            </div>
                            <div className="text-[11px] text-white/50 mt-0.5">
                              {rdfPreview.tbox_changed
                                ? 'TBox change detected'
                                : 'TBox unchanged — only ABox instances grow (bulletin UPDATE)'}
                              {rdfPreview.abox_changed ? ' · ABox has NEW instances' : ' · ABox in sync'}
                            </div>
                          </div>
                          <button type="button" className="btn btn-ghost text-[10px]" onClick={() => setShowRdfPreview(false)}>
                            Close
                          </button>
                        </div>

                        {rdfPreview.tbox_summary && (
                          <div className="text-[11px] text-white/55 border border-white/10 rounded-lg px-2 py-1.5">
                            {rdfPreview.tbox_summary}
                          </div>
                        )}

                        {/* Exact ontology locations */}
                        {(rdfPreview.ontology_hits || []).length > 0 && (
                          <div className="space-y-2">
                            <div className="text-[10px] uppercase tracking-widest text-amber-200/80">
                              Where the change lands in the ontology
                            </div>
                            <div className="space-y-2 max-h-56 overflow-y-auto">
                              {(rdfPreview.ontology_hits as any[]).map((h) => (
                                <div
                                  key={h.entity_id}
                                  className="rounded-lg border border-amber-400/40 bg-amber-500/10 px-3 py-2 text-[11px]"
                                >
                                  <div className="flex flex-wrap items-center gap-2">
                                    <span className="badge badge-warn text-[9px]">NEW ABox</span>
                                    <span className="font-mono text-amber-100">{h.entity_id}</span>
                                    <span className="text-white/70">{h.label}</span>
                                  </div>
                                  <div className="mt-1.5 grid gap-0.5 font-mono text-[10px] text-white/65">
                                    <div>
                                      <span className="text-white/35">OWL class (TBox, existing): </span>
                                      <span className="text-cyan-300">{h.owl_class}</span>
                                    </div>
                                    <div>
                                      <span className="text-white/35">Instance IRI (NEW): </span>
                                      <span className="text-amber-200">{h.instance_iri}</span>
                                    </div>
                                    <div>
                                      <span className="text-white/35">Product link: </span>
                                      <span className="text-emerald-300/90">
                                        {h.product_link?.subject_iri} —{h.product_link?.property}→ {h.product_link?.object_iri}
                                      </span>
                                    </div>
                                    <div>
                                      <span className="text-white/35">Neo4j: </span>
                                      <span className="text-white/80">
                                        {`(:Product)-[:${h.product_link?.neo4j_rel || 'REL'}]->(…)`}
                                      </span>
                                    </div>
                                  </div>
                                  <div className="text-[10px] text-white/40 mt-1">{h.tbox_note}</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {(rdfPreview.ontology_hits || []).length === 0 && (
                          <div className="text-[11px] text-emerald-300/90">
                            No NEW ABox IRIs vs production — core ontology instances already match.
                          </div>
                        )}

                        <div className="flex flex-wrap gap-1.5">
                          {(
                            [
                              ['new_only', 'NEW triples only'],
                              ['full_abox', 'Full product ABox'],
                              ['schema', 'TBox schema only'],
                            ] as const
                          ).map(([mode, label]) => (
                            <button
                              key={mode}
                              type="button"
                              className={`btn text-[10px] py-0.5 ${rdfViewMode === mode ? 'btn-primary' : 'btn-secondary'}`}
                              onClick={async () => {
                                setRdfViewMode(mode);
                                if (mode === 'schema' && !rdfPreview.turtle_schema) {
                                  try {
                                    const schema = await api.getRdfSchema();
                                    setRdfPreview((prev: any) => ({
                                      ...prev,
                                      turtle_schema: schema.turtle || schema.schema || '',
                                    }));
                                  } catch {
                                    /* ignore */
                                  }
                                }
                              }}
                            >
                              {label}
                            </button>
                          ))}
                        </div>

                        <div className="text-[10px] text-white/40">
                          Amber highlight = line mentions a NEW entity id ({(rdfPreview.new_entity_ids || []).join(', ') || 'none'})
                        </div>

                        {rdfViewMode === 'new_only' &&
                          renderHighlightedTurtle(
                            rdfPreview.turtle_new_only || '# No NEW triples (in sync with production)',
                            rdfPreview.new_entity_ids || []
                          )}
                        {rdfViewMode === 'full_abox' &&
                          renderHighlightedTurtle(rdfPreview.turtle_abox || '', rdfPreview.new_entity_ids || [])}
                        {rdfViewMode === 'schema' && (
                          <div className="space-y-1">
                            <div className="text-[11px] text-amber-200/90">
                              TBox is shared schema — classes below are <b>not</b> what this bulletin changes.
                              New data is instances under those classes (ABox tab).
                            </div>
                            {renderHighlightedTurtle(
                              rdfPreview.turtle_schema || 'Loading schema…',
                              ['Symptom', 'FailureMode', 'DiagnosticStep', 'Part', 'hasSymptom', 'canHave', 'hasDiagnosticStep']
                            )}
                          </div>
                        )}

                        {(rdfPreview.how_to_read || []).length > 0 && (
                          <ul className="text-[10px] text-white/40 list-disc pl-4 space-y-0.5">
                            {(rdfPreview.how_to_read as string[]).map((t: string, i: number) => (
                              <li key={i}>{t}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* keep original live banner stats on next line - scope already shown */}
                <div className="glass rounded-xl px-3 py-2 text-xs flex flex-wrap gap-3 items-center">
                  <span className="text-white/40">Gates</span>
                  <span className="text-white/40">Smoke={String(smokePassed)} · Approved={String(humanReviewed)}</span>
                  {(fetchBusy || kgRunBusy || ontologyBusy) && (
                    <span className="text-amber-200 flex items-center gap-1"><RefreshCw className="w-3 h-3 animate-spin" /> Working…</span>
                  )}
                </div>

                {adminLastAction && (
                  <div ref={adminResultRef} className={`rounded-xl px-3 py-2 text-sm border ${adminLastAction.ok ? 'border-emerald-500/40 bg-emerald-500/10' : 'border-rose-500/40 bg-rose-500/10'}`}>
                    <b>{adminLastAction.ok ? '✓' : '✗'} {adminLastAction.title}</b>
                    <span className="text-white/70"> — {adminLastAction.message}</span>
                    {adminLastAction.details?.product_ids && (
                      <div className="text-[11px] font-mono text-white/45 mt-1">scope: {JSON.stringify(adminLastAction.details.product_ids)}</div>
                    )}
                  </div>
                )}

                {/* ===== STEP 1 ===== */}
                <div className={`card p-4 ${current === 1 ? 'ring-1 ring-violet-400/40' : 'opacity-80'}`}>
                  <button type="button" className="w-full flex justify-between text-left" onClick={() => canAccess(1) && setAdminWizardStep(1)} disabled={!canAccess(1)}>
                    <span className="font-semibold">{stepDone[1] ? '✓' : '1.'} Sources</span>
                    {current === 1 ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4 text-white/30" />}
                  </button>
                  {current === 1 && (
                    <div className="mt-3 space-y-2 border-t border-white/10 pt-3">
                      <div className="text-xs text-white/50 space-y-1">
                        <div className={kgInventory?.file_count ? 'text-emerald-300' : ''}>□ Scan pipeline + enterprise source files</div>
                        <div className={kgInventory?.product_ids_seen?.length ? 'text-emerald-300' : ''}>□ Note product IDs present in sources</div>
                      </div>
                      <button type="button" className="btn btn-primary text-xs" disabled={kgInventoryBusy} onClick={async () => {
                        await refreshSourceInventory();
                        recordAdminAction('inventory', true, 'Sources scanned', `${(await refreshSourceInventory(), kgInventory?.file_count) ?? 'files'} files — see list below`);
                        setShowSourceInventory(true);
                        markDone(1);
                      }}>
                        Scan sources &amp; continue
                      </button>
                      {showSourceInventory && (
                        <div className="text-[11px] font-mono max-h-32 overflow-auto text-white/50">
                          Products: {(kgInventory?.product_ids_seen || []).join(', ') || '—'}
                          <div className="mt-1">{(kgInventory?.files || []).slice(0, 12).map((f: any) => f.path).join('\n')}</div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* ===== STEP 2 ===== */}
                <div className={`card p-4 ${current === 2 ? 'ring-1 ring-violet-400/40' : 'opacity-80'}`}>
                  <button type="button" className="w-full flex justify-between text-left" disabled={!canAccess(2)} onClick={() => canAccess(2) && setAdminWizardStep(2)}>
                    <span className="font-semibold">{stepDone[2] ? '✓' : '2.'} Fetch &amp; preview</span>
                    {current === 2 ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4 text-white/30" />}
                  </button>
                  {current === 2 && canAccess(2) && (
                    <div className="mt-3 space-y-3 border-t border-white/10 pt-3" ref={changePreviewRef}>
                      <div className="text-xs text-white/50 space-y-1">
                        <div>□ Pull PIM/CRM/FSM/Claims (dry-run, no Neo4j write)</div>
                        <div>□ Diff catalog vs <b className="text-white/70">production</b> Neo4j (fleet-wide, not just this session)</div>
                        <div>□ Products already promoted &amp; matching production leave the UPDATE list</div>
                        <div>□ Selection / wizard gates reset; audit + Neo4j data <b className="text-white/70">persist</b></div>
                      </div>
                      <button type="button" className="btn btn-primary text-xs" disabled={fetchBusy} onClick={async () => {
                        await handleDryRunETL();
                        markDone(2);
                      }}>
                        {fetchBusy ? 'Fetching…' : 'Run fetch & show preview'}
                      </button>
                      {changePreview && (
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-sm">
                          <div className="glass p-2 rounded-lg"><div className="text-[10px] text-emerald-300">NEW</div><div className="text-xl font-semibold">{diffSummary.new_count ?? 0}</div></div>
                          <div className="glass p-2 rounded-lg"><div className="text-[10px] text-amber-300">Pending UPDATE</div><div className="text-xl font-semibold">{diffSummary.updated_count ?? 0}</div></div>
                          <div className="glass p-2 rounded-lg"><div className="text-[10px] text-emerald-200/80">Already in sync</div><div className="text-xl font-semibold">{unchangedCount}</div></div>
                          <div className="glass p-2 rounded-lg"><div className="text-[10px] text-white/40">Live graph</div><div className="text-xl font-semibold">{changePreview?.live_graph?.production?.count ?? '—'}</div></div>
                          <div className="glass p-2 rounded-lg"><div className="text-[10px] text-white/40">Incoming</div><div className="text-xl font-semibold">{changePreview?.incoming_products?.length ?? '—'}</div></div>
                        </div>
                      )}
                      {changePreview?.headline && <p className="text-xs text-white/60">{changePreview.headline}</p>}
                      {changePreview?.fleet_note && (
                        <p className="text-[11px] text-white/40 leading-relaxed">{changePreview.fleet_note}</p>
                      )}
                      {adminLastAction?.details?.sources && (
                        <div className="text-[11px] font-mono text-white/45">
                          Sources: {JSON.stringify(adminLastAction.details.sources)}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* ===== STEP 3 SELECT ===== */}
                <div className={`card p-4 ${current === 3 ? 'ring-1 ring-violet-400/40' : 'opacity-80'}`}>
                  <button type="button" className="w-full flex justify-between text-left" disabled={!canAccess(3)} onClick={() => canAccess(3) && setAdminWizardStep(3)}>
                    <span className="font-semibold">{stepDone[3] ? '✓' : '3.'} Select products ({selectedTotal})</span>
                    {current === 3 ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4 text-white/30" />}
                  </button>
                  {current === 3 && canAccess(3) && (
                    <div className="mt-3 space-y-3 border-t border-white/10 pt-3">
                      <p className="text-xs text-white/50">
                        Check only products to materialize/promote. Unchecked products are <b className="text-white/70">not</b> processed.
                      </p>
                      {stepActionLocked(3) && (
                        <div className="text-[11px] text-emerald-300/90 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-2 py-1.5">
                          ✓ Selection locked for this run: <span className="font-mono">{selIds.join(', ')}</span>
                          {' '}— pick other products only after <b>Fetch</b> or unlock below.
                        </div>
                      )}
                      <div className="flex flex-wrap gap-1">
                        <button type="button" className="btn btn-secondary text-[11px] py-0.5" disabled={stepActionLocked(3)} onClick={() => handleProductSelection({ select_all_new: true })}>All NEW on</button>
                        <button type="button" className="btn btn-secondary text-[11px] py-0.5" disabled={stepActionLocked(3)} onClick={() => handleProductSelection({ select_all_new: false, select_all_updated: false })}>Clear all</button>
                      </div>
                      <div className="grid md:grid-cols-3 gap-2">
                        <div className="border border-emerald-500/25 rounded-xl p-2 max-h-56 overflow-auto">
                          <div className="text-[10px] text-emerald-300 mb-1">NEW ({newProducts.length})</div>
                          {newProducts.map((p: any) => (
                            <label key={p.product_id} className={`flex gap-2 text-xs py-1 px-1 rounded ${p.selected ? 'bg-emerald-500/15' : 'opacity-50'}`}>
                              <input type="checkbox" disabled={stepActionLocked(3)} checked={Boolean(p.selected)} onChange={(e) => handleProductSelection({ product_id: p.product_id, selected: e.target.checked })} />
                              <span className="font-mono">{p.product_id}</span> <span className="text-white/50 truncate">{p.name}</span>
                            </label>
                          ))}
                          {!newProducts.length && (
                            <div className="text-xs text-white/40">
                              No brand-new product IDs. Check <b>Pending UPDATES</b> for bulletin ABox still not on production.
                            </div>
                          )}
                        </div>
                        <div className="border border-amber-500/25 rounded-xl p-2 max-h-56 overflow-auto">
                          <div className="text-[10px] text-amber-200 mb-1">Pending UPDATES ({updatedProducts.length})</div>
                          {updatedProducts.map((p: any) => (
                            <label key={p.product_id} className={`flex gap-2 text-xs py-1 px-1 rounded ${p.selected ? 'bg-amber-500/15' : 'opacity-50'}`}>
                              <input type="checkbox" disabled={stepActionLocked(3)} checked={Boolean(p.selected)} onChange={(e) => handleProductSelection({ product_id: p.product_id, selected: e.target.checked })} />
                              <div className="min-w-0">
                                <span className="font-mono">{p.product_id}</span>
                                {p.bulletin_id && <span className="text-amber-200/70"> · {p.bulletin_id}</span>}
                                <div className="text-[10px] text-white/40 truncate">{p.reason || p.name}</div>
                              </div>
                            </label>
                          ))}
                          {!updatedProducts.length && <div className="text-xs text-white/40">No pending ABox growth vs production.</div>}
                        </div>
                        <div className="border border-emerald-500/15 rounded-xl p-2 max-h-56 overflow-auto">
                          <div className="text-[10px] text-emerald-200/80 mb-1">
                            Already in sync ({unchangedCount}) — promoted / no delta
                          </div>
                          <p className="text-[10px] text-white/35 mb-1.5">
                            Catalog matches production. These stay in Neo4j — not re-work.
                          </p>
                          {(unchangedProducts as any[]).slice(0, 40).map((p: any) => (
                            <div key={p.product_id} className="text-xs py-0.5 font-mono text-white/45">
                              ✓ {p.product_id}
                              {p.name ? <span className="text-white/30 font-sans"> · {p.name}</span> : null}
                            </div>
                          ))}
                          {!unchangedCount && (
                            <div className="text-xs text-white/40">None fully match production yet.</div>
                          )}
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        <button type="button" className="btn btn-secondary text-[11px] py-0.5" disabled={stepActionLocked(3)} onClick={() => handleProductSelection({ select_all_updated: true })}>
                          Select all UPDATES
                        </button>
                        <button type="button" className="btn btn-secondary text-[11px] py-0.5" disabled={stepActionLocked(3)} onClick={() => handleProductSelection({ select_all_new: true })}>
                          Select all NEW
                        </button>
                        <button
                          type="button"
                          className="btn btn-secondary text-[11px] py-0.5"
                          disabled={
                            entityDeltaBusy ||
                            (selectedFromPreview.length === 0 &&
                              lockedSelectionIds.length === 0 &&
                              !(entityDelta?.products || []).length)
                          }
                          title="Uncheck products already fully loaded on production (catalog vs Neo4j IN SYNC). Stays enabled after Confirm selection."
                          onClick={() => handleDropInSyncFromSelection()}
                        >
                          Drop IN SYNC from selection
                        </button>
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <button
                          type="button"
                          className={`btn text-xs ${stepActionLocked(3) ? 'btn-secondary' : 'btn-primary'}`}
                          disabled={stepActionLocked(3) || (selectedFromPreview.length === 0 && lockedSelectionIds.length === 0)}
                          onClick={async () => {
                            const ids =
                              selectedFromPreview.length > 0 ? selectedFromPreview : lockedSelectionIds;
                            if (!ids.length) return;
                            try {
                              const res = await adminFetch('/admin/pipeline/plan/lock-selection', {
                                method: 'POST',
                                body: JSON.stringify({ product_ids: ids, prune_in_sync: true }),
                              });
                              applyChangePreviewPayload(res);
                              const kept = res.locked_selection_ids || ids;
                              setLockedSelectionIds(kept);
                              recordAdminAction(
                                'select',
                                true,
                                'Selection locked',
                                res.message || `${kept.length} product(s): ${kept.join(', ')}`,
                                {
                                  product_ids: kept,
                                  dropped_in_sync: res.dropped_in_sync,
                                  next: res.ingest_plan?.next_action?.action_id,
                                }
                              );
                              if ((res.dropped_in_sync || []).length) {
                                toast.success('Selection pruned', {
                                  description: res.message,
                                });
                              }
                              await refreshEntityDelta(kept);
                              await refreshNeo4jVerify(kept);
                              markDone(3);
                            } catch (e: any) {
                              const detail = e?.message || 'Lock selection failed';
                              recordAdminAction('select', false, 'Selection lock failed', detail);
                              toast.error('Could not lock selection', { description: detail });
                            }
                          }}
                        >
                          {stepActionLocked(3)
                            ? `✓ Selection confirmed (${selIds.length})`
                            : `Confirm selection (${selectedFromPreview.length || lockedSelectionIds.length}) & continue`}
                        </button>
                        {stepActionLocked(3) && (
                          <button
                            type="button"
                            className="btn btn-ghost text-[11px]"
                            onClick={() => {
                              setWizardStepDone((prev) => {
                                const n: Record<number, boolean> = { ...prev };
                                for (const k of [3, 4, 5, 6, 7, 8]) delete n[k];
                                return n;
                              });
                              setLockedSelectionIds([]);
                              setPromoteResult(null);
                            }}
                          >
                            Change selection
                          </button>
                        )}
                      </div>
                      {selectedTotal === 0 && updatedProducts.length > 0 && !stepActionLocked(3) && (
                        <p className="text-[11px] text-amber-200/80">
                          Updates default to <b>unchecked</b> (opt-in). Click <b>Select all UPDATES</b> or check individual products, then Confirm.
                        </p>
                      )}
                    </div>
                  )}
                </div>

                {/* ===== STEP 4 VALIDATE ===== */}
                <div className={`card p-4 ${current === 4 ? 'ring-1 ring-violet-400/40' : 'opacity-80'}`}>
                  <button type="button" className="w-full flex justify-between text-left" disabled={!canAccess(4)} onClick={() => canAccess(4) && setAdminWizardStep(4)}>
                    <span className="font-semibold">{stepDone[4] ? '✓' : '4.'} Validate ABox</span>
                    {current === 4 ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4 text-white/30" />}
                  </button>
                  {current === 4 && canAccess(4) && (
                    <div className="mt-3 space-y-2 border-t border-white/10 pt-3">
                      <div className="text-xs text-white/50">Scope: <span className="font-mono text-cyan-300">{selIds.join(', ') || '—'}</span></div>
                      <button
                        type="button"
                        className={`btn text-xs ${stepActionLocked(4) ? 'btn-secondary' : 'btn-primary'}`}
                        disabled={stepActionLocked(4) || ontologyBusy || selectedTotal === 0}
                        onClick={async () => {
                          const ok = await handleOntologyValidate();
                          if (ok) markDone(4);
                        }}
                      >
                        {ontologyBusy
                          ? 'Validating…'
                          : stepActionLocked(4)
                            ? '✓ ABox validation passed'
                            : 'Validate selected ABox'}
                      </button>
                      {!stepActionLocked(4) && (
                        <button type="button" className="btn btn-secondary text-xs ml-2" disabled={!ontologyValidation || (ontologyValidation.failed_count > 0 && !ontologyValidation.ok)} onClick={() => markDone(4)}>
                          Continue after validation
                        </button>
                      )}
                      {ontologyValidation && (
                        <div className={`text-xs p-2 rounded-lg border ${ontologyValidation.failed_count ? 'border-amber-500/40' : 'border-emerald-500/40'}`}>
                          {ontologyValidation.headline}
                          <div className="font-mono mt-1">passed: {(ontologyValidation.passed_product_ids || []).join(', ')}</div>
                          {(ontologyValidation.failed_product_ids || []).length > 0 && (
                            <div className="text-rose-300">failed: {(ontologyValidation.failed_product_ids || []).join(', ')}</div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* ===== STEP 5 MATERIALIZE ===== */}
                <div className={`card p-4 ${current === 5 ? 'ring-1 ring-violet-400/40' : 'opacity-80'}`}>
                  <button type="button" className="w-full flex justify-between text-left" disabled={!canAccess(5)} onClick={() => canAccess(5) && setAdminWizardStep(5)}>
                    <span className="font-semibold">{stepDone[5] ? '✓' : '5.'} Materialize (selection only)</span>
                    {current === 5 ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4 text-white/30" />}
                  </button>
                  {current === 5 && canAccess(5) && (
                    <div className="mt-3 space-y-2 border-t border-white/10 pt-3">
                      <div className="text-xs text-white/50 space-y-1">
                        <div>□ Multi-source chain → catalog upsert for <b className="text-cyan-300 font-mono">{selIds.join(', ')}</b> only</div>
                        <div>□ Other catalog products left untouched</div>
                        <div className={kgDryRun ? 'text-amber-300' : 'text-emerald-300'}>
                          {kgDryRun ? '⚠ Dry-run ON — uncheck to write catalog' : '✓ Will write catalog'}
                        </div>
                      </div>
                      <label className="flex items-center gap-2 text-xs text-white/60">
                        <input type="checkbox" checked={kgDryRun} disabled={stepActionLocked(5)} onChange={(e) => setKgDryRun(e.target.checked)} />
                        Dry-run only
                      </label>
                      <p className="text-[11px] text-white/45">
                        Uses <span className="font-mono">knowledge_materialize</span> only (not full bootstrap).
                        Smoke is the <b>next</b> step — a smoke fail will no longer mark materialize as failed.
                      </p>
                      {!planGates.allow_materialize && !stepActionLocked(5) && (
                        <div className="text-[11px] text-rose-300/90">
                          Plan blocks materialize: {planGates.block_reason || 'complete Validate ABox / selection first'}
                        </div>
                      )}
                      <button
                        type="button"
                        className={`btn text-xs ${stepActionLocked(5) ? 'btn-secondary' : 'btn-primary'}`}
                        disabled={
                          stepActionLocked(5) ||
                          kgRunBusy ||
                          selIds.length === 0 ||
                          (!kgDryRun && planGates.allow_materialize === false)
                        }
                        onClick={async () => {
                        await handleRunKgPipeline('knowledge_materialize', { dryRun: kgDryRun });
                        if (kgDryRun) {
                          recordAdminAction('pipeline', true, 'Dry-run materialize done', 'Uncheck dry-run and run again to write', { product_ids: selIds });
                        }
                        await refreshIngestPlan();
                      }}>
                        {kgRunBusy
                          ? 'Running…'
                          : stepActionLocked(5)
                            ? `✓ Materialized ${selIds.length} product(s)`
                            : `Materialize ${selIds.length} product(s)`}
                      </button>
                    </div>
                  )}
                </div>

                {/* ===== STEP 6 SMOKE ===== */}
                <div className={`card p-4 ${current === 6 ? 'ring-1 ring-violet-400/40' : 'opacity-80'}`}>
                  <button type="button" className="w-full flex justify-between text-left" disabled={!canAccess(6)} onClick={() => canAccess(6) && setAdminWizardStep(6)}>
                    <span className="font-semibold">{stepDone[6] ? '✓' : '6.'} Smoke validation</span>
                    {current === 6 ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4 text-white/30" />}
                  </button>
                  {current === 6 && canAccess(6) && (
                    <div className="mt-3 space-y-2 border-t border-white/10 pt-3">
                      <p className="text-[11px] text-white/45">
                        Runs enterprise diagnosis scenarios (washer / dishwasher / microwave smoke set).
                        Materialize already wrote the catalog for your selection; smoke must pass before Approve.
                      </p>
                      <button
                        type="button"
                        className={`btn text-xs ${stepActionLocked(6) || smokePassed ? 'btn-secondary' : 'btn-primary'}`}
                        disabled={stepActionLocked(6) || smokePassed || kgRunBusy}
                        onClick={async () => {
                          await handleValidate();
                        }}
                      >
                        {stepActionLocked(6) || smokePassed ? '✓ Smoke passed' : kgRunBusy ? 'Running…' : 'Run smoke'}
                      </button>
                      <div className="text-xs">Smoke: <span className={smokePassed ? 'text-emerald-400' : 'text-rose-400'}>{String(smokePassed)}</span></div>
                      {smokePassed && !stepActionLocked(6) && (
                        <button type="button" className="btn btn-secondary text-xs" onClick={() => markDone(6)}>Continue to Approve</button>
                      )}
                    </div>
                  )}
                </div>

                {/* ===== STEP 7 APPROVE ===== */}
                <div className={`card p-4 ${current === 7 ? 'ring-1 ring-violet-400/40' : 'opacity-80'}`}>
                  <button type="button" className="w-full flex justify-between text-left" disabled={!canAccess(7)} onClick={() => canAccess(7) && setAdminWizardStep(7)}>
                    <span className="font-semibold">{stepDone[7] ? '✓' : '7.'} Approve</span>
                    {current === 7 ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4 text-white/30" />}
                  </button>
                  {current === 7 && canAccess(7) && (
                    <div className="mt-3 space-y-2 border-t border-white/10 pt-3">
                      <p className="text-xs text-white/50">Confirm scope <span className="font-mono text-cyan-300">{selIds.join(', ')}</span> looks correct.</p>
                      <button
                        type="button"
                        className={`btn text-xs ${stepActionLocked(7) || humanReviewed ? 'btn-secondary' : 'btn-primary'}`}
                        disabled={stepActionLocked(7) || humanReviewed || !smokePassed}
                        onClick={async () => {
                          await handleApprove();
                          markDone(7);
                        }}
                      >
                        {stepActionLocked(7) || humanReviewed ? '✓ Approved' : 'Approve changes'}
                      </button>
                    </div>
                  )}
                </div>

                {/* ===== STEP 8 PROMOTE ===== */}
                {(() => {
                  const promoteScopeKey = `${kgTargetEnv}|${[...selIds].sort().join(',')}`;
                  const promoteAlreadyDone =
                    Boolean(promoteResult?.ok) && promoteResult?.scopeKey === promoteScopeKey;
                  const productionGatesOk = canPromote; // smoke + human approve
                  const promoteBlockedReason =
                    selIds.length === 0
                      ? 'Select at least one product first'
                      : kgTargetEnv === 'production' && !smokePassed
                        ? 'Smoke must pass before production promote'
                        : kgTargetEnv === 'production' && !humanReviewed
                          ? 'Approve (step 7) required before production promote'
                          : null;
                  const canClickPromote =
                    !promoteBusy &&
                    !kgRunBusy &&
                    !promoteAlreadyDone &&
                    !promoteBlockedReason;

                  return (
                <div className={`card p-4 ${current === 8 ? 'ring-1 ring-violet-400/40' : 'opacity-80'}`}>
                  <button type="button" className="w-full flex justify-between text-left" disabled={!canAccess(8)} onClick={() => canAccess(8) && setAdminWizardStep(8)}>
                    <span className="font-semibold">{stepDone[8] || promoteAlreadyDone ? '✓' : '8.'} Promote to Neo4j</span>
                    {current === 8 ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4 text-white/30" />}
                  </button>
                  {current === 8 && canAccess(8) && (
                    <div className="mt-3 space-y-3 border-t border-white/10 pt-3">
                      <div className="text-xs text-white/50">
                        MERGE only: <span className="font-mono text-cyan-300">{selIds.join(', ') || 'selection required'}</span>
                      </div>
                      <p className="text-[11px] text-white/45 leading-relaxed">
                        One promote action: pick the Neo4j target, then run.
                        <b className="text-white/70"> Staging</b> (:7688) is safe for validation;
                        <b className="text-white/70"> production</b> (:7687) powers Diagnosis Chat and needs smoke + approve.
                      </p>

                      <div className="flex flex-wrap items-center gap-2">
                        <label className="text-[11px] text-white/45">Target</label>
                        <select
                          className="input text-xs py-1 w-auto min-w-[140px]"
                          value={kgTargetEnv}
                          disabled={promoteBusy || kgRunBusy}
                          onChange={(e) => setKgTargetEnv(e.target.value as 'staging' | 'production')}
                        >
                          <option value="staging">staging (:7688)</option>
                          <option value="production">production (:7687)</option>
                        </select>
                      </div>

                      {promoteAlreadyDone && promoteResult && (
                        <div className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-sm">
                          <div className="font-semibold text-emerald-300">
                            ✓ Promotion successful → {promoteResult.target}
                          </div>
                          <div className="text-[11px] text-white/55 mt-0.5">
                            {promoteResult.productIds.join(', ')}
                            {promoteResult.at ? ` · ${promoteResult.at.slice(0, 19).replace('T', ' ')}` : ''}
                          </div>
                          {promoteResult.runId && (
                            <div className="text-[10px] font-mono text-white/35 mt-0.5">run {promoteResult.runId}</div>
                          )}
                        </div>
                      )}

                      {promoteResult && !promoteResult.ok && promoteResult.scopeKey === promoteScopeKey && (
                        <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
                          Promote failed: {promoteResult.message}
                        </div>
                      )}

                      {promoteBlockedReason && !promoteAlreadyDone && (
                        <div className="text-[11px] text-amber-200/90">{promoteBlockedReason}</div>
                      )}

                      <div className="flex flex-wrap items-center gap-2">
                        <button
                          type="button"
                          className={`btn text-xs ${promoteAlreadyDone ? 'btn-secondary opacity-80' : 'btn-primary'}`}
                          disabled={!canClickPromote}
                          onClick={() => handlePromoteSelection(kgTargetEnv)}
                        >
                          {promoteBusy || kgRunBusy
                            ? `Promoting to ${kgTargetEnv}…`
                            : promoteAlreadyDone
                              ? `✓ Promoted to ${kgTargetEnv}`
                              : `Promote selection → ${kgTargetEnv}`}
                        </button>
                        {promoteAlreadyDone && (
                          <button
                            type="button"
                            className="btn btn-ghost text-[11px]"
                            disabled={promoteBusy || kgRunBusy}
                            onClick={() => setPromoteResult(null)}
                            title="Clear success state to re-run the same promote"
                          >
                            Promote again
                          </button>
                        )}
                      </div>

                      {kgTargetEnv === 'production' && (
                        <div className="text-[10px] text-white/40 flex flex-wrap gap-2">
                          <span className={smokePassed ? 'text-emerald-400' : 'text-rose-400'}>
                            smoke={String(smokePassed)}
                          </span>
                          <span className={humanReviewed ? 'text-emerald-400' : 'text-rose-400'}>
                            approved={String(humanReviewed)}
                          </span>
                          <span className={productionGatesOk ? 'text-emerald-400' : 'text-amber-300'}>
                            {productionGatesOk ? 'production gates OK' : 'production gates incomplete'}
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                  );
                })()}

                {(stepDone[8] || onboardingComplete || (Number(diffSummary.new_count || 0) === 0 && Number(diffSummary.updated_count || 0) === 0 && readyForCustomerTest)) && (
                  <div className="card p-4 border border-emerald-500/40 bg-emerald-500/5">
                    <div className="font-semibold text-emerald-300">
                      {Number(diffSummary.new_count || 0) === 0 && Number(diffSummary.updated_count || 0) === 0
                        ? 'Fleet fully in sync — ready for next plan'
                        : 'Onboarding complete for selection'}
                    </div>
                    <p className="text-xs text-white/55 mt-1">
                      {Number(diffSummary.new_count || 0) === 0 && Number(diffSummary.updated_count || 0) === 0 ? (
                        <>
                          All catalog products match production Neo4j. This batch is done.
                          Reset the wizard for a clean next cycle (new sources → Fetch → Select…),
                          or open Diagnosis Chat to test what you just promoted.
                        </>
                      ) : (
                        <>
                          Promote finished for <span className="font-mono text-cyan-300">{selIds.join(', ')}</span>.
                          Step action buttons stay disabled so you don’t re-run by accident.
                          Start the next batch when fleet still has NEW/UPDATE work, or open Diagnosis Chat to test.
                        </>
                      )}
                    </p>
                    <div className="flex flex-wrap gap-2 mt-2">
                      <button type="button" className="btn btn-primary text-xs" onClick={() => { setRole('customer'); setActiveView('chat'); qc.invalidateQueries({ queryKey: ['crm-assets', selectedCustomerId] }); }}>
                        Open Diagnosis Chat
                      </button>
                      <button
                        type="button"
                        className="btn btn-secondary text-xs"
                        onClick={() =>
                          resetWizardForNextCycle({
                            reason: 'Operator started next product batch — wizard reset.',
                          })
                        }
                      >
                        {Number(diffSummary.new_count || 0) === 0 && Number(diffSummary.updated_count || 0) === 0
                          ? 'Reset wizard for next plan'
                          : 'Start next product batch'}
                      </button>
                    </div>
                  </div>
                )}

                <div className="text-[11px] text-white/35">
                  TBox is shared domain schema; selection filters ABox materialize/promote. API rejects empty selection for bootstrap/promote.
                </div>

                {/* ===== AUDIT / HISTORY (durable) ===== */}
                <div className="card p-4 border border-white/10 space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <button
                      type="button"
                      className="flex items-center gap-2 text-left"
                      onClick={() => setShowAuditPanel((v) => !v)}
                    >
                      <span className="font-semibold text-sm">Audit & history</span>
                      <span className="text-[10px] uppercase tracking-widest text-white/40">
                        durable · survives restart
                      </span>
                      {showAuditPanel ? (
                        <ChevronDown className="w-4 h-4 text-white/40" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-white/40" />
                      )}
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary text-[11px] py-0.5"
                      disabled={auditBusy}
                      onClick={() => refreshAuditHistory()}
                    >
                      {auditBusy ? 'Loading…' : 'Refresh audit'}
                    </button>
                  </div>
                  {showAuditPanel && (
                    <div className="space-y-3 border-t border-white/10 pt-3">
                      <p className="text-[11px] text-white/45 leading-relaxed">
                        Session journey is in-memory. Durable trail is append-only under{' '}
                        <span className="font-mono text-cyan-300/80">data/lineage/</span>
                        : <span className="font-mono">admin_audit.jsonl</span>,{' '}
                        <span className="font-mono">etl_batches.jsonl</span>,{' '}
                        <span className="font-mono">pipeline_runs/*</span>.
                      </p>
                      {auditHistory?.counts && (
                        <div className="grid grid-cols-3 gap-2 text-[11px]">
                          <div className="glass rounded-lg p-2">
                            <div className="text-white/40">Admin events</div>
                            <div className="text-lg font-semibold">{auditHistory.counts.admin_events ?? 0}</div>
                          </div>
                          <div className="glass rounded-lg p-2">
                            <div className="text-white/40">Pipeline runs</div>
                            <div className="text-lg font-semibold">{auditHistory.counts.pipeline_runs ?? 0}</div>
                          </div>
                          <div className="glass rounded-lg p-2">
                            <div className="text-white/40">ETL batches</div>
                            <div className="text-lg font-semibold">{auditHistory.counts.etl_batches ?? 0}</div>
                          </div>
                        </div>
                      )}
                      {auditHistory?.review_state && (
                        <div className="text-[11px] text-white/50 flex flex-wrap gap-2">
                          <span className={`badge text-[10px] ${auditHistory.review_state.last_smoke_ok ? 'badge-ok' : 'badge-warn'}`}>
                            smoke={String(!!auditHistory.review_state.last_smoke_ok)}
                          </span>
                          <span className={`badge text-[10px] ${auditHistory.review_state.materialize_done ? 'badge-ok' : 'badge-warn'}`}>
                            materialize={String(!!auditHistory.review_state.materialize_done)}
                          </span>
                          <span className={`badge text-[10px] ${auditHistory.review_state.ready_for_customer_test ? 'badge-ok' : 'badge-warn'}`}>
                            ready_for_test={String(!!auditHistory.review_state.ready_for_customer_test)}
                          </span>
                          {(auditHistory.review_state.locked_selection_ids || []).length > 0 && (
                            <span className="font-mono text-cyan-300/80">
                              scope: {(auditHistory.review_state.locked_selection_ids as string[]).join(', ')}
                            </span>
                          )}
                        </div>
                      )}
                      <div>
                        <div className="text-[10px] uppercase tracking-widest text-white/40 mb-1.5">
                          Session journey (this API process)
                        </div>
                        <div className="max-h-40 overflow-y-auto space-y-1 text-[11px] font-mono">
                          {(adminJourney.length ? [...adminJourney].reverse() : []).slice(0, 20).map((j: any, i: number) => (
                            <div key={`j-${i}-${j.ts || i}`} className="border-b border-white/5 py-1 text-white/65">
                              <span className="text-white/30">{(j.ts || '').slice(0, 19)}</span>{' '}
                              <span className="text-violet-300/90">{j.step}</span> · {j.action}
                              <div className="text-white/45 truncate">{j.summary}</div>
                            </div>
                          ))}
                          {!adminJourney.length && (
                            <div className="text-white/35">No session journey yet — run a step or refresh audit.</div>
                          )}
                        </div>
                      </div>
                      <div>
                        <div className="text-[10px] uppercase tracking-widest text-white/40 mb-1.5">
                          Durable admin events
                        </div>
                        <div className="max-h-48 overflow-y-auto space-y-1 text-[11px] font-mono">
                          {(auditHistory?.admin_events || []).slice(0, 25).map((e: any) => (
                            <div key={e.event_id || e.ts} className="border-b border-white/5 py-1 text-white/65">
                              <span className="text-white/30">{(e.ts || '').slice(0, 19)}</span>{' '}
                              <span className={e.status === 'ok' ? 'text-emerald-400' : 'text-amber-300'}>{e.status}</span>{' '}
                              <span className="text-violet-300/90">{e.step}</span> · {e.action}
                              <div className="text-white/45 truncate">{e.summary}</div>
                              {e.changes?.selected_product_ids && (
                                <div className="text-cyan-300/70 truncate">
                                  products: {(e.changes.selected_product_ids as string[]).slice(0, 8).join(', ')}
                                </div>
                              )}
                            </div>
                          ))}
                          {!(auditHistory?.admin_events || []).length && (
                            <div className="text-white/35">
                              No durable events yet. After API restart, every Admin journey step is written here.
                            </div>
                          )}
                        </div>
                      </div>
                      <div>
                        <div className="text-[10px] uppercase tracking-widest text-white/40 mb-1.5">
                          Recent pipeline runs
                        </div>
                        <div className="max-h-40 overflow-y-auto space-y-1 text-[11px] font-mono">
                          {(auditHistory?.pipeline_runs || []).slice(0, 12).map((r: any) => (
                            <div key={r.run_id || `${r.pipeline_id}-${r.finished_at}`} className="flex flex-wrap gap-2 border-b border-white/5 py-1 text-white/60">
                              <span className="text-white/30 w-36 shrink-0">{(r.finished_at || r.started_at || '').slice(0, 19)}</span>
                              <span>{r.pipeline_id}</span>
                              <span className={r.status === 'success' ? 'text-emerald-400' : 'text-amber-300'}>{r.status}</span>
                              {r.target_env && <span className="text-white/35">{r.target_env}</span>}
                            </div>
                          ))}
                          {!(auditHistory?.pipeline_runs || []).length && (
                            <div className="text-white/35">No pipeline runs loaded — click Refresh audit.</div>
                          )}
                        </div>
                      </div>
                      {auditHistory?.paths && (
                        <div className="text-[10px] text-white/30 font-mono break-all">
                          {Object.entries(auditHistory.paths as Record<string, string>).map(([k, v]) => (
                            <div key={k}>{k}: {v}</div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
              );
            })()}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
