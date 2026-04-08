document.addEventListener("DOMContentLoaded", () => {
    // 1. Manejo del Menú Lateral
    const menuButtons = document.querySelectorAll(".menu button");
    
    menuButtons.forEach(button => {
        button.addEventListener("click", () => {
            // Removemos clase activa de otros botones (opcional)
            menuButtons.forEach(btn => btn.style.background = "#f3d58c");
            
            // Efecto visual de selección
            button.style.background = "#d9bb6b";
            
            console.log(`Navegando a: ${button.textContent}`);
            // Aquí podrías cargar diferentes secciones
        });
    });

    // 2. Buscador en tiempo real (Simulación)
    const searchInput = document.querySelector(".search-bar input");
    const cards = document.querySelectorAll(".card");

    searchInput.addEventListener("input", (e) => {
        const searchTerm = e.target.value.toLowerCase();

        cards.forEach(card => {
            const title = card.querySelector("h3").textContent.toLowerCase();
            const content = card.querySelector("p").textContent.toLowerCase();

            // Si el texto coincide con el título o contenido, se muestra, si no, se oculta
            if (title.includes(searchTerm) || content.includes(searchTerm)) {
                card.style.display = "block";
            } else {
                card.style.display = "none";
            }
        });
    });

    // 3. Iconos de Notificaciones y Perfil
    const icons = document.querySelectorAll(".icons span");
    icons.forEach(icon => {
        icon.style.cursor = "pointer";
        icon.addEventListener("click", () => {
            alert(`Has hecho clic en una función de la barra superior.`);
        });
    });

    // 4. Botón Diseño de Página
    const btnDesign = document.querySelector(".btn-orange");
    btnDesign.addEventListener("click", () => {
        const confirmEdit = confirm("¿Deseas entrar al modo de edición de diseño?");
        if (confirmEdit) {
            console.log("Modo edición activado");
        }
    });

    // 5. Selectores de Copropiedad/Conjuntos
    const selects = document.querySelectorAll("select");
    selects.forEach(select => {
        select.addEventListener("change", (e) => {
            alert(`Cambiando vista a: ${e.target.value}`);
        });
    });
});