<script lang="ts">
  const STORAGE_KEY = 'cleric-settings';

  interface Model {
    id: string;
    name: string;
    cost_per_query: string;
    speed: string;
  }

  interface Settings {
    model: string;
    maxResults: number;
  }

  interface Props {
    open: boolean;
    onclose: () => void;
    onsave: (settings: Settings) => void;
  }

  let { open, onclose, onsave }: Props = $props();

  const models: Model[] = [
    { id: 'claude-haiku-4-5-20251001', name: 'Haiku 4.5', cost_per_query: '~$0.15-0.25', speed: 'Fast' },
    { id: 'claude-sonnet-4-6', name: 'Sonnet 4.6', cost_per_query: '~$0.40-0.80', speed: 'Medium' },
    { id: 'claude-opus-4-6', name: 'Opus 4.6', cost_per_query: '~$2.00-5.00', speed: 'Slow' },
  ];

  function loadSettings(): Settings {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) return JSON.parse(raw);
    } catch {}
    return { model: 'claude-sonnet-4-6', maxResults: 5 };
  }

  let selectedModel = $state(loadSettings().model);
  let maxResults = $state(loadSettings().maxResults);

  // Reset form values when panel opens
  $effect(() => {
    if (open) {
      const saved = loadSettings();
      selectedModel = saved.model;
      maxResults = saved.maxResults;
    }
  });

  function handleSave() {
    const settings: Settings = { model: selectedModel, maxResults };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    onsave(settings);
    onclose();
  }

  function handleCancel() {
    onclose();
  }

  function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) {
      onclose();
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      onclose();
    }
  }

  function getSpeedClass(speed: string): string {
    if (speed === 'Fast') return 'speed-fast';
    if (speed === 'Medium') return 'speed-medium';
    return 'speed-slow';
  }
</script>

{#if open}
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="settings-backdrop" onclick={handleBackdropClick} onkeydown={handleKeydown}>
    <div class="settings-panel" role="dialog" aria-label="Settings">
      <div class="settings-header">
        <h3>Settings</h3>
        <button class="close-btn" onclick={handleCancel} aria-label="Close settings">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="settings-body">
        <!-- Model Selection -->
        <div class="setting-group">
          <label class="setting-label" for="model-select">Model</label>
          <p class="setting-description">Choose the Claude model for research queries.</p>
          <div class="model-options">
            {#each models as model}
              <button
                class="model-option"
                class:selected={selectedModel === model.id}
                onclick={() => selectedModel = model.id}
              >
                <div class="model-option-header">
                  <span class="model-name">{model.name}</span>
                  <span class="model-speed {getSpeedClass(model.speed)}">{model.speed}</span>
                </div>
                <span class="model-cost">{model.cost_per_query}</span>
              </button>
            {/each}
          </div>
        </div>

        <!-- Max Search Results -->
        <div class="setting-group">
          <label class="setting-label" for="max-results">Max Search Results: <strong>{maxResults}</strong></label>
          <p class="setting-description">Number of sources to gather per research query (3-15).</p>
          <input
            id="max-results"
            type="range"
            min="3"
            max="15"
            step="1"
            bind:value={maxResults}
            class="range-slider"
          />
          <div class="range-labels">
            <span>3</span>
            <span>15</span>
          </div>
        </div>
      </div>

      <div class="settings-footer">
        <button class="btn-cancel" onclick={handleCancel}>Cancel</button>
        <button class="btn-save" onclick={handleSave}>Save</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .settings-backdrop {
    position: fixed;
    inset: 0;
    z-index: 200;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    animation: fadeInBackdrop 150ms ease-out;
  }

  @keyframes fadeInBackdrop {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  .settings-panel {
    width: 460px;
    max-width: 90vw;
    max-height: 85vh;
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-lg);
    display: flex;
    flex-direction: column;
    animation: fadeInScale 200ms ease-out;
  }

  @keyframes fadeInScale {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
  }

  .settings-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid var(--border-primary);
  }

  .settings-header h3 {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .close-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: none;
    border: 1px solid transparent;
    border-radius: var(--radius-sm);
    color: var(--text-dim);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .close-btn:hover {
    background: var(--bg-tertiary);
    color: var(--text-secondary);
    border-color: var(--border-primary);
  }

  .settings-body {
    padding: 1.5rem;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 1.75rem;
  }

  .setting-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .setting-label {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-primary);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .setting-description {
    font-size: 0.8rem;
    color: var(--text-dim);
    margin: 0;
    line-height: 1.4;
  }

  /* Model selection cards */
  .model-options {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 0.25rem;
  }

  .model-option {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: var(--bg-primary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all var(--transition-fast);
    font-family: var(--font-sans);
    text-align: left;
  }

  .model-option:hover {
    border-color: var(--border-accent);
    background: var(--bg-tertiary);
  }

  .model-option.selected {
    border-color: var(--accent);
    background: var(--accent-bg);
    box-shadow: 0 0 0 1px var(--accent);
  }

  .model-option-header {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .model-name {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .model-speed {
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 100px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .speed-fast {
    background: rgba(34, 197, 94, 0.15);
    color: #4ade80;
  }

  .speed-medium {
    background: rgba(234, 179, 8, 0.15);
    color: #facc15;
  }

  .speed-slow {
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
  }

  .model-cost {
    font-size: 0.8rem;
    color: var(--text-muted);
    font-family: var(--font-mono);
  }

  /* Range slider */
  .range-slider {
    -webkit-appearance: none;
    appearance: none;
    width: 100%;
    height: 6px;
    background: var(--bg-tertiary);
    border-radius: 3px;
    outline: none;
    margin-top: 0.25rem;
  }

  .range-slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 20px;
    height: 20px;
    background: var(--accent);
    border-radius: 50%;
    cursor: pointer;
    border: 2px solid var(--bg-secondary);
    box-shadow: 0 0 0 2px var(--accent);
    transition: transform var(--transition-fast);
  }

  .range-slider::-webkit-slider-thumb:hover {
    transform: scale(1.15);
  }

  .range-slider::-moz-range-thumb {
    width: 20px;
    height: 20px;
    background: var(--accent);
    border-radius: 50%;
    cursor: pointer;
    border: 2px solid var(--bg-secondary);
    box-shadow: 0 0 0 2px var(--accent);
  }

  .range-labels {
    display: flex;
    justify-content: space-between;
    font-size: 0.7rem;
    color: var(--text-dim);
    margin-top: 2px;
  }

  /* Footer buttons */
  .settings-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    padding: 1rem 1.5rem;
    border-top: 1px solid var(--border-primary);
  }

  .btn-cancel,
  .btn-save {
    padding: 8px 20px;
    border-radius: var(--radius-sm);
    font-size: 0.85rem;
    font-weight: 600;
    font-family: var(--font-sans);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .btn-cancel {
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    color: var(--text-secondary);
  }

  .btn-cancel:hover {
    border-color: var(--border-accent);
    color: var(--text-primary);
  }

  .btn-save {
    background: var(--accent);
    border: 1px solid var(--accent);
    color: white;
  }

  .btn-save:hover {
    background: var(--accent-hover);
    border-color: var(--accent-hover);
  }
</style>
