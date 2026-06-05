document.addEventListener("DOMContentLoaded", () => {

    // Elementos
    const loginBtn = document.querySelector(".btn");
    const googleBtn = document.querySelector(".google-btn");
    const inputs = document.querySelectorAll("input");
    const forgotPasswordLink = document.querySelector(".link");

    // Botón iniciar sesión
    loginBtn.addEventListener("click", () => {

        const email = inputs[0].value.trim();
        const password = inputs[1].value.trim();

        if(email === "" || password === ""){
            alert("Por favor completa todos los campos.");
            return;
        }

        alert(`¡Bienvenido ${email}!`);

        // Redirección
        window.location.href = "pagina_1.html";
    });

    // Botón Google
    googleBtn.addEventListener("click", () => {
        alert("Redirigiendo a Google...");
    });

    // Recuperar contraseña
    forgotPasswordLink.addEventListener("click", () => {

        const email = inputs[0].value.trim();

        if(email === ""){
            alert("Escribe tu correo primero.");
        }else{
            alert(`Se envió un enlace a: ${email}`);
        }

    });

    // Enter para iniciar
    inputs.forEach(input => {

        input.addEventListener("keypress", (e) => {

            if(e.key === "Enter"){
                loginBtn.click();
            }

        });

    });

});