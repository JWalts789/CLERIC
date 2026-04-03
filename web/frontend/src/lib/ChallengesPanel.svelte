<script lang="ts">
  interface Props {
    data: Record<string, any>;
  }

  let { data }: Props = $props();

  let challenges = $derived(data?.challenges ?? data?.arguments ?? []);

  function severityConfig(severity: string): { icon: string; color: string; class: string } {
    switch (severity?.toUpperCase()) {
      case 'HIGH': return { icon: '\u{1F534}', color: '#ef4444', class: 'severity-high' };
      case 'MEDIUM': return { icon: '\u{1F7E1}', color: '#eab308', class: 'severity-medium' };
      case 'LOW': return { icon: '\u{1F7E2}', color: '#22c55e', class: 'severity-low' };
      default: return { icon: '\u{1F7E1}', color: '#eab308', class: 'severity-medium' };
    }
  }
</script>

<div class="challenges-panel">
  <div class="section-header">
    <span class="section-icon" style="background: rgba(214, 158, 46, 0.15); color: #d69e2e;">
      {'\u{1F608}'}
    </span>
    <div>
      <h2>Devil's Advocate</h2>
      <p class="section-desc">{challenges.length} challenges raised against the findings</p>
    </div>
  </div>

  <div class="challenges-grid">
    {#each challenges as challenge, i}
      {@const sev = severityConfig(challenge.severity)}
      <div class="challenge-card card" style="animation-delay: {i * 80}ms;">
        <div class="challenge-header">
          <div class="severity-indicator">
            <span class="severity-dot" style="background: {sev.color};"></span>
            <span class="severity-label" style="color: {sev.color};">
              {challenge.severity || 'MEDIUM'}
            </span>
          </div>
          {#if challenge.type}
            <span class="challenge-type">{challenge.type}</span>
          {/if}
        </div>

        <p class="challenge-text">
          {challenge.challenge || challenge.argument || challenge.text || JSON.stringify(challenge)}
        </p>

        {#if challenge.recommendation}
          <div class="recommendation">
            <span class="rec-label">Recommendation:</span>
            <p>{challenge.recommendation}</p>
          </div>
        {/if}
      </div>
    {/each}
  </div>
</div>

<style>
  .challenges-panel {
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

  .challenges-grid {
    display: grid;
    gap: 1rem;
  }

  .challenge-card {
    animation: fadeIn 300ms ease-out backwards;
    border-left: 3px solid var(--border-primary);
  }

  .challenge-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 0.5rem;
  }

  .severity-indicator {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .severity-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .severity-label {
    font-size: 0.7rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  .challenge-type {
    font-size: 0.75rem;
    padding: 2px 10px;
    background: var(--bg-tertiary);
    border-radius: 100px;
    color: var(--text-muted);
    font-weight: 500;
  }

  .challenge-text {
    font-size: 0.925rem;
    line-height: 1.6;
    color: var(--text-secondary);
    margin: 0 0 0.5rem 0;
  }

  .recommendation {
    padding: 0.75rem;
    background: var(--bg-tertiary);
    border-radius: var(--radius-sm);
  }

  .rec-label {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-dim);
    display: block;
    margin-bottom: 4px;
  }

  .recommendation p {
    font-size: 0.85rem;
    margin: 0;
    color: var(--text-muted);
  }
</style>
