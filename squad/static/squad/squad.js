// static/squad/squad.js
(function () {
  const modal = document.getElementById("modal");
  const modalBody = document.getElementById("modal-body");

  function getCookie(name){
    const m = document.cookie.match('(^|;)\\s*'+name+'\\s*=\\s*([^;]+)');
    return m ? m.pop() : '';
  }
  function showModal(){ modal?.classList.remove("hidden"); }
  function hideModal(){ modal?.classList.add("hidden"); if (modalBody) modalBody.innerHTML = ""; }

  async function fetchJSON(url, opts = {}){
    const res = await fetch(url, opts);
    const ct = res.headers.get("content-type") || "";
    const body = ct.includes("application/json") ? await res.json() : await res.text();
    if (!res.ok) throw new Error((body && body.detail) || body || ("Error " + res.status));
    return body;
  }

  // ========== CREATE ==========
  async function openCreateModal(btn){
    try{
      const formUrl = btn?.dataset.formUrl;
      if (!formUrl) return alert("Form URL tidak ditemukan.");
      const data = await fetchJSON(formUrl, {
        headers: { "X-Requested-With":"XMLHttpRequest", "Accept":"application/json" }
      });
      modalBody.innerHTML = data.html || data;   // render partial form
      showModal();

      // intercept submit biasa -> AJAX
      const form = modalBody.querySelector("form");
      form?.addEventListener("submit", async (e)=>{
        e.preventDefault();
        try{
          const createUrl = btn?.dataset.url;
          if (!createUrl) throw new Error("Create URL tidak ditemukan.");
          const payload = await fetchJSON(createUrl, {
            method: "POST",
            headers: { "X-CSRFToken": getCookie("csrftoken"), "X-Requested-With":"XMLHttpRequest", "Accept":"application/json" },
            body: new FormData(form)
          });
          hideModal();

          const group = document.querySelector(`.role-group[data-role="${payload.role_tag}"] .cards`);
          if (group && payload.html){
            group.insertAdjacentHTML("afterbegin", payload.html);
            group.firstElementChild?.scrollIntoView({ behavior:"smooth", block:"nearest" });
          } else {
            location.reload();
          }
        }catch(err){ alert(err.message||err); }
      }, { once:true });

    }catch(err){ alert(err.message||err); }
  }

  // ========== EDIT ==========
  async function openEditModal(btn){
    try{
      const url = btn?.dataset.url;
      if (!url) return alert("Edit URL tidak ditemukan.");
      const data = await fetchJSON(url, {
        headers: { "X-Requested-With":"XMLHttpRequest", "Accept":"application/json" }
      });
      modalBody.innerHTML = data.html || data;
      showModal();

      const form = modalBody.querySelector("form");
      form?.addEventListener("submit", async (e)=>{
        e.preventDefault();
        try{
          const payload = await fetchJSON(url, {
            method: "POST",
            headers: { "X-CSRFToken": getCookie("csrftoken"), "X-Requested-With":"XMLHttpRequest", "Accept":"application/json" },
            body: new FormData(form)
          });
          hideModal();

          const old = document.getElementById("player-card-"+payload.id);
          if (payload.moved){
            old?.remove();
            const group = document.querySelector(`.role-group[data-role="${payload.role_tag}"] .cards`);
            if (group && payload.html){
              group.insertAdjacentHTML("afterbegin", payload.html);
              group.firstElementChild?.scrollIntoView({ behavior:"smooth", block:"nearest" });
            } else {
              location.reload();
            }
          } else {
            if (old && payload.html){
              old.outerHTML = payload.html;
              document.getElementById("player-card-"+payload.id)
                ?.scrollIntoView({ behavior:"smooth", block:"nearest" });
            } else {
              location.reload();
            }
          }
        }catch(err){ alert(err.message||err); }
      }, { once:true });

    }catch(err){ alert(err.message||err); }
  }

  // ========== DELETE ==========
  async function deletePlayer(btn){
    const url = btn?.dataset.url;
    if (!url) return alert("Delete URL tidak ditemukan.");
    if (!confirm("Hapus pemain ini?")) return;

    try{
      const res = await fetchJSON(url, {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken"), "X-Requested-With":"XMLHttpRequest", "Accept":"application/json" }
      });
      if (res.ok || res.id){
        btn.closest("[id^='player-card-']")?.remove();
      }
    }catch(err){ alert(err.message||err); }
  }

// ========== ROLE FILTER  ==========
const ACTIVE_PILL   = ['text-red-700', 'border-red-600', 'font-semibold'];
const INACTIVE_PILL = ['text-gray-500', 'border-gray-200', 'font-normal'];

let currentRole = null;

function filterByRole(btn) {
  const role = btn?.dataset?.role;
  if (!role) return;

  const pills = document.querySelectorAll('#role-filter .pill');

  // Toggle: klik role yang sama -> unfilter
  if (currentRole === role) {
    currentRole = null;
    pills.forEach(p => setPillState(p, false));
    showAllContent();
    return;
  }

  // Set filter baru
  currentRole = role;
  pills.forEach(p => setPillState(p, p === btn));
  applyFilterToContent(role);
}

function setPillState(pill, active) {
  pill.classList.toggle('is-active', active); // untuk group-[.is-active]:scale-x-100 (underline)
  ACTIVE_PILL.forEach(c => pill.classList.toggle(c, active));
  INACTIVE_PILL.forEach(c => pill.classList.toggle(c, !active));
  pill.setAttribute('aria-pressed', active ? 'true' : 'false');
}

function applyFilterToContent(role) {
  // Prioritas 1: grup (section) per role
  const groups = document.querySelectorAll('.role-group[data-role]');
  if (groups.length) {
    groups.forEach(g => g.classList.toggle('hidden', g.dataset.role !== role));
    document.querySelector(`.role-group[data-role="${role}"]`)
      ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    return;
  }

  // Fallback: kartu per item (player-card, dst.)
  const items =
    document.querySelectorAll('[data-role].player-card, [data-role].card, [data-role].player')
      .length
      ? document.querySelectorAll('[data-role].player-card, [data-role].card, [data-role].player')
      : document.querySelectorAll('[data-role]');

  items.forEach(el => el.classList.toggle('hidden', el.dataset.role !== role));
  document.querySelector('[data-role]:not(.hidden)')
    ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showAllContent() {
  const groups = document.querySelectorAll('.role-group[data-role]');
  const items = groups.length ? groups : document.querySelectorAll('[data-role]');
  items.forEach(el => el.classList.remove('hidden'));
}
// =========================================



  // expose biar bisa dipanggil dari HTML onclick
  window.openCreateModal = openCreateModal;
  window.openEditModal   = openEditModal;
  window.deletePlayer    = deletePlayer;
  window.filterByRole    = filterByRole; // <-- Sekarang menggunakan fungsi baru
  window.hideModal       = hideModal;

  // klik backdrop untuk tutup modal
  modal?.addEventListener("click", (e)=>{
    if (e.target?.hasAttribute?.("data-close")) hideModal();
  });
})();