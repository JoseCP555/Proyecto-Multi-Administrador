document.addEventListener("DOMContentLoaded", () => {

    // ===== Menú lateral =====

    const menuButtons = document.querySelectorAll(".menu button");

    menuButtons.forEach(button => {

        button.addEventListener("click", () => {

            menuButtons.forEach(btn => {
                btn.style.background = "white";
                btn.style.color = "#1d4ed8";
            });

            button.style.background = "#dbeafe";
            button.style.color = "#2563eb";

            console.log(`Navegando a: ${button.textContent}`);

        });

    });

    // ===== Buscador =====

    const searchInput = document.querySelector(".search-bar input");
    const cards = document.querySelectorAll(".card");

    searchInput.addEventListener("input", (e) => {

        const searchTerm = e.target.value.toLowerCase();

        cards.forEach(card => {

            const title = card.querySelector("h3").textContent.toLowerCase();
            const content = card.querySelector("p").textContent.toLowerCase();

            if(title.includes(searchTerm) || content.includes(searchTerm)){
                card.style.display = "block";
            }else{
                card.style.display = "none";
            }

        });

    });

    // ===== Iconos =====

    const icons = document.querySelectorAll(".icons span");

    icons.forEach(icon => {

        icon.addEventListener("click", () => {

            alert("Has hecho clic en una función de la barra superior.");

        });

    });

    // ===== Botón Diseño =====

    const btnDesign = document.querySelector(".btn-blue");

    btnDesign.addEventListener("click", () => {

        const confirmEdit = confirm("¿Deseas entrar al modo de edición de diseño?");

        if(confirmEdit){
            console.log("Modo edición activado");
        }

    });

    // ===== Selects =====

    const selects = document.querySelectorAll("select");

    selects.forEach(select => {

        select.addEventListener("change", (e) => {

            alert(`Cambiando vista a: ${e.target.value}`);

        });

    });

});