<script lang="ts">
  import { STAGES } from './types';

  interface Props {
    onsubmit: (query: string) => void;
    loading: boolean;
  }

  let { onsubmit, loading }: Props = $props();

  let query = $state('');

  const examples = [
    'Is nuclear energy safe?',
    'What caused the 2008 financial crisis?',
    'Are electric vehicles better for the environment?',
    'Does social media cause depression in teens?',
    'Is remote work more productive than office work?',
  ];

  function handleSubmit(e: Event) {
    e.preventDefault();
    if (query.trim() && !loading) {
      onsubmit(query.trim());
    }
  }

  function selectExample(example: string) {
    query = example;
  }
</script>

<div class="query-container">
  <div class="hero-section">
    <div class="logo-mark">
      <div class="logo-ring">
        {#each STAGES as stage, i}
          <span
            class="ring-dot"
            style="--dot-color: {stage.color}; --dot-angle: {i * 60}deg;"
          ></span>
        {/each}
        <span class="ring-center">C</span>
      </div>
    </div>
    <h1 class="hero-title">What would you like to investigate?</h1>
    <p class="hero-subtitle">
      C.L.E.R.I.C. deploys six specialized AI agents to analyze your query from
      multiple angles, cross-check facts, and deliver a comprehensive, bias-aware report.
    </p>
  </div>

  <form class="search-form" onsubmit={handleSubmit}>
    <div class="input-wrapper" class:focused={false}>
      <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8" />
        <path d="M21 21l-4.35-4.35" />
      </svg>
      <input
        type="text"
        class="search-input"
        bind:value={query}
        placeholder="Enter a claim, question, or topic to research..."
        disabled={loading}
      />
      <button
        type="submit"
        class="submit-btn"
        disabled={!query.trim() || loading}
      >
        {#if loading}
          <span class="spinner"></span>
          Analyzing...
        {:else}
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
          Research
        {/if}
      </button>
    </div>
  </form>

  <div class="examples-section">
    <span class="examples-label">Try an example:</span>
    <div class="examples-chips">
      {#each examples as example}
        <button
          class="chip"
          onclick={() => selectExample(example)}
          disabled={loading}
        >
          {example}
        </button>
      {/each}
    </div>
  </div>

  <div class="pipeline-preview">
    {#each STAGES as stage, i}
      <div class="preview-stage">
        <span class="preview-icon" style="background: {stage.color}20; color: {stage.color};">
          {stage.icon}
        </span>
        <span class="preview-label">{stage.label}</span>
      </div>
      {#if i < STAGES.length - 1}
        <div class="preview-arrow">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </div>
      {/if}
    {/each}
  </div>
</div>

<style>
  .query-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: calc(100vh - 64px);
    padding: 2rem;
    animation: fadeIn 600ms ease-out;
  }

  .hero-section {
    text-align: center;
    margin-bottom: 2.5rem;
  }

  .logo-mark {
    margin-bottom: 1.5rem;
  }

  .logo-ring {
    position: relative;
    width: 72px;
    height: 72px;
    margin: 0 auto;
    border: 2px solid var(--border-primary);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .ring-dot {
    position: absolute;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--dot-color);
    top: 50%;
    left: 50%;
    transform: rotate(var(--dot-angle)) translateY(-34px) translate(-50%, -50%);
    box-shadow: 0 0 8px color-mix(in srgb, var(--dot-color) 50%, transparent);
  }

  .ring-center {
    font-family: var(--font-mono);
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--accent);
  }

  .hero-title {
    font-size: 2.25rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    margin-bottom: 0.75rem;
    background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .hero-subtitle {
    max-width: 560px;
    margin: 0 auto;
    color: var(--text-muted);
    font-size: 1rem;
    line-height: 1.7;
  }

  /* Search form */
  .search-form {
    width: 100%;
    max-width: 680px;
    margin-bottom: 1.5rem;
  }

  .input-wrapper {
    display: flex;
    align-items: center;
    background: var(--bg-secondary);
    border: 1.5px solid var(--border-primary);
    border-radius: var(--radius-lg);
    padding: 6px 6px 6px 18px;
    transition: border-color var(--transition-base), box-shadow var(--transition-base);
    gap: 8px;
  }

  .input-wrapper:focus-within {
    border-color: var(--accent);
    box-shadow: var(--shadow-glow);
  }

  .search-icon {
    width: 20px;
    height: 20px;
    color: var(--text-dim);
    flex-shrink: 0;
  }

  .search-input {
    flex: 1;
    background: none;
    border: none;
    outline: none;
    color: var(--text-primary);
    font-size: 1rem;
    font-family: var(--font-sans);
    padding: 12px 8px;
    min-width: 0;
  }

  .search-input::placeholder {
    color: var(--text-dim);
  }

  .search-input:disabled {
    opacity: 0.6;
  }

  .submit-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 24px;
    background: var(--accent);
    color: white;
    border: none;
    border-radius: calc(var(--radius-lg) - 4px);
    font-size: 0.925rem;
    font-weight: 600;
    font-family: var(--font-sans);
    cursor: pointer;
    transition: background var(--transition-fast), transform var(--transition-fast);
    white-space: nowrap;
    flex-shrink: 0;
  }

  .submit-btn:hover:not(:disabled) {
    background: var(--accent-hover);
    transform: translateY(-1px);
  }

  .submit-btn:active:not(:disabled) {
    transform: translateY(0);
  }

  .submit-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }

  /* Examples */
  .examples-section {
    text-align: center;
    margin-bottom: 3rem;
    max-width: 680px;
  }

  .examples-label {
    display: block;
    font-size: 0.8rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
    margin-bottom: 0.75rem;
  }

  .examples-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
  }

  .chip {
    padding: 6px 14px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: 100px;
    color: var(--text-secondary);
    font-size: 0.825rem;
    font-family: var(--font-sans);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .chip:hover:not(:disabled) {
    background: var(--accent-bg);
    border-color: var(--accent);
    color: var(--accent);
  }

  .chip:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  /* Pipeline Preview */
  .pipeline-preview {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 1.25rem 2rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    flex-wrap: wrap;
    justify-content: center;
  }

  .preview-stage {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .preview-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    border-radius: var(--radius-sm);
    font-size: 0.9rem;
  }

  .preview-label {
    font-size: 0.8rem;
    color: var(--text-muted);
    font-weight: 500;
  }

  .preview-arrow {
    color: var(--text-dim);
    display: flex;
    align-items: center;
  }

  @media (max-width: 768px) {
    .hero-title {
      font-size: 1.75rem;
    }

    .pipeline-preview {
      display: none;
    }

    .query-container {
      padding: 1.5rem 1rem;
    }
  }
</style>
