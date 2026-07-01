"use client";

import React, { useState, useEffect, useMemo } from 'react';
import {
  MessageCircle, Users, GitBranch, Activity, FileText, Send, RefreshCw,
  ChevronRight, Shield, Zap, AlertTriangle
} from 'lucide-react';
import { AnimatePresence } from 'framer-motion';
import { api } from '../lib/api';
import type { DiagnoseResponse } from '../lib/types';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ReactFlow, Background, Controls, MiniMap, Node, Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';
import { toast } from 'sonner';

// 2026 Modern Enterprise Diagnostics UI — Glass + AI-Native + Data-First

type View = 'chat' | 'cases' | 'explorer' | 'ops' | 'admin';
type Role = 'customer' | 'agent' | 'analyst';

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
    const onPath = hNodes.has(n.id);
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
      },
    };
  });

  const edges = baseEdges.map(e => {
    if (!hasH) return e;
    const onPath = hEdges.has(e.id);
    return {
      ...e,
      animated: onPath,
      style: onPath
        ? { stroke: '#10b981', strokeWidth: 3, filter: 'drop-shadow(0 0 5px rgba(16,185,129,0.8))' }
        : { stroke: 'rgba(100,116,139,0.15)', strokeWidth: 1 },
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

export default function WarrantyGraphModern() {
  const [activeView, setActiveView] = useState<View>('chat');
  const [role, setRole] = useState<Role>('customer');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hello. Describe the issue your appliance is having. I'll run a precise graph-backed diagnosis with full evidence and safety notes."
    }
  ]);
  const [input, setInput] = useState('');
  const [selectedAsset, setSelectedAsset] = useState({ customer_id: 'CUST-10042', asset_id: 'AST-WM-4421' });
  const [selectedProduct, setSelectedProduct] = useState('wm-001');
  const [currentDiagnosis, setCurrentDiagnosis] = useState<any>(null);
  const [isListening, setIsListening] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);

  // Admin state
  const [adminStatus, setAdminStatus] = useState<any>(null);
  const [onboardForm, setOnboardForm] = useState({ product_id: 'new-wm-2026', name: 'New Front-Load Washer 2026', family: 'washer' });

  const qc = useQueryClient();

  // Live data with loading/error
  const { data: health, isLoading: healthLoading } = useQuery({ queryKey: ['health'], queryFn: api.health, refetchInterval: 15000 });
  const { data: claimsData, isLoading: claimsLoading, error: claimsError } = useQuery({ queryKey: ['claims'], queryFn: () => api.listClaims(20) });
  const { data: batchesData, isLoading: batchesLoading } = useQuery({ queryKey: ['batches'], queryFn: () => api.listBatches(8) });
  const { data: statusData } = useQuery({ queryKey: ['status'], queryFn: api.integrationsStatus });
  const { data: ontologyData } = useQuery({ queryKey: ['ontology'], queryFn: api.getOntology });
  const { data: productsData } = useQuery({ queryKey: ['products'], queryFn: api.listProducts });

  const productsList = (productsData?.products || [
    { product_id: 'wm-001', name: 'Washer wm-001' },
    { product_id: 'dw-001', name: 'Dishwasher dw-001' },
    { product_id: 'mw-001', name: 'Microwave mw-001' }
  ]) as Array<{product_id: string, name: string}>;

  // Send diagnosis
  const diagnoseMutation = useMutation({
    mutationFn: (body: any) => api.diagnose(body),
    onSuccess: (res: any) => {
      const diag = res.diagnosis;
      setCurrentDiagnosis(diag);
      setLastDiagnosis({ ...res, product_id: diag?.product_id || selectedProduct });  // capture for path highlighting

      const assistantMsg: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: res.response,
        diagnosis: diag,
        full: res,
      };
      setMessages(prev => [...prev, assistantMsg]);

      if (res.escalated) {
        toast.warning('Case escalated for human review', { description: res.case_id });
      } else {
        toast.success('Diagnosis complete', { description: `${diag?.ranked_failure_modes?.[0]?.name || 'Ready'}` });
      }
    },
    onError: (e: any) => toast.error('Diagnosis failed', { description: e.message }),
  });

  const handleSend = () => {
    if (!input.trim()) return;

    const userMsg: ChatMessage = {
      id: 'u' + Date.now(),
      role: 'user',
      content: input.trim(),
    };
    setMessages(prev => [...prev, userMsg]);

    diagnoseMutation.mutate({
      message: input.trim(),
      ...selectedAsset,
      product_id: selectedProduct,
    });

    setInput('');
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
      // Auto send after voice
      setTimeout(() => {
        const userMsg: ChatMessage = { id: 'u' + Date.now(), role: 'user', content: transcript };
        setMessages(prev => [...prev, userMsg]);
        diagnoseMutation.mutate({ message: transcript, ...selectedAsset, product_id: selectedProduct });
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
    if (cmd === 'explorer') { setActiveView('explorer'); loadExplorer(); }
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

  const refreshAdminStatus = async () => {
    try {
      const res = await fetch(`${ADMIN_BASE}/admin/pipeline/status`, { headers: adminHeaders() }).then(r => r.json());
      setAdminStatus(res);
    } catch (e) {
      toast.error("Failed to fetch admin status");
    }
  };

  const fetchReview = async () => {
    try {
      const res = await fetch(`${ADMIN_BASE}/admin/pipeline/review`, { headers: adminHeaders() }).then(r => r.json());
      setAdminStatus((prev: any) => ({ ...prev, ...res }));
    } catch (e) {
      toast.error("Failed to load review");
    }
  };

  const handleOnboardProduct = async () => {
    try {
      const res = await fetch(`${ADMIN_BASE}/admin/onboard-product`, {
        method: 'POST', headers: adminHeaders({ 'Content-Type': 'application/json' }), body: JSON.stringify(onboardForm)
      }).then(r => r.json());
      toast.success(res.message || "Product staged");
      refreshAdminStatus();
    } catch (e: any) { toast.error(e.message); }
  };

  const handleDryRunETL = async () => {
    await fetch(`${ADMIN_BASE}/admin/pipeline/dry-run-etl`, { method: 'POST', headers: adminHeaders() }).then(r => r.json());
    toast.info("Dry-run complete — review in Admin");
    refreshAdminStatus();
  };

  const handleValidate = async () => {
    const res = await fetch(`${ADMIN_BASE}/admin/pipeline/validate`, { method: 'POST', headers: adminHeaders() }).then(r => r.json());
    toast[res.ok ? "success" : "error"](res.message);
    refreshAdminStatus();
  };

  const handleReview = async () => {
    await fetchReview();
    toast.info("Review loaded. Approve if changes look good.");
  };

  const handleApprove = async () => {
    await fetch(`${ADMIN_BASE}/admin/pipeline/approve-review`, { method: 'POST', headers: adminHeaders() });
    refreshAdminStatus();
    toast.success("Review approved — promotion unlocked");
  };

  const handlePromote = async () => {
    try {
      const res = await fetch(`${ADMIN_BASE}/admin/pipeline/promote`, { method: 'POST', headers: adminHeaders() }).then(r => r.json());
      if (res.error) toast.error(res.error);
      else toast.success(res.message);
      refreshAdminStatus();
    } catch (e: any) { toast.error(e.message); }
  };

  // Auto-refresh admin status when entering admin view
  useEffect(() => {
    if (activeView === 'admin') refreshAdminStatus();
  }, [activeView]);

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

    const isHorizontal = direction === 'LR';
    dagreGraph.setGraph({ rankdir: direction, nodesep: 120, ranksep: 140, edgesep: 50 });

    nodes.forEach((node) => {
      const nodeWithDimensions = node as any;
      dagreGraph.setNode(node.id, {
        width: nodeWithDimensions.width || 180,
        height: nodeWithDimensions.height || 50
      });
    });

    edges.forEach((edge) => {
      dagreGraph.setEdge(edge.source, edge.target);
    });

    dagre.layout(dagreGraph);

    const layoutedNodes = nodes.map((node) => {
      const nodeWithPosition = dagreGraph.node(node.id);
      return {
        ...node,
        position: {
          x: nodeWithPosition.x - (nodeWithPosition.width / 2),
          y: nodeWithPosition.y - (nodeWithPosition.height / 2),
        },
      };
    });

    return { nodes: layoutedNodes, edges };
  };

  const buildFlow = (
    g?: any,
    currentTheme: 'dark' | 'light' = 'dark',
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
      Resolution:          '#64748b',   // alias for HistoricalResolution
      ErrorCode:           '#f43f5e',
      default:             '#64748b',
    };

    const isDark = currentTheme === 'dark';
    const baseTextColor     = isDark ? '#f1f1f3' : '#111113';
    // Dark: rich colored fill. Light: light tint + solid border ("outlined" style).
    const baseNodeBg        = isDark ? 0.82 : 0.18;
    const baseNodeBorder    = isDark ? 0.8 : 1;

    const initialNodes: Node[] = (g.nodes || []).map((n: any) => {
      let label = n.title || n.name || n.description || n.label || n.id || 'Node';
      if (typeof label === 'string') label = label.split('\n')[0].trim();
      if (label.length > 30) label = label.substring(0, 27) + '...';

      const nodeType = n.type || n.label || 'default';
      const color    = typeColors[nodeType] || typeColors.default;

      // Parse hex to RGB for rgba() usage
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
          typeColor: color,   // read by applyHighlight for path-node glow
          raw: n,
        },
        position: { x: 0, y: 0 },
        style: {
          background: `rgba(${rgb},${baseNodeBg})`,
          border: `${isDark ? '1.5px' : '2px'} solid rgba(${rgb},${baseNodeBorder})`,
          color: baseTextColor,
          borderRadius: '8px',
          padding: '7px 10px',
          fontSize: '11px',
          fontWeight: 500,
          width: 180,
          cursor: 'pointer',
          // transition handled by CSS (.react-flow__node)
        },
      };
    });

    const edgeBg = isDark ? 'rgba(255,255,255,0.85)' : 'rgba(0,0,0,0.75)';
    const edgeFg = isDark ? '#475569' : '#64748b';
    const initialEdges: Edge[] = (g.edges || []).map((e: any, i: number) => ({
      id: e.id || `e${i}`,
      source: e.source,
      target: e.target,
      label: e.label || e.type || '',
      data: { type: e.type || e.label },
      style: { stroke: isDark ? 'rgba(100,116,139,0.55)' : 'rgba(100,116,139,0.70)', strokeWidth: 1.5 },
      animated: false,
      labelBgStyle: { fill: edgeBg, rx: 3, ry: 3, fillOpacity: 0.9 },
      labelStyle: { fill: edgeFg, fontSize: 9, fontWeight: 400 },
    }));

    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(initialNodes, initialEdges, 'TB');
    return { nodes: layoutedNodes, edges: layoutedEdges };
  };

  const [explorerData, setExplorerData] = useState<any>(null);
  const [isLoadingExplorer, setIsLoadingExplorer] = useState(false);
  const [rfInstance, setRfInstance] = useState<any>(null);
  const [lastDiagnosis, setLastDiagnosis] = useState<any>(null);
  const [highlightPath, setHighlightPath] = useState<{ nodes: string[]; edges: string[] } | null>(null);
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  // Selected node for investigation panel
  const [selectedNode, setSelectedNode] = useState<any>(null);

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

  const loadExplorer = async (pid = selectedProduct, highlight = false) => {
    if (highlight) {
      // ── HIGHLIGHT OVERLAY ─────────────────────────────────────────────────
      // The full product graph stays in explorerData. We only compute which
      // node / edge IDs belong to the diagnosis path and store them as an
      // overlay. This avoids the race condition where clearing explorerData
      // triggers the auto-load useEffect and overwrites the subgraph.
      if (!lastDiagnosis?.diagnosis) return;
      setIsLoadingExplorer(true);
      try {
        const d = lastDiagnosis.diagnosis;
        const symptomIds = (d.matched_symptoms || []).map((s: any) => s.symptom_id);
        const fmId = d.ranked_failure_modes?.[0]?.failure_mode_id;

        // Ensure the full graph is loaded before we paint the overlay.
        let graphData = explorerData;
        if (!graphData) {
          graphData = await api.getProductGraph(pid);
          setExplorerData(graphData);
        }

        // Fetch path IDs. The subgraph API returns prefixed IDs ("Symptom:wm-s03")
        // that match the full product graph node IDs directly.
        const pathData = await api.getDiagnosisSubgraph(pid, symptomIds, fmId);
        const pathNodes = (pathData.nodes || []).map((n: any) => n.id as string);
        const pathEdges = (pathData.edges || []).map(
          (e: any) => (e.id as string) || `${e.source}|${e.target}`
        );

        if (pathNodes.length > 0) {
          setHighlightPath({ nodes: pathNodes, edges: pathEdges });
          setTimeout(() => rfInstance?.fitView({ padding: 0.15, duration: 250 }), 150);
        }
      } catch {
        // Silently fail — existing graph stays visible
      } finally {
        setIsLoadingExplorer(false);
      }
      return;
    }

    // ── FULL GRAPH LOAD ────────────────────────────────────────────────────
    // Clears both data and highlight, loads fresh product subgraph.
    setIsLoadingExplorer(true);
    setHighlightPath(null);
    setExplorerData(null);
    try {
      const data = await api.getProductGraph(pid);
      if (data?.nodes?.length) {
        setExplorerData(data);
        setTimeout(() => rfInstance?.fitView({ padding: 0.15, duration: 250 }), 150);
        return;
      }
      // Fallback: full ontology
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

  // Auto load real product subgraph when entering explorer
  useEffect(() => {
    if (activeView === 'explorer' && !explorerData) {
      loadExplorer(selectedProduct);
    }
  }, [activeView, selectedProduct]);

  const onNodeClick = (_event: any, node: any) => {
    setSelectedNode(node);
  };

  // Keyboard pan: arrow keys pan the viewport when in explorer view
  useEffect(() => {
    if (activeView !== 'explorer') return;
    const handleKey = (e: KeyboardEvent) => {
      if (!rfInstance || (e.target as HTMLElement).tagName === 'INPUT') return;
      const step = e.shiftKey ? 200 : 80;
      const vp = rfInstance.getViewport();
      const moves: Record<string, { x: number; y: number }> = {
        ArrowLeft:  { x: vp.x + step, y: vp.y },
        ArrowRight: { x: vp.x - step, y: vp.y },
        ArrowUp:    { x: vp.x, y: vp.y + step },
        ArrowDown:  { x: vp.x, y: vp.y - step },
      };
      if (moves[e.key]) {
        e.preventDefault();
        rfInstance.setViewport({ ...moves[e.key], zoom: vp.zoom }, { duration: 120 });
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [activeView, rfInstance]);

  // Stable layout — only recomputes when graph data or theme changes.
  // Highlight toggling does NOT trigger a layout recalculation.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const baseFlow = useMemo(() => buildFlow(explorerData || ontologyData, theme), [explorerData, ontologyData, theme]);

  // Highlight overlay — pure className + glow applied on top of the stable layout.
  const flow = useMemo(() => applyHighlight(baseFlow.nodes, baseFlow.edges, highlightPath), [baseFlow, highlightPath]);

  // Refit only when the underlying layout changes (not on highlight toggle).
  useEffect(() => {
    if (rfInstance && baseFlow.nodes.length > 0) {
      setTimeout(() => {
        try { rfInstance.fitView({ padding: 0.15, duration: 300 }); } catch {}
      }, 50);
    }
  }, [baseFlow.nodes.length, rfInstance]);

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
        </div>

        <div className="mt-auto p-4 text-[10px] text-white/40 dark:text-white/40 border-t border-white/10 dark:border-white/10">
          GraphRAG + FMEA + Provenance<br />
          Neo4j · LangGraph · FastAPI
        </div>
      </div>

      {/* Main Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Glass Topbar */}
        <div className="h-14 border-b border-white/10 glass flex items-center justify-between px-5 text-sm z-50">
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

        {/* View Content */}
        <div className="flex-1 overflow-auto p-6">
          <AnimatePresence mode="wait">
            {/* ==================== CHAT — AI-NATIVE CONVERSATIONAL ==================== */}
            {activeView === 'chat' && (
              <div className="max-w-[1200px] mx-auto space-y-6">
                <div>
                  <div className="text-4xl font-semibold tracking-tighter">Diagnosis Chat</div>
                  <p className="text-white/60 mt-1">Describe the problem. Get structured, evidence-backed diagnosis with full provenance.</p>
                </div>

                {/* Context bar */}
                <div className="glass flex items-center gap-3 px-4 py-3 rounded-2xl text-sm">
                  <div>Context:</div>
                  <input className="input w-44" placeholder="Customer ID" value={selectedAsset.customer_id} onChange={e => setSelectedAsset(s => ({...s, customer_id: e.target.value}))} />
                  <input className="input w-44" placeholder="Asset ID" value={selectedAsset.asset_id} onChange={e => setSelectedAsset(s => ({...s, asset_id: e.target.value}))} />
                  <select className="input w-40" title="Select appliance" value={selectedProduct} onChange={e => setSelectedProduct(e.target.value)}>
                    {productsList.map((p: any) => (
                      <option key={p.product_id} value={p.product_id}>{p.name}</option>
                    ))}
                  </select>
                  <div className="ml-auto text-xs text-white/50">Asset binding enables CRM + warranty + parts prediction</div>
                </div>

                {/* Messages + Rich Diagnosis */}
                <div className="space-y-6">
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

                                {/* Provenance Trail */}
                                {msg.full?.provenance_trail && msg.full.provenance_trail.length > 0 && (
                                  <div>
                                    <div className="text-xs uppercase tracking-widest mb-1 text-white/50">PROVENANCE TRAIL</div>
                                    <div className="space-y-1 text-[11px]">
                                      {msg.full.provenance_trail.slice(0,4).map((p:any, i:number) => (
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
                                    onClick={() => {
                                      setActiveView('explorer');
                                      const hasPrecisePath = !!(msg.diagnosis?.traversed_fm_id && msg.diagnosis?.traversed_symptom_ids?.length);
                                      loadExplorer(msg.diagnosis?.product_id || selectedProduct, hasPrecisePath);
                                    }}
                                    className="btn btn-secondary text-xs"
                                    title="Navigate to Knowledge Explorer with the exact diagnosis path highlighted"
                                  >
                                    {msg.diagnosis?.traversed_fm_id ? '🔍 Explore Exact Path' : 'Explore Graph'}
                                  </button>
                                  <button
                                    onClick={() => {
                                      if (!msg.full) return;
                                      api.submitClaim({ message: messages.find(m => m.role==='user')?.content || '', asset_id: selectedAsset.asset_id }).then(() => {
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
                </div>

                {/* Input area — modern glass + voice + examples */}
                <div className="sticky bottom-6 pt-4">
                  <div className="glass rounded-3xl p-2 flex gap-2 items-end">
                    <div className="flex-1 px-1">
                      <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                        placeholder="Describe the problem (e.g. washing machine won't spin...)"
                        className="input resize-y min-h-[52px] bg-transparent border-0 focus:ring-0"
                        rows={2}
                      />
                      <div className="flex gap-1.5 mt-1 px-1 flex-wrap items-center">
                        {examplePrompts.map((p, i) => (
                          <button key={i} onClick={() => { setInput(p); }} className="text-[10px] px-2.5 py-px rounded-full glass border border-white/10 hover:border-white/30">{p.slice(0,42)}…</button>
                        ))}
                        <button onClick={toggleVoice} className={`text-[10px] px-2.5 py-px rounded-full border transition ${isListening ? 'bg-rose-500/20 border-rose-500/40' : 'glass border-white/10 hover:border-white/30'}`}>
                          🎤 {isListening ? 'Listening...' : 'Voice'}
                        </button>
                        <span className="ml-auto text-[10px] text-white/30">⌘K for commands</span>
                      </div>
                    </div>
                    <button onClick={handleSend} disabled={!input.trim() || diagnoseMutation.isPending} className="btn btn-primary h-12 w-12 rounded-2xl">
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

            {/* ==================== KNOWLEDGE EXPLORER - Real Neo4j Data ==================== */}
            {activeView === 'explorer' && (
              <div className="max-w-[1400px] mx-auto">
                <div className="flex items-end justify-between mb-5">
                  <div>
                    <div className="text-3xl font-semibold tracking-tight">Knowledge Graph Explorer</div>
                    <div className="text-[var(--text-1)] mt-1 flex items-center gap-2 text-sm">
                      Live from Neo4j · Product → Symptoms → Failure Modes → Parts
                      <span className={`text-[10px] px-1.5 py-px rounded font-medium ${
                        health?.neo4j ? 'badge-ok' : 'badge-error'
                      }`}>
                        {health?.neo4j ? 'CONNECTED' : 'NOT CONNECTED'}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-wrap justify-end">
                    <select
                      title="Select product to explore"
                      value={selectedProduct}
                      onChange={e => { setSelectedProduct(e.target.value); loadExplorer(e.target.value); setSelectedNode(null); }}
                      className="input w-48 py-1.5 text-sm"
                    >
                      {productsList.map((p: any) => (
                        <option key={p.product_id} value={p.product_id}>{p.name}</option>
                      ))}
                    </select>
                    <button onClick={() => { loadExplorer(); setSelectedNode(null); }} disabled={isLoadingExplorer} className="btn btn-primary">
                      {isLoadingExplorer ? 'Loading...' : 'Load Subgraph'}
                    </button>
                    {lastDiagnosis && lastDiagnosis.diagnosis?.product_id === selectedProduct && !highlightPath && (
                      <button
                        onClick={() => { loadExplorer(selectedProduct, true); setSelectedNode(null); }}
                        className="btn btn-secondary text-sm"
                        title="Highlight the exact symptoms + failure mode path from your last diagnosis"
                      >
                        Highlight Diagnosis Path
                      </button>
                    )}
                    {highlightPath && (
                      <button onClick={() => { setHighlightPath(null); loadExplorer(selectedProduct); setSelectedNode(null); }} className="btn btn-ghost text-xs">Clear Highlight</button>
                    )}
                  </div>
                </div>

                {/* Navigation hint */}
                <div className="mb-2 flex items-center gap-3 text-[11px] text-[var(--text-2)]">
                  <span>🖱️ <strong>Drag</strong> to pan &nbsp;·&nbsp; 🖱️ <strong>Scroll</strong> to zoom &nbsp;·&nbsp; ⌨️ <strong>Arrow keys</strong> to navigate &nbsp;·&nbsp; 🖱️ <strong>Click node</strong> to inspect</span>
                  {highlightPath && <span className="text-emerald-400 font-medium">● Diagnosis path highlighted — dimmed nodes not on path</span>}
                </div>

                {/* Main explorer: graph + inspection panel side-by-side */}
                <div className={`flex gap-4 ${selectedNode ? 'items-start' : ''}`}>
                  {/* Graph canvas */}
                  <div className={`graph-container relative flex-1 ${selectedNode ? 'h-[560px]' : 'h-[580px]'}`}>
                    <ReactFlow
                      key={explorerData ? 'loaded-' + (explorerData.node_count || flow.nodes.length) : 'empty'}
                      nodes={flow.nodes}
                      edges={flow.edges}
                      fitView
                      panOnDrag
                      panOnScroll={false}
                      zoomOnScroll
                      zoomOnPinch
                      selectNodesOnDrag={false}
                      nodesDraggable={false}
                      onNodeClick={onNodeClick}
                      onPaneClick={() => setSelectedNode(null)}
                      onInit={setRfInstance}
                      proOptions={{ hideAttribution: true }}
                      style={{ width: '100%', height: '100%', cursor: 'grab' }}
                    >
                      <Background
                        gap={24}
                        color={theme === 'dark' ? '#1c2433' : '#d1d5db'}
                        size={1}
                      />
                      <Controls showInteractive={false} />
                      <MiniMap
                        nodeColor={(n) => {
                          if ((n.className as string)?.includes('node-on-path')) return '#10b981';
                          return (n.data as any)?.typeColor ?? (theme === 'dark' ? '#334155' : '#94a3b8');
                        }}
                        style={{
                          background: theme === 'dark' ? '#0a0a12' : '#f1f5f9',
                          border: `1px solid ${theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.12)'}`,
                          borderRadius: '8px',
                        }}
                        maskColor={theme === 'dark' ? 'rgba(0,0,0,0.6)' : 'rgba(255,255,255,0.6)'}
                      />
                    </ReactFlow>

                    {flow.nodes.length === 0 && !isLoadingExplorer && (
                      <div className="graph-empty-overlay">
                        <GitBranch className="w-10 h-10 mb-3 opacity-30" />
                        <p className="text-sm mb-1">No graph data loaded.</p>
                        <p className="text-xs mb-4">Click <strong>Load Subgraph</strong> to fetch live data from Neo4j.</p>
                        <button onClick={() => loadExplorer(selectedProduct)} className="btn btn-secondary">Load {selectedProduct}</button>
                      </div>
                    )}
                    {isLoadingExplorer && (
                      <div className="graph-loading-overlay">
                        <div className="text-sm">Fetching from Neo4j…</div>
                      </div>
                    )}
                  </div>

                  {/* Node inspection panel */}
                  {selectedNode && (() => {
                    const raw   = selectedNode.data?.raw || {};
                    const ntype = selectedNode.data?.type || 'Node';
                    const title = selectedNode.data?.fullLabel || selectedNode.data?.label || selectedNode.id;
                    // Read from highlightPath state (not stale node data) for accuracy.
                    const isOnPath = !!(highlightPath?.nodes?.includes(selectedNode.id));
                    // Edges connected to this node
                    const connEdges = flow.edges.filter(
                      (e: any) => e.source === selectedNode.id || e.target === selectedNode.id
                    );
                    const connNodes = new Set(connEdges.flatMap((e: any) => [e.source, e.target]).filter((id: string) => id !== selectedNode.id));
                    const typeColorMap: Record<string,string> = { Product:'#10b981', Symptom:'#3b82f6', FailureMode:'#f59e0b', Part:'#8b5cf6', Component:'#ec4899', DiagnosticStep:'#14b8a6', HistoricalResolution:'#64748b', ErrorCode:'#f43f5e' };
                    const accentColor = typeColorMap[ntype] || '#64748b';

                    return (
                      <div className="w-72 flex-shrink-0 rounded-xl overflow-hidden node-panel" style={{ border: `1px solid ${accentColor}55` }}>
                        {/* Panel header */}
                        <div className="px-4 py-3 flex items-center justify-between" style={{ background: accentColor, color: '#fff' }}>
                          <div>
                            <div className="text-[10px] font-bold uppercase tracking-widest opacity-80">{ntype}</div>
                            <div className="text-sm font-semibold truncate max-w-[190px]" title={title}>{title.split('\n')[0]}</div>
                          </div>
                          <button onClick={() => setSelectedNode(null)} className="opacity-70 hover:opacity-100 text-white text-lg leading-none">×</button>
                        </div>

                        <div className="p-4 space-y-3 text-xs node-panel-body">
                          {/* ID */}
                          <div>
                            <div className="uppercase tracking-widest text-[9px] mb-1 node-panel-label">Node ID</div>
                            <code className="text-[11px] font-mono break-all node-panel-value">{raw.entity_id || selectedNode.id}</code>
                          </div>

                          {/* Path status */}
                          {highlightPath && (
                            <div className={`rounded-md px-2.5 py-1.5 text-[10px] font-medium ${
                              isOnPath
                                ? 'bg-emerald-900/40 text-emerald-300 border border-emerald-700/40'
                                : 'border'
                            }`} style={isOnPath ? {} : { borderColor: 'var(--border-0)', color: 'var(--text-2)' }}>
                              {isOnPath ? '● On active diagnosis path' : '○ Not on diagnosis path'}
                            </div>
                          )}

                          {/* Description lines from title */}
                          {raw.title && raw.title.includes('\n') && (
                            <div>
                              <div className="uppercase tracking-widest text-[9px] mb-1 node-panel-label">Details</div>
                              <div className="space-y-0.5 node-panel-body">
                                {raw.title.split('\n').slice(1).map((line: string, i: number) => (
                                  <div key={i}>{line}</div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Connections */}
                          <div>
                            <div className="uppercase tracking-widest text-[9px] mb-1.5 node-panel-label">Connections ({connEdges.length})</div>
                            <div className="space-y-1 max-h-40 overflow-y-auto">
                              {connEdges.slice(0, 8).map((e: any, i: number) => {
                                const otherId = e.source === selectedNode.id ? e.target : e.source;
                                const direction = e.source === selectedNode.id ? '→' : '←';
                                const relType = (e.data?.type || e.label || '').replace(/_/g,' ');
                                return (
                                  <button
                                    key={i}
                                    type="button"
                                    className="node-panel-edge-row flex items-center gap-1.5 w-full text-left"
                                    onClick={() => {
                                      const targetNode = flow.nodes.find((n: any) => n.id === otherId);
                                      if (targetNode) setSelectedNode(targetNode);
                                    }}
                                    title={`Navigate to ${otherId}`}
                                  >
                                    <span className="font-bold" style={{ color: accentColor }}>{direction}</span>
                                    <span className="font-mono text-[9px] truncate opacity-70 node-panel-muted">{relType}</span>
                                    <span className="truncate node-panel-value">{otherId.split(':').slice(-1)[0]}</span>
                                  </button>
                                );
                              })}
                              {connEdges.length > 8 && <div className="text-[9px] node-panel-muted">+{connEdges.length - 8} more</div>}
                            </div>
                          </div>

                          {/* Highlight path action */}
                          {ntype === 'Product' && !highlightPath && lastDiagnosis && (
                            <button
                              className="btn btn-primary w-full text-xs py-1.5"
                              onClick={() => loadExplorer(selectedProduct, true)}
                            >
                              Highlight Diagnosis Path
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })()}
                </div>

                {/* Legend */}
                <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-[11px] graph-legend">
                  {[
                    ['#10b981','Product'], ['#3b82f6','Symptom'],
                    ['#f59e0b','Failure Mode'], ['#8b5cf6','Part'],
                    ['#14b8a6','Diagnostic Step'], ['#64748b','Resolution'],
                  ].map(([col, lbl]) => (
                    <span key={lbl} className="flex items-center gap-1">
                      <span style={{ color: col }}>●</span> {lbl}
                    </span>
                  ))}
                  <span className="ml-auto">{flow.nodes.length} nodes · {flow.edges.length} edges{highlightPath ? ' · path active' : ''}</span>
                </div>
              </div>
            )}

            {/* ==================== ENTERPRISE OPS ==================== */}
            {activeView === 'ops' && (
              <div className="max-w-5xl mx-auto space-y-6">
                <div>
                  <div className="text-3xl font-semibold tracking-tight">Enterprise Operations</div>
                  <div className="text-white/60">Pipeline health, lineage, and connector status</div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                  <div className="card p-5">
                    <div className="text-xs uppercase tracking-widest mb-2">Connectors</div>
                    <pre className="text-xs bg-black/40 p-3 rounded font-mono overflow-auto max-h-52">{JSON.stringify(statusData || {}, null, 2)}</pre>
                  </div>

                  <div className="card p-5 md:col-span-2">
                    <div className="text-xs uppercase tracking-widest mb-2">Recent Lineage Batches</div>
                    {batchesLoading && <div className="text-sm text-white/50">Loading...</div>}
                    <div className="space-y-1 text-sm">
                      {(batchesData?.batches || []).slice(0, 6).map((b: any, i: number) => (
                        <div key={i} className="flex justify-between border-b border-white/5 py-1 text-xs">
                          <div>{b.batch_id || b.id} — {b.status}</div>
                          <div className="text-white/40">{b.created_at?.slice(0,16) || ''}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="text-xs text-white/40">Use the <b>Admin</b> tab (ETL Dry-run / Promote) to populate data if empty. Or run <span className="font-mono">./run_enterprise_demo.sh</span> from terminal.</div>
              </div>
            )}

            {/* ==================== ADMIN MODULE — Full Enterprise Control ==================== */}
            {activeView === 'admin' && (
              <div className="max-w-6xl mx-auto space-y-8">
                <div>
                  <div className="flex items-center gap-3">
                    <Shield className="w-8 h-8 text-violet-400" />
                    <div className="text-4xl font-semibold tracking-tighter">Admin — Knowledge Base Management</div>
                  </div>
                  <p className="text-white/60 mt-1 max-w-3xl">
                    Staged enterprise pipeline with human gates. Onboard new products, fetch data, validate, review changes, then promote to the live GraphRAG knowledge base.
                    Designed for real enterprise complexity: quality gates, audit, and controlled promotion.
                  </p>
                </div>

                {/* Status */}
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
                  <div className="card p-4">
                    <div className="text-xs text-white/50">REVIEW STATE</div>
                    <div className="mt-2 text-lg font-medium">{adminStatus?.review_state?.reviewed ? 'APPROVED' : 'PENDING REVIEW'}</div>
                    <div className="text-xs text-white/40">Smoke OK: {String(adminStatus?.review_state?.last_smoke_ok)}</div>
                  </div>
                  <div className="card p-4">
                    <div className="text-xs text-white/50">CATALOG PRODUCTS</div>
                    <div className="text-3xl font-semibold mt-1">{adminStatus?.catalog_stats?.products || 0}</div>
                  </div>
                  <div className="card p-4 col-span-2">
                    <div className="text-xs text-white/50 mb-1">LAST LINEAGE</div>
                    <div className="text-xs font-mono">{JSON.stringify((adminStatus?.lineage_last || []).slice(0,1))}</div>
                  </div>
                </div>

                {/* Stage 1: Onboard + Fetch */}
                <div className="card p-6">
                  <div className="font-semibold mb-4 flex items-center gap-2">1. Onboard New Product &amp; Fetch (Dry Run)</div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Onboard Form */}
                    <div>
                      <div className="text-sm mb-2 text-white/60">Onboard New Product</div>
                      <input className="input mb-2" placeholder="product_id (e.g. new-wm-2026)" value={onboardForm.product_id} onChange={e => setOnboardForm({...onboardForm, product_id: e.target.value})} />
                      <input className="input mb-2" placeholder="name" value={onboardForm.name} onChange={e => setOnboardForm({...onboardForm, name: e.target.value})} />
                      <input className="input mb-2" placeholder="family (washer/dishwasher/microwave)" value={onboardForm.family} onChange={e => setOnboardForm({...onboardForm, family: e.target.value})} />
                      <button onClick={handleOnboardProduct} className="btn btn-secondary w-full">Add to Staging Catalog</button>
                    </div>

                    <div>
                      <button onClick={handleDryRunETL} className="btn btn-primary w-full mb-3">Run Dry-Run ETL (Fetch &amp; Preview)</button>
                      <div className="text-xs text-white/50">This fetches from enterprise sources without loading Neo4j. Results appear in Review.</div>
                    </div>
                  </div>
                </div>

                {/* Stage 2 + 3: Validate + Review Gate */}
                <div className="card p-6">
                  <div className="font-semibold mb-4">2. Validate &amp; 3. Human Review Gate</div>

                  <div className="flex gap-3 mb-4">
                    <button onClick={handleValidate} className="btn btn-secondary">Run Smoke Validation</button>
                    <button onClick={handleReview} className="btn btn-secondary">Refresh Review</button>
                    <button onClick={handleApprove} disabled={!adminStatus?.staged_changes && !adminStatus?.smoke_passed} className="btn btn-primary">Approve Changes (Gate)</button>
                  </div>

                  <div className="glass p-4 rounded-xl text-sm">
                    <div>Smoke Passed: <span className={adminStatus?.smoke_passed ? "text-emerald-400" : "text-rose-400"}>{String(adminStatus?.smoke_passed)}</span></div>
                    <div>Human Reviewed: <span className={adminStatus?.reviewed ? "text-emerald-400" : "text-amber-400"}>{String(adminStatus?.reviewed)}</span></div>
                    <div className="mt-2 text-xs text-white/50">You must review the staged changes (source counts, new products) and click Approve before promotion is allowed. This models real enterprise change control.</div>
                  </div>
                </div>

                {/* Stage 4: Promote */}
                <div className="card p-6">
                  <div className="font-semibold mb-3">4. Promote to Live Knowledge Base</div>
                  <button
                    onClick={handlePromote}
                    disabled={!adminStatus?.can_promote}
                    className={`btn w-full ${adminStatus?.can_promote ? 'btn-primary' : 'opacity-50 cursor-not-allowed bg-white/5'}`}
                  >
                    PROMOTE (after review + smoke pass)
                  </button>
                  <div className="text-xs text-white/40 mt-2">This loads the validated catalog into Neo4j. New products become available for diagnosis immediately.</div>
                </div>

                <div className="text-xs text-white/40">All actions are auditable via /admin/pipeline/status and lineage. In production you would add RBAC, signed approvals, and blue/green graph instances.</div>
              </div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
