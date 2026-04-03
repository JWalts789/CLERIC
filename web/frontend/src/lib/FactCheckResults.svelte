<script lang="ts">
  import type { ClaimStatus } from './types';

  interface Props {
    data: Record<string, any>;
  }

  let { data }: Props = $props();

  let claims = $derived(data?.claims ?? data?.verified_claims ?? data?.results ?? []);

  function statusConfig(status: string): { icon: string; color: string; label: string; class: string } {
    switch (status?.toUpperCase()) {
      case 'VERIFIED': return { icon: '\u2705', color: '#22c55e', label: 'Verified', class: 'badge-success' };
      case 'DISPUTED': return { icon: '\u26A0\uFE0F', color: '#eab308', label: 'Disputed', class: 'badge-warning' };
      case 'UNVERIFIED': return { icon: '\u2753', color: '#94a3b8', label: 'Unverified', class: 'badge-neutral' };
      case 'FALSE': return { icon: '\u274C', color: '#ef4444', label: 'False', class: 'badge-error' };
      default: return { icon: '\u2753', color: '#94a3b8', label: status || 'Unknown', class: 'badge-neutral' };
    }
  }
</script>

<div class="fact-check-results">
  <div class="section-header">
    <span class="section-icon" style="background: rgba(56, 161, 105, 0.15); color: #38a169;">
      {'\u2705'}
    </span>
    <div>
      <h2>Fact Check Results</h2>
      <p class="section-desc">{claims.length} claims analyzed for accuracy</p>
    </div>
  </div>

  <div class="claims-list">
    {#each claims as claim, i}
      {@const status = statusConfig(claim.status || claim.verdict)}
      {@const confidence = claim.confidence ?? claim.confidence_score ?? 0}
      {@const supporting = claim.supporting_sources ?? claim.supporting ?? 0}
      {@const contradicting = claim.contradicting_sources ?? claim.contradicting ?? 0}
      <div class="claim-row card" style="animation-delay: {i * 60}ms;">
        <div class="claim-main">
          <div class="claim-status">
            <span class="status-icon">{status.icon}</span>
            <span class="badge {status.class}">{status.label}</span>
          </div>
          <div class="claim-text">
            <p>{claim.claim || claim.text || claim.statement || JSON.stringify(claim)}</p>
          </div>
        </div>

        <div class="claim-meta">
          {#if confidence > 0}
            <div class="confidence-bar-container">
              <div class="confidence-label">
                <span>Confidence</span>
                <span class="confidence-value">{Math.round(confidence * (confidence <= 1 ? 100 : 1))}%</span>
              </div>
              <div class="confidence-track">
                <div
                  class="confidence-fill"
                  style="width: {confidence <= 1 ? confidence * 100 : confidence}%; background: {status.color};"
                ></div>
              </div>
            </div>
          {/if}

          <div class="source-counts">
            {#if supporting > 0}
              <span class="source-count supporting" title="Supporting sources">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                  <path d="M7 10l5 5 5-5" />
                </svg>
                {supporting} supporting
              </span>
            {/if}
            {#if contradicting > 0}
              <span class="source-count contradicting" title="Contradicting sources">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                  <path d="M7 14l5-5 5 5" />
                </svg>
                {contradicting} contradicting
              </span>
            {/if}
          </div>
        </div>

        {#if claim.explanation}
          <p class="claim-explanation">{claim.explanation}</p>
        {/if}
      </div>
    {/each}
  </div>
</div>

<style>
  .fact-check-results {
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

  .claims-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .claim-row {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    animation: fadeIn 300ms ease-out backwards;
  }

  .claim-main {
    display: flex;
    gap: 12px;
    align-items: flex-start;
  }

  .claim-status {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    flex-shrink: 0;
    min-width: 90px;
  }

  .status-icon {
    font-size: 1.5rem;
  }

  .claim-text p {
    font-size: 0.925rem;
    color: var(--text-secondary);
    margin: 0;
    line-height: 1.6;
  }

  .claim-meta {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    padding-left: 102px;
  }

  .confidence-bar-container {
    flex: 1;
    max-width: 250px;
  }

  .confidence-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 4px;
  }

  .confidence-value {
    font-family: var(--font-mono);
    color: var(--text-secondary);
  }

  .confidence-track {
    height: 6px;
    background: var(--bg-tertiary);
    border-radius: 3px;
    overflow: hidden;
  }

  .confidence-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .source-counts {
    display: flex;
    gap: 12px;
  }

  .source-count {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .source-count.supporting {
    color: #4ade80;
  }

  .source-count.contradicting {
    color: #f87171;
  }

  .claim-explanation {
    font-size: 0.85rem;
    color: var(--text-muted);
    padding-left: 102px;
    margin: 0;
    line-height: 1.6;
  }

  @media (max-width: 768px) {
    .claim-main {
      flex-direction: column;
    }

    .claim-meta, .claim-explanation {
      padding-left: 0;
    }

    .claim-meta {
      flex-direction: column;
      gap: 0.75rem;
    }

    .confidence-bar-container {
      max-width: 100%;
    }
  }
</style>
