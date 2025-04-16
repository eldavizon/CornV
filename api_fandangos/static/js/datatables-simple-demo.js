window.addEventListener('DOMContentLoaded', event => {
    const datatablesSimple = document.getElementById('datatablesSimple');
    if (datatablesSimple) {
        new simpleDatatables.DataTable(datatablesSimple);
    }

    const datatablesFS = document.getElementById('datatablesFS');
    if (datatablesFS) {
        new simpleDatatables.DataTable(datatablesFS);
    }
});
