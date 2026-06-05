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

// CONFIGURACIONES

const settings = document.querySelectorAll(".setting-box");

settings.forEach(setting => {

    setting.addEventListener("click", () => {

        settings.forEach(s => {

            s.classList.remove("active-setting");

        });

        setting.classList.add("active-setting");

    });

});

// BOTON RESET

const resetBtn = document.querySelector(".reset-btn");

resetBtn.addEventListener("click", () => {

    alert("Configuración restablecida");

});