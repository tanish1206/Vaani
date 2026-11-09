/**
 * VAANI — Parchi (Medicine Reminders) Workspace Controller
 * Daily Timeline, Dose Status, Snooze, Prescription Records,
 * and Contextual Parchi Agent Integration.
 */

(function () {
  'use strict';

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
        initialGreeting: 'Namaste! Main Parchi assistant hoon. Dawa ka reminder lagana ho ya poochhna ho — boliye, jaise: "Maa ko BP ki goli subah-shaam 5 din".',
        quickPhrases: [
          'Subah ki dawa ka reminder bana do',
          'Meri next medicine kab hai?',
          'Combiflam lunch ke baad lena hai',
          'De di',
          '10 minute baad yaad dilana',
          'Maa ko BP ki goli subah shaam 5 din'
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
    }

    async loadDosesData() {
      try {
        const resp = await fetch('/api/v1/parchi/doses');
        const data = await resp.json();

        this.renderTimeline(data.doses || []);
      } catch (err) {
        console.error('Error loading doses:', err);
      }
    }

    renderTimeline(doses) {
      if (!this.timelineList) return;

      if (doses.length === 0) {
        this.timelineList.innerHTML = `
          <div style="padding: 32px; text-align: center; color: var(--text-muted); background: var(--ice-50); border-radius: var(--radius-sm); border: 1px dashed var(--border);">
            Aaj ke liye koi pending dawa nahi hai. Bolkar ya button se nayi dawa jodein.
          </div>
        `;
        return;
      }

      this.timelineList.innerHTML = doses.map(d => {
        const isDone = d.status === 'done';
        const isPending = d.status === 'pending';
        const timeStr = d.due_at ? d.due_at.split('T')[1].substring(0, 5) : '08:00';

        const foodTag = d.with_food ? `&bull; ${d.with_food} food` : '';

        return `
          <div style="display: flex; justify-content: space-between; align-items: center; background: #FFFFFF; border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 14px 18px; border-left: 4px solid ${isDone ? 'var(--success)' : 'var(--marigold)'};">
            <div>
              <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-weight: 700; color: var(--aubergine); font-size: 15px;">${d.patient_label}: ${d.name}</span>
                <span style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: ${isDone ? 'var(--success)' : 'var(--aubergine)'}; background: ${isDone ? 'rgba(46,125,50,0.1)' : 'var(--marigold-100)'}; padding: 2px 8px; border-radius: var(--radius-pill);">
                  ${d.status}
                </span>
              </div>
              <div style="font-size: 12.5px; color: var(--text-muted); margin-top: 4px;">
                ⏰ Samay: <strong>${timeStr}</strong> ${foodTag} ${d.dose_text ? '&bull; ' + d.dose_text : ''}
              </div>
            </div>

            <div style="display: flex; gap: 8px;">
              ${isPending ? `
                <button class="utility-chip-btn" style="background: var(--aubergine); color: #FFFFFF;" onclick="window.parchiWorkspace.markDone()">
                  ✓ De Di
                </button>
                <button class="utility-chip-btn" onclick="window.parchiWorkspace.snooze(10)">
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

