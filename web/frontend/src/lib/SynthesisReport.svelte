<script lang="ts">
  interface Props {
    data: Record<string, any>;
    content: string;
  }

  let { data, content }: Props = $props();

  let reportHtml = $derived(markdownToHtml(content || data?.report || data?.synthesis || ''));
  let findings = $derived(data?.key_findings ?? data?.findings ?? []);

  /**
   * Simple markdown-to-HTML converter for the synthesis report.
   * Handles headers, bold, italic, lists, links, blockquotes, and code.
   */
  function markdownToHtml(md: string): string {
    if (!md) return '';
    return md
      // Code blocks
      .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="lang-$1">$2</code></pre>')
      // Inline code
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      // Headers
      .replace(/^#### (.+)$/gm, '<h4>$1</h4>')
      .replace(/^### (.+)$/gm, '<h3>$1</h3>')
      .replace(/^## (.+)$/gm, '<h2>$1</h2>')
      .replace(/^# (.+)$/gm, '<h1>$1</h1>')
      // Bold and italic
      .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      // Blockquotes
      .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
      // Unordered lists
      .replace(/^[-*] (.+)$/gm, '<li>$1</li>')
      // Links
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
      // Horizontal rules
      .replace(/^---$/gm, '<hr />')
      // Line breaks into paragraphs (simplified)
      .replace(/\n\n/g, '</p><p>')
      .replace(/^(?!<[hbluop])/gm, '')
      ;
  }
</script>

<div class="synthesis-report">
  <div class="section-header">
    <span class="section-icon" style="background: rgba(128, 90, 213, 0.15); color: #805ad5;">
      {'\u{1F4DD}'}
    </span>
    <div>
      <h2>Synthesis Report</h2>
      <p class="section-desc">Comprehensive analysis combining all agent findings</p>
    </div>
  </div>

  {#if findings.length > 0}
    <div class="key-findings">
      <h3>Key Findings</h3>
      <div class="findings-list">
        {#each findings as finding, i}
          <div class="finding-item" style="animation-delay: {i * 80}ms;">
            <span class="finding-number">{i + 1}</span>
            <div class="finding-content">
              {#if typeof finding === 'string'}
                <p>{finding}</p>
              {:else}
                <p class="finding-text">{finding.finding || finding.text || JSON.stringify(finding)}</p>
                {#if finding.confidence}
                  <span class="confidence-tag" class:high={finding.confidence === 'HIGH'} class:medium={finding.confidence === 'MEDIUM'} class:low={finding.confidence === 'LOW'}>
                    {finding.confidence} confidence
                  </span>
                {/if}
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <div class="report-body">
    {@html reportHtml}
  </div>
</div>

<style>
  .synthesis-report {
    animation: fadeIn 400ms ease-out;
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 1.5rem;
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

  /* Key Findings */
  .key-findings {
    margin-bottom: 2rem;
    padding: 1.25rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
  }

  .key-findings h3 {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-dim);
    margin-bottom: 1rem;
    font-weight: 700;
  }

  .findings-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .finding-item {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    animation: fadeIn 300ms ease-out backwards;
  }

  .finding-number {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: var(--accent-bg);
    color: var(--accent);
    font-size: 0.8rem;
    font-weight: 700;
    font-family: var(--font-mono);
    flex-shrink: 0;
  }

  .finding-content p {
    font-size: 0.925rem;
    color: var(--text-secondary);
    margin: 0;
    line-height: 1.6;
  }

  .confidence-tag {
    display: inline-block;
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    padding: 2px 8px;
    border-radius: 100px;
    margin-top: 4px;
  }

  .confidence-tag.high {
    background: rgba(34, 197, 94, 0.15);
    color: #4ade80;
  }

  .confidence-tag.medium {
    background: rgba(234, 179, 8, 0.15);
    color: #facc15;
  }

  .confidence-tag.low {
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
  }

  /* Report Body */
  .report-body {
    padding: 1.5rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    line-height: 1.8;
    color: var(--text-secondary);
    font-size: 0.95rem;
  }

  .report-body :global(h1),
  .report-body :global(h2),
  .report-body :global(h3),
  .report-body :global(h4) {
    color: var(--text-primary);
    margin-top: 1.5rem;
    margin-bottom: 0.5rem;
  }

  .report-body :global(h1) { font-size: 1.5rem; }
  .report-body :global(h2) { font-size: 1.3rem; }
  .report-body :global(h3) { font-size: 1.1rem; }

  .report-body :global(p) {
    margin-bottom: 0.75rem;
  }

  .report-body :global(strong) {
    color: var(--text-primary);
    font-weight: 600;
  }

  .report-body :global(blockquote) {
    border-left: 3px solid var(--accent);
    padding: 0.5rem 1rem;
    margin: 0.75rem 0;
    background: var(--accent-bg);
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    font-style: italic;
    color: var(--text-muted);
  }

  .report-body :global(code) {
    font-family: var(--font-mono);
    font-size: 0.85em;
    padding: 2px 6px;
    background: var(--bg-tertiary);
    border-radius: 4px;
    color: var(--accent);
  }

  .report-body :global(pre) {
    padding: 1rem;
    background: var(--bg-primary);
    border-radius: var(--radius-sm);
    overflow-x: auto;
    margin: 0.75rem 0;
  }

  .report-body :global(pre code) {
    padding: 0;
    background: none;
  }

  .report-body :global(li) {
    margin-bottom: 4px;
    padding-left: 4px;
  }

  .report-body :global(hr) {
    border: none;
    border-top: 1px solid var(--border-primary);
    margin: 1.5rem 0;
  }

  .report-body :global(a) {
    color: var(--accent);
    text-decoration: underline;
    text-underline-offset: 2px;
  }
</style>
