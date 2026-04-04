<script lang="ts">
  import { startResearch, connectWebSocket, fetchResult, fetchHistory, type HistoryItem } from './lib/api';
  import { STAGES, type StageName, type StageStatus, type PipelineResult, type WSEvent } from './lib/types';
  import QueryInput from './lib/QueryInput.svelte';
  import SettingsPanel from './lib/SettingsPanel.svelte';
  import PipelineProgress from './lib/PipelineProgress.svelte';
  import BiasAnalysis from './lib/BiasAnalysis.svelte';
  import SourceCards from './lib/SourceCards.svelte';
  import FactCheckResults from './lib/FactCheckResults.svelte';
  import ChallengesPanel from './lib/ChallengesPanel.svelte';
  import SynthesisReport from './lib/SynthesisReport.svelte';
  import EvaluationScorecard from './lib/EvaluationScorecard.svelte';
  import MermaidDiagram from './lib/MermaidDiagram.svelte';
  import TokenUsage from './lib/TokenUsage.svelte';
  import QueryHistory from './lib/QueryHistory.svelte';
  import ExportMenu from './lib/ExportMenu.svelte';

  // App state
  type View = 'input' | 'results';

  let view = $state<View>('input');
  let loading = $state(false);
  let errorMsg = $state('');
  let query = $state('');

  // Pipeline tracking
  let stageStatuses = $state<Record<string, StageStatus>>({});
  let stageTokens = $state<Record<string, { input: number; output: number }>>({});
  let stageData = $state<Record<string, Record<string, any>>>({});
  let stageContent = $state<Record<string, string>>({});
  let activeStage = $state<string | null>(null);

  // Final results
  let pipelineResult = $state<PipelineResult | null>(null);
  let mermaidDiagrams = $state<Record<string, string>>({});
  let jobId = $state<string | null>(null);

  // History count for top-bar badge
  let historyCount = $state(0);

  // Settings
  let settingsOpen = $state(false);

  function loadSavedSettings(): { model: string; maxResults: number } {
    try {
      const raw = localStorage.getItem('cleric-settings');
      if (raw) return JSON.parse(raw);
    } catch {}
    return { model: 'claude-sonnet-4-6', maxResults: 5 };
  }

  let currentSettings = $state(loadSavedSettings());

  // Active results tab
  type ResultTab = 'bias' | 'sources' | 'facts' | 'challenges' | 'synthesis' | 'evaluation' | 'diagrams';
  let activeResultTab = $state<ResultTab>('bias');

  let ws: WebSocket | null = null;

  function resetState() {
    stageStatuses = {};
    stageTokens = {};
    stageData = {};
    stageContent = {};
    activeStage = null;
    pipelineResult = null;
    mermaidDiagrams = {};
    jobId = null;
    errorMsg = '';
    activeResultTab = 'bias';
  }

  async function handleSubmit(q: string) {
    query = q;
    loading = true;
    resetState();
    view = 'results';

    // Initialize all stages as pending
    for (const stage of STAGES) {
      stageStatuses[stage.key] = 'pending';
    }

    try {
      const id = await startResearch(q, currentSettings);
      jobId = id;
      ws = connectWebSocket(id, handleEvent, handleClose, handleWsError);
    } catch (e: any) {
      errorMsg = e.message || 'Failed to start research. Is the backend running?';
      loading = false;
    }
  }

  function handleEvent(event: WSEvent) {
    switch (event.type) {
      case 'stage_start':
        stageStatuses[event.stage] = 'running';
        activeStage = event.stage;
        break;

      case 'stage_complete':
        stageStatuses[event.stage] = 'complete';
        stageTokens[event.stage] = event.tokens as { input: number; output: number };
        stageData[event.stage] = event.data;
        stageContent[event.stage] = event.content;

        // Auto-switch to the tab for the completed stage
        const tabMap: Record<string, ResultTab> = {
          bias_detection: 'bias',
          research: 'sources',
          fact_checking: 'facts',
          devils_advocate: 'challenges',
          synthesis: 'synthesis',
          evaluation: 'evaluation',
        };
        if (tabMap[event.stage]) {
          activeResultTab = tabMap[event.stage];
        }
        break;

      case 'pipeline_complete':
        pipelineResult = event.result;
        mermaidDiagrams = event.mermaid_diagrams || {};
        loading = false;
        activeStage = null;
        break;

      case 'error':
        errorMsg = event.message;
        loading = false;
        // Mark current running stage as error
        for (const [key, status] of Object.entries(stageStatuses)) {
          if (status === 'running') {
            stageStatuses[key] = 'error';
          }
        }
        break;
    }
  }

  function handleClose() {
    if (loading) {
      loading = false;
    }
  }

  function handleWsError(_e: Event) {
    if (!pipelineResult && !errorMsg) {
      errorMsg = 'Connection lost. The backend may have stopped.';
      loading = false;
    }
  }

  function goBack() {
    view = 'input';
    loading = false;
    if (ws) {
      ws.close();
      ws = null;
    }
  }

  async function handleHistorySelect(item: HistoryItem) {
    try {
      loading = true;
      resetState();
      const full = await fetchResult(item.id);
      jobId = item.id;
      query = full.query;
      view = 'results';

      // Rehydrate stage data from the stored result
      const result = full.result;
      if (result && result.stages) {
        for (const [key, stage] of Object.entries(result.stages) as [string, any][]) {
          stageStatuses[key] = 'complete';
          stageData[key] = stage.data || {};
          stageContent[key] = stage.content || '';
          stageTokens[key] = stage.tokens || { input: 0, output: 0 };
        }
      }

      mermaidDiagrams = full.mermaid_diagrams || {};
      pipelineResult = result as PipelineResult;
      loading = false;
    } catch {
      errorMsg = 'Failed to load historical result.';
      loading = false;
    }
  }

  async function loadHistoryCount() {
    try {
      const res = await fetchHistory(1, 0);
      historyCount = res.total;
    } catch {
      historyCount = 0;
    }
  }

  // Load history count on init
  loadHistoryCount();

  // Tab definitions for the results view
  const resultTabs: { key: ResultTab; label: string; icon: string; stage?: string }[] = [
    { key: 'bias', label: 'Bias', icon: '\u{1F6E1}\uFE0F', stage: 'bias_detection' },
    { key: 'sources', label: 'Sources', icon: '\u{1F50E}', stage: 'research' },
    { key: 'facts', label: 'Facts', icon: '\u2705', stage: 'fact_checking' },
    { key: 'challenges', label: 'Challenges', icon: '\u{1F608}', stage: 'devils_advocate' },
    { key: 'synthesis', label: 'Synthesis', icon: '\u{1F4DD}', stage: 'synthesis' },
    { key: 'evaluation', label: 'Score', icon: '\u{1F4CA}', stage: 'evaluation' },
    { key: 'diagrams', label: 'Diagrams', icon: '\u{1F4C8}' },
  ];

  function isTabAvailable(tab: typeof resultTabs[0]): boolean {
    if (tab.key === 'diagrams') return Object.keys(mermaidDiagrams).length > 0;
    if (!tab.stage) return false;
    return stageStatuses[tab.stage] === 'complete';
  }
</script>

<div class="app-layout">
  <!-- Top Bar -->
  <header class="top-bar">
    <div class="top-bar-inner">
      <div class="brand" role="button" tabindex="0" onclick={goBack} onkeydown={(e) => e.key === 'Enter' && goBack()}>
        <img src="/cleric-logo.png" alt="C.L.E.R.I.C." class="brand-logo-img" />
        <div class="brand-text">
          <span class="brand-name">C.L.E.R.I.C.</span>
          <span class="brand-subtitle">Cross-Lateral Evidence Review for Informational Clarity</span>
        </div>
      </div>
      <div class="top-bar-right">
        {#if historyCount > 0}
          <span class="history-badge badge badge-info">{historyCount} past</span>
        {/if}
        <button class="settings-btn" onclick={() => settingsOpen = true} aria-label="Open settings">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        </button>
        {#if view === 'results'}
          <button class="back-btn" onclick={goBack} aria-label="Go back to search">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            New Query
          </button>
        {/if}
      </div>
    </div>
  </header>

  <!-- Main Content -->
  <main class="main-content">
    {#if view === 'input'}
      <QueryInput onsubmit={handleSubmit} {loading} />
      <div class="history-section">
        <QueryHistory onselect={handleHistorySelect} />
      </div>
    {:else}
      <div class="results-layout" aria-busy={loading}>
        <!-- Query display -->
        <div class="query-banner">
          <div class="query-banner-top">
            <div>
              <span class="query-label">Researching:</span>
              <h2 class="query-text">{query}</h2>
            </div>
            {#if pipelineResult && jobId}
              <ExportMenu {jobId} />
            {/if}
          </div>
        </div>

        <!-- Pipeline Progress -->
        <div aria-live="polite">
          <PipelineProgress {stageStatuses} {stageTokens} {activeStage} />
        </div>

        <!-- Error -->
        {#if errorMsg}
          <div class="error-banner">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v4M12 16h.01" />
            </svg>
            <p>{errorMsg}</p>
            <button class="retry-btn" onclick={() => handleSubmit(query)}>Retry</button>
          </div>
        {/if}

        <!-- Token Usage (shown when complete) -->
        {#if pipelineResult}
          <TokenUsage
            totalTokens={pipelineResult.total_tokens}
            durationSeconds={pipelineResult.duration_seconds}
            {stageTokens}
          />
        {/if}

        <!-- Results Tabs -->
        {#if Object.values(stageStatuses).some(s => s === 'complete')}
          <div class="results-section">
            <div class="result-tabs" role="tablist">
              {#each resultTabs as tab}
                {@const available = isTabAvailable(tab)}
                <button
                  class="result-tab"
                  class:active={activeResultTab === tab.key}
                  class:disabled={!available}
                  disabled={!available}
                  role="tab"
                  aria-selected={activeResultTab === tab.key}
                  onclick={() => activeResultTab = tab.key}
                >
                  <span class="tab-icon">{tab.icon}</span>
                  <span class="tab-label">{tab.label}</span>
                  {#if tab.stage && stageStatuses[tab.stage] === 'running'}
                    <span class="tab-spinner"></span>
                  {/if}
                </button>
              {/each}
            </div>

            <div class="result-content" role="tabpanel">
              {#if activeResultTab === 'bias' && stageData.bias_detection}
                <BiasAnalysis data={stageData.bias_detection} />
              {:else if activeResultTab === 'sources' && stageData.research}
                <SourceCards data={stageData.research} content={stageContent.research || ''} />
              {:else if activeResultTab === 'facts' && stageData.fact_checking}
                <FactCheckResults data={stageData.fact_checking} />
              {:else if activeResultTab === 'challenges' && stageData.devils_advocate}
                <ChallengesPanel data={stageData.devils_advocate} />
              {:else if activeResultTab === 'synthesis' && stageData.synthesis}
                <SynthesisReport data={stageData.synthesis} content={stageContent.synthesis || ''} />
              {:else if activeResultTab === 'evaluation' && stageData.evaluation}
                <EvaluationScorecard
                  data={stageData.evaluation}
                  overallGrade={pipelineResult?.overall_grade || stageData.evaluation?.overall_grade || '?'}
                />
              {:else if activeResultTab === 'diagrams' && Object.keys(mermaidDiagrams).length > 0}
                <MermaidDiagram diagrams={mermaidDiagrams} />
              {:else}
                <div class="empty-tab">
                  <p>Waiting for data...</p>
                </div>
              {/if}
            </div>
          </div>
        {:else if loading && !errorMsg}
          <div class="loading-state">
            <div class="loading-spinner-lg"></div>
            <p>Initializing pipeline...</p>
          </div>
        {/if}
      </div>
    {/if}
  </main>
</div>

<SettingsPanel
  open={settingsOpen}
  onclose={() => settingsOpen = false}
  onsave={(settings) => currentSettings = settings}
/>

<style>
  .settings-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .settings-btn:hover {
    border-color: var(--accent);
    color: var(--accent);
  }

  .app-layout {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* Top Bar */
  .top-bar {
    position: sticky;
    top: 0;
    z-index: 100;
    background: rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border-primary);
  }

  .top-bar-inner {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1.5rem;
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    user-select: none;
  }

  .brand:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 4px;
    border-radius: 4px;
  }

  .brand-logo-img {
    width: 38px;
    height: 38px;
    border-radius: var(--radius-sm);
    object-fit: contain;
  }

  .brand-text {
    display: flex;
    flex-direction: column;
  }

  .brand-name {
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: 0.04em;
    font-family: var(--font-mono);
  }

  .brand-subtitle {
    font-size: 0.65rem;
    color: var(--text-dim);
    letter-spacing: 0.01em;
  }

  .back-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    font-size: 0.85rem;
    font-family: var(--font-sans);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .back-btn:hover {
    border-color: var(--accent);
    color: var(--accent);
  }

  .top-bar-right {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .history-badge {
    font-size: 0.7rem;
  }

  /* Main Content */
  .main-content {
    flex: 1;
    max-width: 1200px;
    width: 100%;
    margin: 0 auto;
  }

  .history-section {
    max-width: 700px;
    margin: 1.5rem auto 0;
    padding: 0 1.5rem;
  }

  /* Results Layout */
  .results-layout {
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    animation: fadeIn 300ms ease-out;
  }

  .query-banner {
    padding: 1rem 1.25rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    border-left: 4px solid var(--accent);
  }

  .query-banner-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1rem;
  }

  .query-label {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-dim);
    display: block;
    margin-bottom: 4px;
  }

  .query-text {
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }

  /* Error Banner */
  .error-banner {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 1rem 1.25rem;
    background: rgba(239, 68, 68, 0.08);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: var(--radius-md);
    color: #f87171;
    animation: fadeIn 200ms ease-out;
  }

  .error-banner svg {
    flex-shrink: 0;
    margin-top: 1px;
  }

  .error-banner p {
    font-size: 0.9rem;
    margin: 0;
    color: #fca5a5;
    flex: 1;
  }

  .retry-btn {
    flex-shrink: 0;
    padding: 6px 16px;
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.4);
    border-radius: var(--radius-sm);
    color: #f87171;
    font-size: 0.85rem;
    font-weight: 600;
    font-family: var(--font-sans);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .retry-btn:hover {
    background: rgba(239, 68, 68, 0.25);
    border-color: rgba(239, 68, 68, 0.6);
    color: #fca5a5;
  }

  /* Result Tabs */
  .results-section {
    animation: fadeIn 300ms ease-out;
  }

  .result-tabs {
    display: flex;
    gap: 2px;
    border-bottom: 1px solid var(--border-primary);
    overflow-x: auto;
    padding-bottom: 0;
    margin-bottom: 1.5rem;
  }

  .result-tab {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 10px 16px;
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    color: var(--text-dim);
    font-size: 0.85rem;
    font-weight: 600;
    font-family: var(--font-sans);
    cursor: pointer;
    transition: all var(--transition-fast);
    white-space: nowrap;
    margin-bottom: -1px;
  }

  .result-tab.active {
    color: var(--accent);
    border-bottom-color: var(--accent);
  }

  .result-tab:hover:not(.active):not(:disabled) {
    color: var(--text-secondary);
  }

  .result-tab.disabled {
    opacity: 0.35;
    cursor: not-allowed;
  }

  .tab-icon {
    font-size: 1rem;
  }

  .tab-spinner {
    width: 12px;
    height: 12px;
    border: 2px solid rgba(59, 130, 246, 0.3);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  .result-content {
    min-height: 300px;
  }

  .empty-tab {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 200px;
  }

  .empty-tab p {
    color: var(--text-dim);
    font-size: 0.9rem;
  }

  /* Loading State */
  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    padding: 3rem 0;
  }

  .loading-spinner-lg {
    width: 40px;
    height: 40px;
    border: 3px solid var(--border-primary);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  .loading-state p {
    color: var(--text-dim);
    font-size: 0.9rem;
  }

  @media (max-width: 768px) {
    .brand-subtitle {
      display: none;
    }

    .results-layout {
      padding: 1rem;
    }

    .result-tab .tab-label {
      display: none;
    }

    .result-tab {
      padding: 10px 12px;
    }

    .tab-icon {
      font-size: 1.25rem;
    }
  }
</style>
