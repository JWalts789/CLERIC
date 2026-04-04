<script lang="ts">
  import type { Source } from './types';

  interface Props {
    data: Record<string, any>;
    content?: string;
  }

  let { data, content = '' }: Props = $props();

  let sources: Source[] = $derived(data?.sources ?? []);
  let hasRawContent = $derived(sources.length === 0 && content.length > 0);
  let perspectives = $derived([...new Set(sources.map(s => s.perspective).filter(Boolean))]);
  let activeFilter = $state<string | null>(null);

  let filteredSources = $derived(
    activeFilter ? sources.filter(s => s.perspective === activeFilter) : sources
  );

  function conflictBadge(level: string): { icon: string; class: string; label: string } {
    switch (level?.toUpperCase()) {
      case 'HIGH': return { icon: '\u{1F534}', class: 'badge-error', label: 'High COI' };
      case 'MODERATE': return { icon: '\u{1F7E1}', class: 'badge-warning', label: 'Moderate COI' };
      case 'LOW': return { icon: '\u{1F7E2}', class: 'badge-success', label: 'Low COI' };
      default: return { icon: '', class: '', label: '' };
    }
  }
</script>

<div class="source-cards">
  <div class="section-header">
    <span class="section-icon" style="background: rgba(49, 130, 206, 0.15); color: #3182ce;">
      {'\u{1F50E}'}
    </span>
    <div>
      <h2>Research Sources</h2>
      <p class="section-desc">{sources.length} sources gathered across {perspectives.length} perspectives</p>
    </div>
  </div>

  {#if perspectives.length > 1}
    <div class="filter-bar">
      <button
        class="filter-chip"
        class:active={activeFilter === null}
        onclick={() => activeFilter = null}
      >
        All ({sources.length})
      </button>
      {#each perspectives as perspective}
        <button
          class="filter-chip"
          class:active={activeFilter === perspective}
          onclick={() => activeFilter = activeFilter === perspective ? null : perspective}
        >
          {perspective} ({sources.filter(s => s.perspective === perspective).length})
        </button>
      {/each}
    </div>
  {/if}

  {#if sources.length > 0}
    <div class="sources-grid">
      {#each filteredSources as source, i}
        {@const coi = conflictBadge(source.conflict_of_interest)}
        <div class="source-card card" style="animation-delay: {i * 50}ms;">
          <div class="source-header">
            <h4 class="source-title">
              <a href={source.url} target="_blank" rel="noopener noreferrer">
                {source.title || source.url}
              </a>
            </h4>
            {#if coi.label}
              <span class="badge {coi.class}" title={source.conflict_detail || ''}>
                {coi.icon} {coi.label}
              </span>
            {/if}
          </div>

          {#if source.url}
            <a class="source-url" href={source.url} target="_blank" rel="noopener noreferrer">
              {source.url.length > 60 ? source.url.slice(0, 60) + '...' : source.url}
            </a>
          {/if}

          {#if source.perspective}
            <span class="perspective-badge badge badge-info">{source.perspective}</span>
          {/if}

          {#if source.claims?.length > 0}
            <div class="claims-list">
              <span class="claims-label">Key Claims:</span>
              <ul>
                {#each source.claims as claim}
                  <li>{claim}</li>
                {/each}
              </ul>
            </div>
          {/if}

          {#if source.credibility_notes}
            <p class="credibility-notes">
              <span class="notes-label">Credibility:</span> {source.credibility_notes}
            </p>
          {/if}

          {#if source.conflict_detail}
            <p class="conflict-detail">
              <span class="notes-label">Conflict Detail:</span> {source.conflict_detail}
            </p>
          {/if}
        </div>
      {/each}
    </div>
  {:else if hasRawContent}
    <div class="raw-content-fallback card">
      <p class="fallback-note">
        Structured source data was not extracted. Showing raw researcher findings below.
      </p>
      <div class="raw-prose">
        {#each content.split('\n') as line}
          {#if line.trim()}
            <p>{line}</p>
          {/if}
        {/each}
      </div>
    </div>
  {:else}
    <div class="empty-state">
      <p>No sources were gathered for this query.</p>
    </div>
  {/if}
</div>

<style>
  .source-cards {
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
    font-size: 1.2rem;
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

  .filter-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 1.25rem;
  }

  .filter-chip {
    padding: 5px 14px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: 100px;
    color: var(--text-muted);
    font-size: 0.8rem;
    font-family: var(--font-sans);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .filter-chip.active {
    background: var(--accent-bg);
    border-color: var(--accent);
    color: var(--accent);
  }

  .filter-chip:hover:not(.active) {
    border-color: var(--border-accent);
    color: var(--text-secondary);
  }

  .sources-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    gap: 1rem;
  }

  .source-card {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    animation: fadeIn 300ms ease-out backwards;
  }

  .source-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 8px;
  }

  .source-title {
    font-size: 1rem;
    font-weight: 600;
    line-height: 1.3;
    margin: 0;
  }

  .source-title a {
    color: var(--text-primary);
  }

  .source-title a:hover {
    color: var(--accent);
  }

  .source-url {
    font-size: 0.8rem;
    font-family: var(--font-mono);
    color: var(--text-dim);
    word-break: break-all;
  }

  .perspective-badge {
    align-self: flex-start;
  }

  .claims-list {
    margin-top: 4px;
  }

  .claims-label, .notes-label {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-dim);
  }

  .claims-list ul {
    list-style: none;
    padding: 0;
    margin: 4px 0 0 0;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .claims-list li {
    font-size: 0.875rem;
    color: var(--text-secondary);
    padding-left: 16px;
    position: relative;
  }

  .claims-list li::before {
    content: '\u2022';
    position: absolute;
    left: 4px;
    color: var(--accent);
  }

  .credibility-notes, .conflict-detail {
    font-size: 0.85rem;
    color: var(--text-muted);
    margin: 0;
  }

  .raw-content-fallback {
    padding: 1.25rem;
  }

  .fallback-note {
    font-size: 0.8rem;
    color: var(--text-dim);
    font-style: italic;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border-primary);
  }

  .raw-prose p {
    font-size: 0.875rem;
    color: var(--text-secondary);
    line-height: 1.7;
    margin: 0 0 0.5rem 0;
  }

  .empty-state {
    padding: 2rem;
    text-align: center;
    color: var(--text-dim);
  }

  @media (max-width: 768px) {
    .sources-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
