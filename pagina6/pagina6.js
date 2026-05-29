document.addEventListener("DOMContentLoaded", () => {

    const botones = document.querySelectorAll(".menu button");

    botones.forEach(btn => {
        btn.addEventListener("click", () => {

            botones.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            alert("Sección: " + btn.textContent);

        });
    });

});