<script lang="ts">
  import { onMount } from 'svelte';
  import mermaid from 'mermaid';

  interface Props {
    diagrams: Record<string, string>;
  }

  let { diagrams }: Props = $props();

  let diagramKeys = $derived(Object.keys(diagrams));
  let activeTab = $state('');
  let containerEl: HTMLDivElement | undefined = $state();
  let copied = $state(false);

  // Initialize mermaid
  onMount(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      themeVariables: {
        primaryColor: '#3b82f6',
        primaryTextColor: '#e2e8f0',
        primaryBorderColor: '#475569',
        lineColor: '#64748b',
        secondaryColor: '#1e293b',
        tertiaryColor: '#283548',
        fontFamily: 'Inter, system-ui, sans-serif',
      },
    });
  });

  $effect(() => {
    if (diagramKeys.length > 0 && !activeTab) {
      activeTab = diagramKeys[0];
    }
  });

  $effect(() => {
    if (activeTab && diagrams[activeTab] && containerEl) {
      renderDiagram();
    }
  });

  async function renderDiagram() {
    if (!containerEl || !diagrams[activeTab]) return;
    try {
      const id = `mermaid-${Date.now()}`;
      const { svg } = await mermaid.render(id, diagrams[activeTab]);
      containerEl.innerHTML = svg;
    } catch (e) {
      console.error('Mermaid render error:', e);
      containerEl.innerHTML = `<pre class="mermaid-error">${diagrams[activeTab]}</pre>`;
    }
  }

  async function copySource() {
    if (!diagrams[activeTab]) return;
    try {
      await navigator.clipboard.writeText(diagrams[activeTab]);
      copied = true;
      setTimeout(() => copied = false, 2000);
    } catch {
      // Fallback
      const ta = document.createElement('textarea');
      ta.value = diagrams[activeTab];
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      copied = true;
      setTimeout(() => copied = false, 2000);
    }
  }

  function formatTabName(key: string): string {
    return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }
</script>

<div class="mermaid-diagrams">
  <div class="section-header">
    <span class="section-icon" style="background: rgba(59, 130, 246, 0.15); color: #3b82f6;">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
        <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
      </svg>
    </span>
    <div>
      <h2>Analysis Diagrams</h2>
      <p class="section-desc">Visual representations of the research pipeline</p>
    </div>
  </div>

  {#if diagramKeys.length > 1}
    <div class="diagram-tabs">
      {#each diagramKeys as key}
        <button
          class="tab-btn"
          class:active={activeTab === key}
          onclick={() => activeTab = key}
        >
          {formatTabName(key)}
        </button>
      {/each}
    </div>
  {/if}

  <div class="diagram-container card">
    <div class="diagram-toolbar">
      <span class="diagram-name">{formatTabName(activeTab)}</span>
      <button class="copy-btn" onclick={copySource}>
        {#if copied}
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <path d="M5 13l4 4L19 7" />
          </svg>
          Copied
        {:else}
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
            <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
          </svg>
          Copy Source
        {/if}
      </button>
    </div>
    <div class="diagram-render" bind:this={containerEl}></div>
  </div>
</div>

<style>
  .mermaid-diagrams {
    animation: fadeIn 400ms ease-out;
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 1.25rem;
  }

  .section-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: var(--radius-sm);
    flex-shrink: 0;
  }

  .section-header h2 {
    margin-bottom: 2px;
    font-size: 1.25rem;
  }

  .section-desc {
    font-size: 0.85rem;
    color: var(--text-dim);
    margin: 0;
  }

  .diagram-tabs {
    display: flex;
    gap: 4px;
    margin-bottom: 1rem;
    border-bottom: 1px solid var(--border-primary);
    padding-bottom: 0;
  }

  .tab-btn {
    padding: 8px 16px;
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    color: var(--text-muted);
    font-size: 0.85rem;
    font-weight: 600;
    font-family: var(--font-sans);
    cursor: pointer;
    transition: all var(--transition-fast);
    margin-bottom: -1px;
  }

  .tab-btn.active {
    color: var(--accent);
    border-bottom-color: var(--accent);
  }

  .tab-btn:hover:not(.active) {
    color: var(--text-secondary);
  }

  .diagram-container {
    overflow: hidden;
  }

  .diagram-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border-primary);
    margin-bottom: 1rem;
  }

  .diagram-name {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .copy-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-sm);
    color: var(--text-muted);
    font-size: 0.8rem;
    font-family: var(--font-sans);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .copy-btn:hover {
    border-color: var(--accent);
    color: var(--accent);
  }

  .diagram-render {
    display: flex;
    justify-content: center;
    overflow-x: auto;
    padding: 0.5rem 0;
    min-height: 200px;
  }

  .diagram-render :global(svg) {
    max-width: 100%;
    height: auto;
  }

  .diagram-render :global(.mermaid-error) {
    font-family: var(--font-mono);
    font-size: 0.8rem;
    color: var(--text-muted);
    white-space: pre-wrap;
    word-break: break-word;
  }
</style>
