document.addEventListener("DOMContentLoaded", () => {
    // Seleccionamos los elementos del DOM
    const loginBtn = document.querySelector(".btn");
    const googleBtn = document.querySelector(".google-btn");
    const inputs = document.querySelectorAll("input");
    const forgotPasswordLink = document.querySelector(".link");

    // Evento para el botón de INICIAR
    loginBtn.addEventListener("click", () => {
        const email = inputs[0].value.trim();
        const password = inputs[1].value.trim();

        if (email === "" || password === "") {
            alert("Por favor, completa todos los campos.");
            return;
        }

        // Aquí iría la lógica de conexión con tu base de datos o API
        console.log("Intentando iniciar sesión con:", email);
        alert(`¡Bienvenido! Has ingresado con el correo: ${email}`);
    });

    // Evento para el botón de Google (Simulación)
    googleBtn.addEventListener("click", () => {
        alert("Redirigiendo a la autenticación de Google...");
    });

    // Evento para "Olvidaste tu contraseña"
    forgotPasswordLink.addEventListener("click", () => {
        const email = inputs[0].value.trim();
        if (email) {
            alert(`Se ha enviado un enlace de recuperación a: ${email}`);
        } else {
            alert("Por favor, escribe tu correo electrónico primero.");
        }
    });

    // Permitir iniciar sesión al presionar "Enter" en los campos
    inputs.forEach(input => {
        input.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                loginBtn.click();
            }
        });
    });
});