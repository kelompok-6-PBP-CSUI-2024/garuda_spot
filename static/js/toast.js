/**
 * Menampilkan notifikasi toast sementara.
 * @param {string} title Judul toast.
 * @param {string} message Pesan toast.
 * @param {'success'|'error'|'info'|'normal'} [type='normal'] Tipe toast (mempengaruhi warna).
 * @param {number} [duration=3000] Durasi tampilan toast dalam milidetik.
 */
function showToast(title, message, type = 'normal', duration = 3000) {
    // 1. Dapatkan elemen HTML toast dari halaman
    const toastComponent = document.getElementById('toast-component');
    const toastTitle = document.getElementById('toast-title');
    const toastMessage = document.getElementById('toast-message');

    // 2. Pastikan elemen ada sebelum melanjutkan
    if (!toastComponent || !toastTitle || !toastMessage) {
        console.error("Toast HTML elements (toast-component, toast-title, toast-message) not found in the DOM!");
        return; // Hentikan eksekusi jika elemen tidak ditemukan
    }

    // 3. Hapus kelas warna sebelumnya untuk reset
    toastComponent.classList.remove(
        'bg-red-50', 'border-red-500', 'text-red-600',       // Error styles
        'bg-green-50', 'border-green-500', 'text-green-600', // Success styles
        'bg-blue-50', 'border-blue-500', 'text-blue-600',     // Info styles
        'bg-white', 'border-gray-300', 'text-gray-800'      // Normal styles
    );

    // 4. Atur kelas warna dan border berdasarkan tipe
    if (type === 'success') {
        toastComponent.classList.add('bg-green-50', 'border-green-500', 'text-green-600');
        toastComponent.style.border = '1px solid #b11402ff'; // Tailwind green-500
    } else if (type === 'error') {
        toastComponent.classList.add('bg-red-50', 'border-red-500', 'text-red-600');
        toastComponent.style.border = '1px solid #ef4444'; // Tailwind red-500
    } else if (type === 'info') {
        toastComponent.classList.add('bg-blue-50', 'border-blue-500', 'text-blue-600');
        toastComponent.style.border = '1px solid #3b82f6'; // Tailwind blue-500
    } else { // 'normal' atau tipe tidak dikenal
        toastComponent.classList.add('bg-white', 'border-gray-300', 'text-gray-800');
        toastComponent.style.border = '1px solid #d1d5db'; // Tailwind gray-300
    }

    // 5. Atur teks judul dan pesan
    toastTitle.textContent = title;
    toastMessage.textContent = message;

    // 6. Tampilkan toast dengan animasi
    toastComponent.classList.remove('opacity-0', 'translate-y-64');
    toastComponent.classList.add('opacity-100', 'translate-y-0');

    // 7. Sembunyikan toast setelah durasi tertentu
    setTimeout(() => {
        toastComponent.classList.remove('opacity-100', 'translate-y-0');
        toastComponent.classList.add('opacity-0', 'translate-y-64');
    }, duration);
}

// Opsional: Tambahkan console log untuk memastikan file ini dimuat
// console.log("toast.js loaded successfully.");