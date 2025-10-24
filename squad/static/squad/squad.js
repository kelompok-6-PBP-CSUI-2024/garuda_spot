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
  // Kelas-kelas styling dari jawaban sebelumnya
  const activeClasses = ['border-red-700', 'font-semibold', 'text-gray-900'];
  const inactiveClasses = ['border-transparent', 'font-normal', 'text-gray-500', 'hover:border-gray-300', 'hover:text-gray-700'];

  function filterByRole(clickedButton) {
    // 1. Ambil role dari tombol yang diklik
    const role = clickedButton?.dataset.role;
    if (!role) return; // Keluar jika tombol tidak punya data-role

    // 2. Dapatkan semua tombol filter dan semua grup konten
    const allButtons = document.querySelectorAll("#role-filter .pill");
    const allGroups = document.querySelectorAll(".role-group");

    // 3. Loop dan jadikan SEMUA tombol inaktif (gray)
    allButtons.forEach(button => {
      button.classList.remove(...activeClasses);
      button.classList.add(...inactiveClasses);
      button.setAttribute("aria-pressed", "false"); // Baik untuk aksesibilitas
    });

    // 4. Jadikan HANYA tombol yang diklik menjadi aktif (merah)
    clickedButton.classList.remove(...inactiveClasses);
    clickedButton.classList.add(...activeClasses);
    clickedButton.setAttribute("aria-pressed", "true");

    // 5. Tampilkan/sembunyikan grup konten berdasarkan role
    allGroups.forEach(group => {
      // Tampilkan jika role-nya cocok, sembunyikan jika tidak
      group.classList.toggle("hidden", group.dataset.role !== role);
    });

    // 6. Scroll ke grup yang baru saja diaktifkan
    document.querySelector(`.role-group[data-role="${role}"]`)
      ?.scrollIntoView({ behavior:"smooth", block:"start" });
  }
  // ============================


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