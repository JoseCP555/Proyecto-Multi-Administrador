// MENU PRINCIPAL

const menuButtons = document.querySelectorAll(".menu button");

menuButtons.forEach(btn => {

    btn.addEventListener("click", () => {

        menuButtons.forEach(b => {

            b.classList.remove("active");

        });

        btn.classList.add("active");

    });

});

// MENU REPORTES

const reportButtons = document.querySelectorAll(".report-btn");

reportButtons.forEach(btn => {

    btn.addEventListener("click", () => {

        reportButtons.forEach(b => {

            b.classList.remove("active-report");

        });

        btn.classList.add("active-report");

    });

});

// BUSCADOR

const searchInput = document.querySelector(".search-box input");

searchInput.addEventListener("keyup", () => {

    console.log("Buscando:", searchInput.value);

});