<script lang="ts">
  import { exportMarkdown, exportJson } from './api';

  interface Props {
    jobId: string;
  }

  let { jobId }: Props = $props();

  let open = $state(false);
  let menuRef = $state<HTMLDivElement | null>(null);

  function toggle() {
    open = !open;
  }

  async function downloadMarkdown() {
    open = false;
    try {
      await exportMarkdown(jobId);
    } catch (err) {
      console.error('Markdown export failed:', err);
    }
  }

  async function downloadJson() {
    open = false;
    try {
      await exportJson(jobId);
    } catch (err) {
      console.error('JSON export failed:', err);
    }
  }

  function printPdf() {
    open = false;
    window.print();
  }

  $effect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (menuRef && !menuRef.contains(e.target as Node)) {
        open = false;
      }
    };
    document.addEventListener('click', handler, true);
    return () => document.removeEventListener('click', handler, true);
  });
</script>

<div class="export-menu" bind:this={menuRef}>
  <button class="export-btn" onclick={toggle}>
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
    Export
    <svg class="chevron" class:open viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
      <polyline points="6 9 12 15 18 9" />
    </svg>
  </button>

  {#if open}
    <div class="dropdown">
      <button class="dropdown-item" onclick={downloadMarkdown}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </svg>
        Download Markdown
      </button>
      <button class="dropdown-item" onclick={downloadJson}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="12" y1="18" x2="12" y2="12" />
          <polyline points="9 15 12 12 15 15" />
        </svg>
        Download JSON
      </button>
      <div class="dropdown-divider"></div>
      <button class="dropdown-item" onclick={printPdf}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
          <polyline points="6 9 6 2 18 2 18 9" />
          <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" />
          <rect x="6" y="14" width="12" height="8" />
        </svg>
        Print as PDF
      </button>
    </div>
  {/if}
</div>

<style>
  .export-menu {
    position: relative;
    display: inline-block;
  }

  .export-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    font-size: 0.85rem;
    font-weight: 600;
    font-family: var(--font-sans);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .export-btn:hover {
    border-color: var(--accent);
    color: var(--accent);
  }

  .chevron {
    transition: transform var(--transition-fast);
  }

  .chevron.open {
    transform: rotate(180deg);
  }

  .dropdown {
    position: absolute;
    top: calc(100% + 4px);
    right: 0;
    min-width: 200px;
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-lg);
    z-index: 200;
    padding: 4px;
    animation: fadeIn 150ms ease-out;
  }

  .dropdown-item {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    padding: 8px 12px;
    background: none;
    border: none;
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    font-size: 0.85rem;
    font-family: var(--font-sans);
    cursor: pointer;
    transition: all var(--transition-fast);
    text-align: left;
  }

  .dropdown-item:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }

  .dropdown-divider {
    height: 1px;
    background: var(--border-primary);
    margin: 4px 0;
  }
</style>
