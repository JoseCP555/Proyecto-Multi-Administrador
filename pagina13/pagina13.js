// MENU ACTIVO

const botones = document.querySelectorAll(".menu button");

botones.forEach(btn => {

    btn.addEventListener("click", () => {

        botones.forEach(b => {

            b.classList.remove("active");

        });

        btn.classList.add("active");

    });

});

// BOTONES DOCUMENTOS

const docButtons = document.querySelectorAll(".doc-btn");

docButtons.forEach(btn => {

    btn.addEventListener("click", () => {

        docButtons.forEach(b => {

            b.classList.remove("active-orange");

        });

        btn.classList.add("active-orange");

    });

});