/**
 * VAANI — Sensex Awaaz Workspace Controller
 * Live Market Quotes, Candlestick Movement Spectrum, Watchlist Management,
 * Spoken Market Briefings, and Contextual Sensex Agent Integration.
 */

(function () {
  'use strict';

  class SensexWorkspace {
    constructor() {
      this.latestBriefText = '';
      this.initDOMElements();
      this.initAgent();
      this.bindEvents();
      this.loadMarketData();
    }

    initDOMElements() {
      this.sensexPrice = document.getElementById('page-sensex-price');
      this.sensexDelta = document.getElementById('page-sensex-delta');
      this.niftyPrice = document.getElementById('page-nifty-price');
      this.niftyDelta = document.getElementById('page-nifty-delta');
      this.freshnessBadge = document.getElementById('freshness-badge');
      this.briefTextEl = document.getElementById('spoken-brief-text');
      this.watchlistTbody = document.getElementById('page-watchlist-tbody');
      this.chartTimestamp = document.getElementById('chart-timestamp');

      this.btnPlayBrief = document.getElementById('btn-play-brief');
      this.btnReplayBrief = document.getElementById('btn-replay-brief');
      this.btnRefresh = document.getElementById('btn-refresh-market');

      // Modal
      this.modalStock = document.getElementById('modal-add-stock');
      this.btnOpenAddStock = document.getElementById('btn-open-add-stock');
      this.btnCancelStock = document.getElementById('btn-cancel-stock');
      this.formStock = document.getElementById('form-add-stock');
    }

    initAgent() {
      window.vaaniAgents['bazaar-agent-container'] = new window.VaaniAgent({
        containerId: 'bazaar-agent-container',
        moduleId: 'bazaar',
        moduleTitle: 'Sensex Awaaz Market Agent',
        initialGreeting: 'Namaste! Main Sensex Awaaz assistant hoon. Sensex, Nifty ya share bazaar ka haal poochhiye, jaise: "Sensex ka aaj ka haal batao".',
        quickPhrases: [
          'Sensex ka aaj ka haal batao',
          'Nifty mein kitna change hua?',
          'Reliance ka market update batao',
          'Watchlist mein TCS jodo',
          'Kya Reliance kharidun?'
        ],
        onActionExecuted: () => {
          this.loadMarketData();
        }
      });
    }

    bindEvents() {
      this.btnRefresh.addEventListener('click', () => this.loadMarketData());

      this.btnPlayBrief.addEventListener('click', () => this.playSpokenBrief());
      this.btnReplayBrief.addEventListener('click', () => this.playSpokenBrief());

      // Modal
      this.btnOpenAddStock.addEventListener('click', () => this.modalStock.classList.add('open'));
      this.btnCancelStock.addEventListener('click', () => this.modalStock.classList.remove('open'));

      this.formStock.addEventListener('submit', async (e) => {
        e.preventDefault();
        const symbol = document.getElementById('stock-symbol-input').value.trim();
        this.modalStock.classList.remove('open');
        this.formStock.reset();
        await window.vaaniAgents['bazaar-agent-container'].processQuery(`Watchlist mein ${symbol} jodo`);
      });
    }

    async loadMarketData() {
      try {
        const resp = await fetch('/api/v1/bazaar/snapshot');
        const data = await resp.json();

        // Freshness Badge
        if (this.freshnessBadge) {
          if (data.is_sample) {
            this.freshnessBadge.textContent = '🟡 Sample / Demo Data (Offline)';
            this.freshnessBadge.style.background = 'var(--marigold-100)';
            this.freshnessBadge.style.color = 'var(--aubergine)';
          } else if (data.freshness === 'Live') {
            this.freshnessBadge.textContent = '🟢 Live Market Feed';
            this.freshnessBadge.style.background = 'rgba(46, 125, 50, 0.12)';
            this.freshnessBadge.style.color = 'var(--success)';
          } else {
            this.freshnessBadge.textContent = '⚪ Cached Market Snapshot';
          }
        }

        // Indices
        if (data.sensex) {
          this.sensexPrice.textContent = data.sensex.price ? data.sensex.price.toLocaleString('en-IN') : '83,410.20';
          const chg = data.sensex.change_abs || 0;
          const pct = data.sensex.change_pct || 0;
          this.sensexDelta.innerHTML = `${chg >= 0 ? '&#9650; +' : '&#9660; '}${chg} (${pct}%)`;
          this.sensexDelta.style.color = chg >= 0 ? 'var(--success)' : 'var(--danger)';
        }

        if (data.nifty) {
          this.niftyPrice.textContent = data.nifty.price ? data.nifty.price.toLocaleString('en-IN') : '25,480.60';
          const chg = data.nifty.change_abs || 0;
          const pct = data.nifty.change_pct || 0;
          this.niftyDelta.innerHTML = `${chg >= 0 ? '&#9650; +' : '&#9660; '}${chg} (${pct}%)`;
          this.niftyDelta.style.color = chg >= 0 ? 'var(--success)' : 'var(--danger)';
        }

        // Brief text
        if (data.reply_text) {
          this.latestBriefText = data.reply_text;
          this.briefTextEl.textContent = `"${data.reply_text}"`;
        }

        // Watchlist Table
        this.renderWatchlist(data.quotes || []);

        if (data.as_of && this.chartTimestamp) {
          const dateStr = data.as_of.split('T')[0];
          const timeStr = data.as_of.split('T')[1].substring(0, 5);
          this.chartTimestamp.textContent = `As Of: ${dateStr} ${timeStr} UTC`;
        }
      } catch (err) {
        console.error('Error loading market data:', err);
      }
    }

    renderWatchlist(quotes) {
      if (!this.watchlistTbody) return;

      if (quotes.length === 0) {
        this.watchlistTbody.innerHTML = `
          <tr>
            <td colspan="6" style="text-align:center; padding:44px 24px; color:var(--text-muted);">
              <div style="font-size:28px; margin-bottom:8px;">📊</div>
              <div style="font-size:15px; font-weight:700; color:var(--aubergine); margin-bottom:4px;">No watchlist created yet.</div>
              <div style="font-size:13px; color:var(--text-muted);">Watchlist khali hai. Bolkar ya "+ Stock Jodein" se naya share jodein.</div>
            </td>
          </tr>
        `;
        return;
      }

      this.watchlistTbody.innerHTML = quotes.map(q => {
        const chg = q.change_abs || 0;
        const isUp = chg >= 0;
        const timePart = q.as_of ? q.as_of.split('T')[1].substring(0, 5) : '15:30';

        return `
          <tr>
            <td><strong>${q.label}</strong></td>
            <td style="font-family: var(--font-mono); font-size: 12px; color: var(--text-muted);">${q.symbol}</td>
            <td style="font-weight: 700; font-variant-numeric: tabular-nums;">&#8377;${q.price ? q.price.toLocaleString('en-IN') : '--'}</td>
            <td style="color: ${isUp ? 'var(--success)' : 'var(--danger)'}; font-weight: 700;">
              ${isUp ? '&#9650; +' : '&#9660; '}${chg} (${q.change_pct || 0}%)
            </td>
            <td style="font-size: 12px; color: var(--text-subtle);">${timePart}</td>
            <td>
              <span style="font-size: 11px; padding: 2px 8px; border-radius: var(--radius-pill); background: var(--ice-50); border: 1px solid var(--border);">
                ${q.is_sample ? 'sample' : (q.source || 'cache')}
              </span>
            </td>
          </tr>
        `;
      }).join('');
    }

    playSpokenBrief() {
      if (!this.latestBriefText) return;
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utt = new SpeechSynthesisUtterance(this.latestBriefText);
        utt.lang = 'hi-IN';
        utt.rate = 0.95;
        window.speechSynthesis.speak(utt);
      }
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    window.sensexWorkspace = new SensexWorkspace();
  });
})();

