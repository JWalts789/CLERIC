<script lang="ts">
  import { STAGES, type StageName, type StageStatus } from './types';

  interface Props {
    stageStatuses: Record<string, StageStatus>;
    stageTokens: Record<string, { input: number; output: number }>;
    activeStage: string | null;
  }

  let { stageStatuses, stageTokens, activeStage }: Props = $props();

  function formatTokens(tokens: { input: number; output: number }): string {
    const total = tokens.input + tokens.output;
    if (total >= 1000) return `${(total / 1000).toFixed(1)}k`;
    return total.toString();
  }
</script>

<div class="pipeline-progress" aria-label={activeStage ? `Pipeline running: ${STAGES.find(s => s.key === activeStage)?.label ?? activeStage}` : 'Analysis pipeline'}>
  <h3 class="progress-title">Analysis Pipeline</h3>
  <div class="stages">
    {#each STAGES as stage, i}
      {@const status = stageStatuses[stage.key] || 'pending'}
      {@const tokens = stageTokens[stage.key]}
      <div class="stage-wrapper">
        <div
          class="stage-card"
          class:pending={status === 'pending'}
          class:running={status === 'running'}
          class:complete={status === 'complete'}
          class:error={status === 'error'}
          style="--stage-color: {stage.color};"
        >
          <div class="stage-indicator">
            {#if status === 'complete'}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" class="check-icon">
                <path d="M5 13l4 4L19 7" />
              </svg>
            {:else if status === 'running'}
              <div class="running-spinner"></div>
            {:else if status === 'error'}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" class="error-icon">
                <path d="M6 18L18 6M6 6l12 12" />
              </svg>
            {:else}
              <span class="stage-number">{i + 1}</span>
            {/if}
          </div>

          <div class="stage-content">
            <span class="stage-icon">{stage.icon}</span>
            <span class="stage-label">{stage.label}</span>
          </div>

          {#if tokens}
            <div class="token-badge" style="background: {stage.color}20; color: {stage.color};">
              {formatTokens(tokens)} tokens
            </div>
          {/if}
        </div>

        {#if i < STAGES.length - 1}
          <div class="connector" class:active={status === 'complete'}></div>
        {/if}
      </div>
    {/each}
  </div>
</div>

<style>
  .pipeline-progress {
    margin-bottom: 1.5rem;
  }

  .progress-title {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-dim);
    margin-bottom: 1rem;
    font-weight: 600;
    background: linear-gradient(90deg, var(--text-dim) 0%, rgba(110, 231, 183, 0.4) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .stages {
    display: flex;
    align-items: flex-start;
    gap: 0;
    overflow-x: auto;
    padding-bottom: 4px;
  }

  .stage-wrapper {
    display: flex;
    align-items: center;
    flex-shrink: 0;
  }

  .stage-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 1rem 1.25rem;
    background: rgba(17, 24, 39, 0.7);
    backdrop-filter: blur(12px);
    border: 1.5px solid rgba(110, 231, 183, 0.06);
    border-radius: 16px;
    min-width: 130px;
    transition: all var(--transition-base);
    position: relative;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
  }

  .stage-card.running {
    border-color: var(--stage-color);
    --pulse-color: color-mix(in srgb, var(--stage-color) 25%, transparent);
    animation: gentlePulse 2.5s ease-in-out infinite;
  }

  .stage-card.complete {
    border-color: color-mix(in srgb, var(--stage-color) 40%, transparent);
    background: color-mix(in srgb, var(--stage-color) 4%, rgba(17, 24, 39, 0.7));
  }

  .stage-card.error {
    border-color: var(--color-error);
    background: rgba(248, 113, 113, 0.05);
  }

  .stage-card.pending {
    opacity: 0.4;
  }

  .stage-indicator {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 700;
    background: var(--bg-tertiary);
    color: var(--text-dim);
  }

  .stage-card.running .stage-indicator {
    background: color-mix(in srgb, var(--stage-color) 20%, transparent);
    color: var(--stage-color);
  }

  .stage-card.complete .stage-indicator {
    background: var(--stage-color);
    color: white;
    box-shadow: 0 0 12px color-mix(in srgb, var(--stage-color) 30%, transparent);
  }

  .stage-card.error .stage-indicator {
    background: var(--color-error);
    color: white;
  }

  .check-icon, .error-icon {
    width: 16px;
    height: 16px;
  }

  .running-spinner {
    width: 18px;
    height: 18px;
    border: 2.5px solid color-mix(in srgb, var(--stage-color) 30%, transparent);
    border-top-color: var(--stage-color);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  .stage-number {
    font-family: var(--font-mono);
  }

  .stage-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
  }

  .stage-icon {
    font-size: 1.25rem;
  }

  .stage-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-align: center;
    white-space: nowrap;
  }

  .token-badge {
    font-size: 0.65rem;
    font-weight: 600;
    font-family: var(--font-mono);
    padding: 2px 8px;
    border-radius: 100px;
    animation: fadeIn 200ms ease-out;
  }

  .connector {
    width: 32px;
    height: 2px;
    background: linear-gradient(90deg, rgba(110, 231, 183, 0.1), rgba(110, 231, 183, 0.05));
    flex-shrink: 0;
    transition: all var(--transition-base);
    position: relative;
    border-radius: 1px;
  }

  .connector.active {
    background: linear-gradient(90deg, var(--accent), rgba(110, 231, 183, 0.4));
  }

  .connector::after {
    content: '';
    position: absolute;
    right: -3px;
    top: -3px;
    width: 0;
    height: 0;
    border-top: 4px solid transparent;
    border-bottom: 4px solid transparent;
    border-left: 6px solid rgba(110, 231, 183, 0.1);
    transition: border-left-color var(--transition-base);
  }

  .connector.active::after {
    border-left-color: var(--accent);
  }

  @media (max-width: 900px) {
    .stages {
      flex-direction: column;
      align-items: stretch;
    }

    .stage-wrapper {
      flex-direction: column;
    }

    .stage-card {
      flex-direction: row;
      min-width: 0;
      width: 100%;
      padding: 0.75rem 1rem;
    }

    .connector {
      width: 2px;
      height: 16px;
      margin-left: 2.5rem;
    }

    .connector::after {
      right: auto;
      left: -3px;
      top: auto;
      bottom: -3px;
      border-left: 4px solid transparent;
      border-right: 4px solid transparent;
      border-top: 6px solid rgba(110, 231, 183, 0.1);
      border-bottom: none;
    }

    .connector.active::after {
      border-top-color: var(--accent);
      border-left-color: transparent;
    }
  }
</style>
