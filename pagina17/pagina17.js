// MENU ACTIVO

const menuButtons = document.querySelectorAll(".menu button");

menuButtons.forEach(button => {

    button.addEventListener("click", () => {

        menuButtons.forEach(btn => {

            btn.classList.remove("active");

        });

        button.classList.add("active");

    });

});

// BOTON RESTABLECER

const resetBtn = document.querySelector(".reset-btn");

resetBtn.addEventListener("click", () => {

    const checks = document.querySelectorAll("input[type='checkbox']");
    const radios = document.querySelectorAll("input[type='radio']");
    const range = document.querySelector("input[type='range']");

    checks.forEach(check => {

        check.checked = false;

    });

    radios.forEach(radio => {

        radio.checked = false;

    });

    range.value = 50;

    alert("Configuración restablecida");

});