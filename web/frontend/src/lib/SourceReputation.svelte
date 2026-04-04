<script lang="ts">
  import { fetchReputation, type ReputationDomain, type ReputationSummary } from './api';

  let summary = $state<ReputationSummary | null>(null);
  let domains = $state<ReputationDomain[]>([]);
  let loading = $state(true);
  let error = $state('');

  async function load() {
    loading = true;
    error = '';
    try {
      const res = await fetchReputation();
      summary = res.summary;
      domains = res.top_domains;
    } catch {
      error = 'Could not load reputation data.';
    } finally {
      loading = false;
    }
  }

  function scoreColor(score: number): string {
    if (score >= 0.7) return 'var(--color-success)';
    if (score >= 0.4) return 'var(--color-warning)';
    return 'var(--color-error)';
  }

  function scoreBg(score: number): string {
    if (score >= 0.7) return 'rgba(110, 231, 183, 0.15)';
    if (score >= 0.4) return 'rgba(251, 191, 36, 0.15)';
    return 'rgba(248, 113, 113, 0.15)';
  }

  function scoreLabel(score: number): string {
    if (score >= 0.8) return 'High';
    if (score >= 0.6) return 'Good';
    if (score >= 0.4) return 'Mixed';
    if (score >= 0.2) return 'Low';
    return 'Poor';
  }

  $effect(() => {
    load();
  });
</script>

{#if loading}
  <div class="rep-loading">
    <div class="rep-spinner"></div>
  </div>
{:else if error}
  <!-- silently hide if no data -->
{:else if summary && summary.total_domains > 0}
  <div class="rep-container">
    <div class="rep-header">
      <h3 class="rep-title">Source Reputation</h3>
      <div class="rep-stats">
        <span class="rep-stat">{summary.total_domains} domains</span>
        <span class="rep-stat-sep"></span>
        <span class="rep-stat">{summary.total_runs} runs</span>
        <span class="rep-stat-sep"></span>
        <span class="rep-stat" style="color: {scoreColor(summary.avg_credibility)}">
          avg {(summary.avg_credibility * 100).toFixed(0)}%
        </span>
      </div>
    </div>

    <div class="rep-table-wrap">
      <table class="rep-table">
        <thead>
          <tr>
            <th class="th-domain">Domain</th>
            <th class="th-score">Credibility</th>
            <th class="th-num">Cited</th>
            <th class="th-num">Verified</th>
            <th class="th-num">Disputed</th>
            <th class="th-num">False</th>
          </tr>
        </thead>
        <tbody>
          {#each domains as d (d.domain)}
            <tr class="rep-row">
              <td class="td-domain">{d.domain}</td>
              <td class="td-score">
                <div class="score-bar-bg">
                  <div
                    class="score-bar-fill"
                    style="width: {d.credibility_score * 100}%; background: {scoreColor(d.credibility_score)}"
                  ></div>
                </div>
                <span class="score-label" style="color: {scoreColor(d.credibility_score)}">
                  {(d.credibility_score * 100).toFixed(0)}%
                </span>
              </td>
              <td class="td-num">{d.cited_count}</td>
              <td class="td-num td-verified">{d.verified_claims}</td>
              <td class="td-num td-disputed">{d.disputed_claims}</td>
              <td class="td-num td-false">{d.false_claims}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
{/if}

<style>
  .rep-container {
    width: 100%;
  }

  .rep-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.75rem;
    flex-wrap: wrap;
    gap: 8px;
  }

  .rep-title {
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .rep-stats {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .rep-stat {
    font-size: 0.72rem;
    color: var(--text-dim);
    font-weight: 500;
  }

  .rep-stat-sep {
    width: 3px;
    height: 3px;
    border-radius: 50%;
    background: var(--text-dim);
    opacity: 0.5;
  }

  .rep-table-wrap {
    overflow-x: auto;
    max-height: 300px;
    overflow-y: auto;
  }

  .rep-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8rem;
  }

  .rep-table thead {
    position: sticky;
    top: 0;
    z-index: 1;
  }

  .rep-table th {
    text-align: left;
    padding: 6px 8px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-dim);
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-primary);
  }

  .th-num {
    text-align: center !important;
    width: 60px;
  }

  .th-score {
    width: 140px;
  }

  .rep-row {
    transition: background var(--transition-fast);
  }

  .rep-row:hover {
    background: rgba(110, 231, 183, 0.04);
  }

  .rep-table td {
    padding: 5px 8px;
    border-bottom: 1px solid rgba(30, 41, 59, 0.5);
    vertical-align: middle;
  }

  .td-domain {
    font-family: var(--font-mono);
    font-size: 0.78rem;
    color: var(--text-primary);
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .td-score {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .score-bar-bg {
    flex: 1;
    height: 6px;
    background: rgba(30, 41, 59, 0.8);
    border-radius: 3px;
    overflow: hidden;
  }

  .score-bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width var(--transition-base);
  }

  .score-label {
    font-size: 0.72rem;
    font-weight: 700;
    font-family: var(--font-mono);
    min-width: 32px;
    text-align: right;
  }

  .td-num {
    text-align: center;
    font-family: var(--font-mono);
    font-size: 0.78rem;
    color: var(--text-secondary);
  }

  .td-verified {
    color: var(--color-success);
  }

  .td-disputed {
    color: var(--color-warning);
  }

  .td-false {
    color: var(--color-error);
  }

  .rep-loading {
    display: flex;
    justify-content: center;
    padding: 1rem 0;
  }

  .rep-spinner {
    width: 20px;
    height: 20px;
    border: 2px solid var(--border-primary);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }
</style>
