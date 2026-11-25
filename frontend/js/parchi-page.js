/**
 * VAANI — Parchi (Medicine Reminders) Workspace Controller
 * Daily Timeline, Dose Status, Snooze, Prescription Records,
 * and Contextual Parchi Agent Integration.
 */

(function () {
  'use strict';

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  class ParchiWorkspace {
    constructor() {
      this.initDOMElements();
      this.initAgent();
      this.bindEvents();
      this.loadDosesData();
    }

    initDOMElements() {
      this.timelineList = document.getElementById('parchi-timeline-list');
      this.prescriptionsList = document.getElementById('active-prescriptions-list');
      this.btnRefresh = document.getElementById('btn-refresh-doses');
      this.btnQuickDone = document.getElementById('btn-quick-dose-done');

      // Modal
      this.modalPresc = document.getElementById('modal-add-presc');
      this.btnOpenPresc = document.getElementById('btn-open-add-prescription');
      this.btnCancelPresc = document.getElementById('btn-cancel-presc');
      this.formPresc = document.getElementById('form-add-presc');
    }

    initAgent() {
      window.vaaniAgents['parchi-agent-container'] = new window.VaaniAgent({
        containerId: 'parchi-agent-container',
        moduleId: 'parchi',
        moduleTitle: 'Parchi Medicine Agent',
        initialGreeting: 'Namaste! Main Parchi assistant hoon. Dawa ka reminder lagana ho ya poochhna ho — bas boliye, jaise: "Dawa ka reminder bana do".',
        quickPhrases: [
          'Dawa ka reminder bana do',
          'Meri next medicine kab hai?',
          'De di',
          '10 minute baad yaad dilana'
        ],
        onActionExecuted: () => {
          this.loadDosesData();
        }
      });
    }

    bindEvents() {
      this.btnRefresh.addEventListener('click', () => this.loadDosesData());

      // Quick done button
      this.btnQuickDone.addEventListener('click', () => {
        window.vaaniAgents['parchi-agent-container'].processQuery('De di');
      });

      // Modal open/close
      this.btnOpenPresc.addEventListener('click', () => this.modalPresc.classList.add('open'));
      this.btnCancelPresc.addEventListener('click', () => this.modalPresc.classList.remove('open'));

      // Form submit
      this.formPresc.addEventListener('submit', async (e) => {
        e.preventDefault();
        const patient = document.getElementById('presc-patient').value.trim();
        const medName = document.getElementById('presc-med-name').value.trim();
        const food = document.getElementById('presc-food').value;
        const days = document.getElementById('presc-days').value.trim();

        const slotCheckboxes = document.querySelectorAll('input[name="slots"]:checked');
        const slots = Array.from(slotCheckboxes).map(cb => cb.value);

        let timesText = 'subah shaam';
        if (slots.length === 3) timesText = 'din mein teen baar';
        else if (slots.length === 1) timesText = slots[0];

        const query = `${patient} ko ${medName} ${timesText} ${days} din, khane ke ${food === 'before' ? 'pehle' : 'baad'}`;
        
        this.modalPresc.classList.remove('open');
        this.formPresc.reset();
        await window.vaaniAgents['parchi-agent-container'].processQuery(query);
      });

      if (this.timelineList) {
        this.timelineList.addEventListener('click', (e) => {
          const btn = e.target.closest('button[data-parchi-action]');
          if (!btn) return;
          const action = btn.getAttribute('data-parchi-action');
          if (action === 'done') this.markDone();
          else if (action === 'snooze') this.snooze(10);
        });
      }
    }

    async loadDosesData() {
      try {
        const resp = await fetch('/api/v1/parchi/doses');
        const data = await resp.json();
        const doses = data.doses || [];
        this.renderTimeline(doses);
        this.renderActivePrescriptions(doses);
      } catch (err) {
        console.error('Error loading doses:', err);
      }
    }

    renderActivePrescriptions(doses) {
      if (!this.prescriptionsList) return;
      if (doses.length === 0) {
        this.prescriptionsList.innerHTML = `
          <div style="grid-column: 1 / -1; padding: 24px; text-align: center; color: var(--text-muted); font-size: 13px;">
            Koi active prescription nahi hai.
          </div>
        `;
        return;
      }

      const grouped = new Map();
      doses.forEach(d => {
        const key = `${d.patient_label || 'Self'}::${d.name}`;
        if (!grouped.has(key)) {
          grouped.set(key, {
            patient: d.patient_label || 'Self',
            medicine: d.name,
            withFood: d.with_food,
            durationDays: d.duration_days || 5,
            doseText: d.dose_text,
            slots: []
          });
        }
        const t = d.due_at && d.due_at.includes('T') ? d.due_at.split('T')[1].substring(0, 5) : '08:00';
        grouped.get(key).slots.push(t);
      });

      this.prescriptionsList.innerHTML = Array.from(grouped.values()).map(item => `
        <div style="background: var(--ice-50); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 14px 16px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-weight: 700; color: var(--aubergine); font-size: 14.5px;">${escapeHtml(item.patient)}</span>
            <span style="font-size: 11px; font-weight: 700; color: var(--marigold-600); background: var(--marigold-100); padding: 2px 8px; border-radius: var(--radius-pill);">${Number(item.durationDays)} Days</span>
          </div>
          <div style="font-weight: 600; color: var(--aubergine); margin-bottom: 4px;">${escapeHtml(item.medicine)}</div>
          <div style="font-size: 12px; color: var(--text-muted);">
            ⏰ ${escapeHtml(item.slots.join(', '))} ${item.withFood ? `• ${escapeHtml(item.withFood)} food` : ''}
            ${item.doseText ? `• ${escapeHtml(item.doseText)}` : ''}
          </div>
        </div>
      `).join('');
    }

    renderTimeline(doses) {
      if (!this.timelineList) return;

      if (doses.length === 0) {
        this.timelineList.innerHTML = `
          <div style="padding: 44px 24px; text-align: center; color: var(--text-muted); background: var(--ice-50); border-radius: var(--radius-sm); border: 1.5px dashed var(--border);">
            <div style="font-size:30px; margin-bottom:10px;">💊</div>
            <div style="font-size: 16px; font-weight: 700; color: var(--aubergine); margin-bottom: 4px;">No prescriptions added yet.</div>
            <div style="font-size: 13px; color: var(--text-muted);">Koi parchi ya dawa darj nahi hai. Bolkar ya '+ Nayi Parchi' se shuru karein.</div>
          </div>
        `;
        return;
      }

      this.timelineList.innerHTML = doses.map(d => {
        const isDone = d.status === 'done';
        const isPending = d.status === 'pending';
        const timeStr = (d.due_at && d.due_at.includes('T')) ? d.due_at.split('T')[1].substring(0, 5) : '08:00';
        const foodTag = d.with_food ? `&bull; ${escapeHtml(d.with_food)} food` : '';

        return `
          <div style="display: flex; justify-content: space-between; align-items: center; background: #FFFFFF; border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 14px 18px; border-left: 4px solid ${isDone ? 'var(--success)' : 'var(--marigold)'};">
            <div>
              <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-weight: 700; color: var(--aubergine); font-size: 15px;">${escapeHtml(d.patient_label)}: ${escapeHtml(d.name)}</span>
                <span style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: ${isDone ? 'var(--success)' : 'var(--aubergine)'}; background: ${isDone ? 'rgba(46,125,50,0.1)' : 'var(--marigold-100)'}; padding: 2px 8px; border-radius: var(--radius-pill);">
                  ${escapeHtml(d.status)}
                </span>
              </div>
              <div style="font-size: 12.5px; color: var(--text-muted); margin-top: 4px;">
                ⏰ Samay: <strong>${escapeHtml(timeStr)}</strong> ${foodTag} ${d.dose_text ? '&bull; ' + escapeHtml(d.dose_text) : ''}
              </div>
            </div>

            <div style="display: flex; gap: 8px;">
              ${isPending ? `
                <button class="utility-chip-btn" type="button" data-parchi-action="done" style="background: var(--aubergine); color: #FFFFFF;">
                  ✓ De Di
                </button>
                <button class="utility-chip-btn" type="button" data-parchi-action="snooze">
                  ⏰ 10m Snooze
                </button>
              ` : `
                <span style="font-size: 12px; color: var(--success); font-weight: 600;">✓ Completed</span>
              `}
            </div>
          </div>
        `;
      }).join('');
    }

    async markDone() {
      await window.vaaniAgents['parchi-agent-container'].processQuery('De di');
    }

    async snooze(mins = 10) {
      await window.vaaniAgents['parchi-agent-container'].processQuery(`${mins} minute baad yaad dilana`);
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    window.parchiWorkspace = new ParchiWorkspace();
  });
})();

