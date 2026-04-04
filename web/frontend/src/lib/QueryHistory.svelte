<script lang="ts">
  import { fetchHistory, deleteResult, type HistoryItem } from './api';

  interface Props {
    onselect: (result: HistoryItem) => void;
  }

  let { onselect }: Props = $props();

  let items = $state<HistoryItem[]>([]);
  let total = $state(0);
  let search = $state('');
  let loading = $state(true);
  let searchTimeout: ReturnType<typeof setTimeout> | null = null;

  async function load(searchQuery?: string) {
    loading = true;
    try {
      const res = await fetchHistory(20, 0, searchQuery || undefined);
      items = res.results;
      total = res.total;
    } catch {
      items = [];
      total = 0;
    } finally {
      loading = false;
    }
  }

  function handleSearchInput() {
    if (searchTimeout) clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => load(search), 300);
  }

  async function handleDelete(e: Event, id: string) {
    e.stopPropagation();
    try {
      await deleteResult(id);
      items = items.filter((i) => i.id !== id);
      total = Math.max(0, total - 1);
    } catch {
      // silently ignore
    }
  }

  function gradeColor(grade: string): string {
    if (!grade) return 'badge-neutral';
    const g = grade.toUpperCase();
    if (g.startsWith('A')) return 'badge-success';
    if (g.startsWith('B')) return 'badge-info';
    if (g.startsWith('C')) return 'badge-warning';
    return 'badge-error';
  }

  function formatDate(iso: string): string {
    try {
      const d = new Date(iso);
      return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return iso;
    }
  }

  function formatDuration(seconds: number | null): string {
    if (!seconds) return '--';
    if (seconds < 60) return `${seconds.toFixed(0)}s`;
    return `${(seconds / 60).toFixed(1)}m`;
  }

  function formatTokens(count: number | null): string {
    if (!count) return '--';
    if (count >= 1000) return `${(count / 1000).toFixed(1)}k`;
    return String(count);
  }

  $effect(() => {
    load();
  });
</script>

<div class="history-container">
  <div class="history-header">
    <h3 class="history-title">Past Research</h3>
    {#if total > 0}
      <span class="history-count badge badge-neutral">{total}</span>
    {/if}
  </div>

  <div class="history-search">
    <input
      type="text"
      placeholder="Search past queries..."
      bind:value={search}
      oninput={handleSearchInput}
      class="search-input"
      aria-label="Search past queries"
    />
  </div>

  {#if loading}
    <div class="history-loading">
      <div class="history-spinner"></div>
    </div>
  {:else if items.length === 0}
    <div class="history-empty">
      <p>No past research</p>
    </div>
  {:else}
    <div class="history-list">
      {#each items as item (item.id)}
        <div
          class="history-card"
          role="button"
          tabindex="0"
          onclick={() => onselect(item)}
          onkeydown={(e) => e.key === 'Enter' && onselect(item)}
        >
          <div class="card-top">
            <span class="card-query">{item.query}</span>
            <button
              class="card-delete"
              onclick={(e) => handleDelete(e, item.id)}
              title="Delete"
              aria-label="Delete this research result"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="card-meta">
            {#if item.overall_grade}
              <span class="badge {gradeColor(item.overall_grade)}">{item.overall_grade}</span>
            {/if}
            <span class="meta-item">{formatDate(item.created_at)}</span>
            <span class="meta-item">{formatDuration(item.duration_seconds)}</span>
            <span class="meta-item">{formatTokens(item.total_tokens)} tok</span>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .history-container {
    width: 100%;
  }

  .history-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 0.75rem;
  }

  .history-title {
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .history-count {
    font-size: 0.7rem;
  }

  .history-search {
    margin-bottom: 0.75rem;
  }

  .search-input {
    width: 100%;
    padding: 8px 12px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-sm);
    color: var(--text-primary);
    font-size: 0.85rem;
    font-family: var(--font-sans);
    transition: border-color var(--transition-fast);
  }

  .search-input::placeholder {
    color: var(--text-dim);
  }

  .search-input:focus {
    outline: none;
    border-color: var(--accent);
  }

  .history-loading {
    display: flex;
    justify-content: center;
    padding: 2rem 0;
  }

  .history-spinner {
    width: 24px;
    height: 24px;
    border: 2px solid var(--border-primary);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  .history-empty {
    text-align: center;
    padding: 2rem 0;
  }

  .history-empty p {
    color: var(--text-dim);
    font-size: 0.85rem;
  }

  .history-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
    max-height: 400px;
    overflow-y: auto;
  }

  .history-card {
    display: flex;
    flex-direction: column;
    gap: 6px;
    width: 100%;
    padding: 10px 12px;
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-sm);
    cursor: pointer;
    text-align: left;
    font-family: var(--font-sans);
    transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
  }

  .history-card:hover {
    border-color: var(--accent);
    box-shadow: var(--shadow-sm);
  }

  .card-top {
    display: flex;
    align-items: flex-start;
    gap: 8px;
  }

  .card-query {
    flex: 1;
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text-primary);
    line-height: 1.3;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }

  .card-delete {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    padding: 0;
    background: none;
    border: 1px solid transparent;
    border-radius: var(--radius-sm);
    color: var(--text-dim);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .card-delete:hover {
    color: var(--color-error);
    border-color: rgba(239, 68, 68, 0.3);
    background: rgba(239, 68, 68, 0.08);
  }

  .card-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .meta-item {
    font-size: 0.72rem;
    color: var(--text-dim);
  }
</style>
