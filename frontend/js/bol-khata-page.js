/**
 * VAANI — Bol-Khata Dedicated Workspace Controller
 * Customer Ledger Management, Real-time Search, Transaction Modals,
 * WhatsApp Reminder Drafts, and Contextual Bol-Khata Agent Integration.
 */

(function () {
  'use strict';

  class BolKhataWorkspace {
    constructor() {
      this.customers = [];
      this.activeCustomer = null;

      this.initDOMElements();
      this.initAgent();
      this.bindEvents();
      this.loadLedgerData();
    }

    initDOMElements() {
      this.tbody = document.getElementById('khata-customers-tbody');
      this.searchInput = document.getElementById('customer-search-input');
      this.statTotalUdhaar = document.getElementById('stat-total-udhaar');
      this.statTodayCredit = document.getElementById('stat-today-credit');
      this.statTodayPayment = document.getElementById('stat-today-payment');

      // Modals
      this.modalCredit = document.getElementById('modal-add-credit');
      this.modalPayment = document.getElementById('modal-add-payment');
      this.btnOpenCredit = document.getElementById('btn-open-add-credit');
      this.btnOpenPayment = document.getElementById('btn-open-add-payment');
      this.btnCancelCredit = document.getElementById('btn-cancel-credit');
      this.btnCancelPayment = document.getElementById('btn-cancel-payment');
      this.formCredit = document.getElementById('form-add-credit');
      this.formPayment = document.getElementById('form-add-payment');

      // Detail Drawer
      this.detailCard = document.getElementById('customer-detail-card');
      this.detailName = document.getElementById('detail-customer-name');
      this.detailBalance = document.getElementById('detail-customer-balance');
      this.detailEntriesList = document.getElementById('customer-entries-list');
      this.btnCloseDetail = document.getElementById('btn-close-detail');
      this.btnCopyReminder = document.getElementById('btn-copy-reminder');

      // Undo Snackbar
      this.undoSnackbar = document.getElementById('khata-undo-snackbar');
      this.btnTriggerUndo = document.getElementById('btn-trigger-undo');
    }

    initAgent() {
      window.vaaniAgents['khata-agent-container'] = new window.VaaniAgent({
        containerId: 'khata-agent-container',
        moduleId: 'khata',
        moduleTitle: 'Bol-Khata Ledger Agent',
        initialGreeting: 'Namaste! Main Bol-Khata assistant hoon. Dukaan ka hisaab bolkar darj karein ya "+ Udhaar Likhna" se shuru karein.',
        quickPhrases: [
          'Naya khata jodo',
          'Aaj ka hisaab batao',
          'Sabse zyada udhaar kiska hai?',
          'Galat ho gaya, hata do'
        ],
        onActionExecuted: (data) => {
          this.loadLedgerData();
          if (data && data.actions && data.actions.some(a => a.tool === 'add_credit' || a.tool === 'record_payment')) {
            this.showUndoSnackbar();
          }
        }
      });
    }

    bindEvents() {
      // Live search
      this.searchInput.addEventListener('input', () => this.filterCustomers());

      // Modals open/close
      this.btnOpenCredit.addEventListener('click', () => this.modalCredit.classList.add('open'));
      this.btnOpenPayment.addEventListener('click', () => this.modalPayment.classList.add('open'));
      this.btnCancelCredit.addEventListener('click', () => this.modalCredit.classList.remove('open'));
      this.btnCancelPayment.addEventListener('click', () => this.modalPayment.classList.remove('open'));

      // Modals submit: dispatches through existing Python-validated pipeline
      this.formCredit.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('credit-cust-name').value.trim();
        const amt = document.getElementById('credit-amount').value.trim();
        const note = document.getElementById('credit-note').value.trim();
        const query = `${name} ko ${amt} rupaye ka udhaar likh do${note ? ' note ' + note : ''}`;
        this.modalCredit.classList.remove('open');
        this.formCredit.reset();
        await window.vaaniAgents['khata-agent-container'].processQuery(query);
      });

      this.formPayment.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('payment-cust-name').value.trim();
        const amt = document.getElementById('payment-amount').value.trim();
        const query = `${name} ne ${amt} rupaye jama kiye`;
        this.modalPayment.classList.remove('open');
        this.formPayment.reset();
        await window.vaaniAgents['khata-agent-container'].processQuery(query);
      });

      // Detail drawer close
      this.btnCloseDetail.addEventListener('click', () => {
        this.detailCard.style.display = 'none';
        this.activeCustomer = null;
      });

      // WhatsApp reminder copy
      this.btnCopyReminder.addEventListener('click', () => this.copyWhatsAppReminder());

      // Undo button
      this.btnTriggerUndo.addEventListener('click', () => {
        this.undoSnackbar.classList.remove('visible');
        window.vaaniAgents['khata-agent-container'].processQuery('Galat ho gaya, hata do');
      });
    }

    async loadLedgerData() {
      try {
        const [custResp, sumResp] = await Promise.all([
          fetch('/api/v1/khata/customers'),
          fetch('/api/v1/khata/summary')
        ]);
        this.customers = await custResp.json();
        const summary = await sumResp.json();

        // Total Outstanding
        const totalPaise = this.customers.reduce((acc, c) => acc + (c.balance_paise || 0), 0);
        this.statTotalUdhaar.textContent = `₹${(totalPaise / 100).toLocaleString('en-IN')}`;

        if (summary.total_credit_paise !== undefined) {
          this.statTodayCredit.textContent = `₹${(summary.total_credit_paise / 100).toLocaleString('en-IN')}`;
        }
        if (summary.total_payment_paise !== undefined) {
          this.statTodayPayment.textContent = `₹${(summary.total_payment_paise / 100).toLocaleString('en-IN')}`;
        }

        this.renderCustomersTable(this.customers);

        // If detail drawer open, refresh it
        if (this.activeCustomer) {
          this.openCustomerDetail(this.activeCustomer.id);
        }
      } catch (err) {
        console.error('Error loading ledger data:', err);
      }
    }

    renderCustomersTable(customersList) {
      if (!this.tbody) return;

      if (customersList.length === 0) {
        this.tbody.innerHTML = `
          <tr>
            <td colspan="5" style="text-align:center; padding:48px 24px; color:var(--text-muted);">
              <div style="font-size:32px; margin-bottom:12px;">📖</div>
              <div style="font-size:16px; font-weight:700; color:var(--aubergine); margin-bottom:6px;">No customers added yet.</div>
              <div style="font-size:13px; color:var(--text-muted);">Koi grahak nahi mila. Boliye ya "+ Udhaar Likhna" se naya khata shuru karein.</div>
            </td>
          </tr>
        `;
        return;
      }

      this.tbody.innerHTML = customersList.map((c, idx) => {
        const balanceRupees = c.balance_paise / 100;
        const isCleared = balanceRupees <= 0;
        const statusBadge = isCleared 
          ? `<span style="font-size:11px; font-weight:700; color:var(--success); background:rgba(46,125,50,0.1); padding:2px 8px; border-radius:var(--radius-pill);">Chukta</span>`
          : `<span style="font-size:11px; font-weight:700; color:var(--marigold-600); background:var(--marigold-100); padding:2px 8px; border-radius:var(--radius-pill);">Udhaar Baaki</span>`;

        return `
          <tr style="cursor: pointer; transition: background var(--dur-fast);" onclick="window.khataWorkspace.openCustomerDetail(${c.id})">
            <td><strong>${idx + 1}</strong></td>
            <td>
              <div style="font-weight:700; color:var(--aubergine); font-size:15px;">${c.name}</div>
              <div style="font-size:12px; color:var(--text-muted);">${c.name_roman}</div>
            </td>
            <td>
              <span class="customer-balance-chip" style="background:${isCleared ? 'var(--ice-50)' : 'var(--marigold)'}; color:var(--aubergine);">
                &#8377;${balanceRupees.toLocaleString('en-IN')}
              </span>
            </td>
            <td>${statusBadge}</td>
            <td style="text-align: right;">
              <button class="utility-chip-btn" onclick="event.stopPropagation(); window.khataWorkspace.openCustomerDetail(${c.id})">
                Tafseel &rarr;
              </button>
            </td>
          </tr>
        `;
      }).join('');
    }

    filterCustomers() {
      const q = this.searchInput.value.toLowerCase().trim();
      const filtered = this.customers.filter(c => 
        c.name.toLowerCase().includes(q) || 
        c.name_roman.toLowerCase().includes(q)
      );
      this.renderCustomersTable(filtered);
    }

    async openCustomerDetail(customerId) {
      const cust = this.customers.find(c => c.id === customerId);
      if (!cust) return;
      this.activeCustomer = cust;

      this.detailName.textContent = `${cust.name} (${cust.name_roman})`;
      this.detailBalance.textContent = `Total Baaki: ₹${(cust.balance_paise / 100).toLocaleString('en-IN')}`;
      this.detailCard.style.display = 'block';

      try {
        const resp = await fetch(`/api/v1/khata/customer/${customerId}/entries`);
        const entries = await resp.json();

        if (entries.length === 0) {
          this.detailEntriesList.innerHTML = `<div style="color:var(--text-muted); font-size:13px;">Koi purana hisaab nahi hai.</div>`;
        } else {
          this.detailEntriesList.innerHTML = entries.map(e => `
            <div style="display:flex; justify-content:space-between; align-items:center; background:var(--ice-50); padding:10px 14px; border-radius:var(--radius-sm); border-left:3px solid ${e.kind === 'CREDIT' ? 'var(--danger)' : 'var(--success)'};">
              <div>
                <span style="font-weight:700; font-size:13.5px; color:${e.kind === 'CREDIT' ? 'var(--danger)' : 'var(--success)'};">
                  ${e.kind === 'CREDIT' ? '+ ₹' : '− ₹'}${(e.amount_paise / 100).toLocaleString('en-IN')} (${e.kind})
                </span>
                <span style="font-size:12px; color:var(--text-muted); margin-left:8px;">${e.note || ''}</span>
              </div>
              <span style="font-size:11px; color:var(--text-subtle);">${e.created_at ? e.created_at.split('T')[0] : ''}</span>
            </div>
          `).join('');
        }

        // Scroll to detail drawer
        this.detailCard.scrollIntoView({ behavior: 'smooth' });
      } catch (err) {
        console.error('Error fetching entries:', err);
      }
    }

    copyWhatsAppReminder() {
      if (!this.activeCustomer) return;
      const cust = this.activeCustomer;
      const amt = (cust.balance_paise / 100).toLocaleString('en-IN');
      const text = `Namaste ${cust.name} ji, aapka dukaan par ₹${amt} baaki hai. Jab suvidha ho, kripya bhej dein. Dhanyavaad.`;

      navigator.clipboard.writeText(text).then(() => {
        alert(`WhatsApp reminder message copy ho gaya!\n\n"${text}"`);
      }).catch(() => {
        alert(`Message:\n${text}`);
      });
    }

    showUndoSnackbar() {
      if (!this.undoSnackbar) return;
      this.undoSnackbar.classList.add('visible');
      setTimeout(() => {
        this.undoSnackbar.classList.remove('visible');
      }, 8000);
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    window.khataWorkspace = new BolKhataWorkspace();
  });
})();

