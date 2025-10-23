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

  // ========== FILTER ==========
// GANTI fungsi lama kamu dengan ini
function filterByRole(btn){
  const role   = btn?.dataset.role || "";
  const pills  = document.querySelectorAll("#role-filter .pill");
  const groups = document.querySelectorAll(".role-group");

  const alreadyActive = btn.classList.contains("is-active");

  // kalau tombol yang sama diklik lagi -> UNFILTER (tampilkan semua)
  if (alreadyActive){
    pills.forEach(b=>{
      b.classList.remove("is-active","border-red-500");
      b.setAttribute("aria-pressed","false");
    });
    groups.forEach(sec=> sec.classList.remove("hidden"));
    return;
  }

  // aktifkan filter baru
  pills.forEach(b=>{
    b.classList.remove("is-active","border-red-500");
    b.setAttribute("aria-pressed","false");
  });
  btn.classList.add("is-active","border-red-500");
  btn.setAttribute("aria-pressed","true");

  groups.forEach(sec=>{
    sec.classList.toggle("hidden", sec.dataset.role !== role);
  });

  document.querySelector(`.role-group[data-role="${role}"]`)
    ?.scrollIntoView({ behavior:"smooth", block:"start" });
}


  // expose biar bisa dipanggil dari HTML onclick
  window.openCreateModal = openCreateModal;
  window.openEditModal   = openEditModal;
  window.deletePlayer    = deletePlayer;
  window.filterByRole    = filterByRole;
  window.hideModal       = hideModal;

  // klik backdrop untuk tutup modal
  modal?.addEventListener("click", (e)=>{
    if (e.target?.hasAttribute?.("data-close")) hideModal();
  });
})();
