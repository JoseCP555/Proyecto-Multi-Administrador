document.addEventListener("DOMContentLoaded", () => {

    const botones = document.querySelectorAll(".menu button");

    botones.forEach(btn => {
        btn.addEventListener("click", () => {

            // quitar activo
            botones.forEach(b => b.classList.remove("active"));

            // poner activo
            btn.classList.add("active");

            // mostrar acción
            alert("Entraste a: " + btn.textContent);

        });
    });

});