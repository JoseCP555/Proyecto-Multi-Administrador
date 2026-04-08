document.addEventListener("DOMContentLoaded", () => {
    // 1. Lógica de Modo Claro / Oscuro
    const toggleButtons = document.querySelectorAll(".toggle button");
    const body = document.body;
    const sidebar = document.querySelector(".sidebar");

    toggleButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const mode = btn.textContent.trim().toLowerCase();
            
            if (mode === "oscuro") {
                body.style.background = "#2c2c2c";
                body.style.color = "#ffffff";
                sidebar.style.background = "#1a1a1a";
                // Ajustar botones del menú para que se vean en modo oscuro
                document.querySelectorAll(".menu button").forEach(b => {
                    b.style.background = "#444";
                    b.style.color = "#fff";
                });
            } else {
                // Volver al modo original (Claro)
                body.style.background = "#d9bb6b";
                body.style.color = "#000000";
                sidebar.style.background = "#e2a94f";
                document.querySelectorAll(".menu button").forEach(b => {
                    b.style.background = "#f3d58c";
                    b.style.color = "#000";
                });
            }
            console.log(`Modo ${mode} activado`);
        });
    });

    // 2. Filtro de Búsqueda de Tarjetas
    const searchInput = document.querySelector(".search-bar input");
    const cards = document.querySelectorAll(".card");

    searchInput.addEventListener("input", () => {
        const query = searchInput.value.toLowerCase();
        
        cards.forEach(card => {
            const text = card.innerText.toLowerCase();
            card.style.display = text.includes(query) ? "block" : "none";
        });
    });

    // 3. Manejo de Filtros (Selects)
    const selects = document.querySelectorAll("select");
    selects.forEach(select => {
        select.addEventListener("change", (e) => {
            console.log(`Filtro cambiado: ${e.target.value}`);
            // Aquí podrías filtrar las tarjetas por categoría si las tuvieras
        });
    });

    // 4. Botón de Diseño (Simulación de edición)
    const designBtn = document.querySelector(".btn-orange");
    designBtn.addEventListener("click", () => {
        alert("Entrando al editor de bloques del Dashboard...");
    });

    // 5. Interactividad en el Menú
    const menuButtons = document.querySelectorAll(".menu button");
    menuButtons.forEach(button => {
        button.addEventListener("click", () => {
            alert(`Cargando sección de ${button.textContent}...`);
        });
    });
});