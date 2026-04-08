document.addEventListener("DOMContentLoaded", () => {
    // 1. Gestión del Menú Activo
    const menuButtons = document.querySelectorAll(".menu button");

    menuButtons.forEach(button => {
        button.addEventListener("click", () => {
            // Quitamos la clase 'active' de todos los botones
            menuButtons.forEach(btn => btn.classList.remove("active"));
            // Se la añadimos al botón clicado
            button.classList.add("active");

            console.log(`Cargando vista: ${button.textContent}`);
        });
    });

    // 2. Buscador Dinámico (Filtra contenido dentro de las tarjetas)
    const searchInput = document.querySelector(".search-bar input");
    const cards = document.querySelectorAll(".card");

    searchInput.addEventListener("input", (e) => {
        const term = e.target.value.toLowerCase();

        cards.forEach(card => {
            const content = card.innerText.toLowerCase();
            // Si el texto de la tarjeta contiene el término, se muestra
            if (content.includes(term)) {
                card.style.opacity = "1";
                card.style.transform = "scale(1)";
                card.style.display = "block";
            } else {
                card.style.opacity = "0.5"; // En lugar de ocultar, atenuamos
                // card.style.display = "none"; // Descomenta esta línea si prefieres ocultar
            }
        });
    });

    // 3. Manejo de Selectores (Filtros de Residencial)
    const selects = document.querySelectorAll("select");
    selects.forEach(select => {
        select.addEventListener("change", (e) => {
            const selectedValue = e.target.value;
            alert(`Cambiando datos para: ${selectedValue}`);
            // Aquí podrías disparar una función para actualizar los valores de las tarjetas
        });
    });

    // 4. Interacción con los ítems de las tarjetas
    // Hacemos que los nombres de proveedores o vigilantes sean clicables para ver detalles
    const cardItems = document.querySelectorAll(".card p");
    cardItems.forEach(item => {
        item.style.cursor = "pointer";
        item.addEventListener("click", () => {
            const info = item.textContent;
            console.log(`Detalle seleccionado: ${info}`);
            // Ejemplo: resaltar el item seleccionado
            item.style.fontWeight = "bold";
            setTimeout(() => item.style.fontWeight = "normal", 2000);
        });
    });

    // 5. Soporte y Ayuda
    const footerLinks = document.querySelector(".footer");
    footerLinks.addEventListener("click", (e) => {
        if (e.target.textContent.includes("Soporte")) {
            alert("Abriendo ticket de soporte técnico...");
        } else if (e.target.textContent.includes("Centro de Ayuda")) {
            alert("Redirigiendo a la base de conocimientos...");
        }
    });
});