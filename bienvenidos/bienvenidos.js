document.addEventListener("DOMContentLoaded", () => {
    // Seleccionamos los elementos del formulario
    const helpInput = document.querySelector('input[placeholder*="necesitas ayuda"]');
    const buttons = document.querySelectorAll(".btn");

    // Asignamos funciones según el texto de cada botón
    buttons.forEach(button => {
        button.addEventListener("click", () => {
            const actionText = button.textContent.trim().toLowerCase();

            if (actionText.includes("registrarse")) {
                handleRegister();
            } else if (actionText.includes("ya tienes cuenta")) {
                handleLogin();
            } else if (actionText.includes("google")) {
                handleSocialLogin("Google");
            } else if (actionText.includes("apple")) {
                handleSocialLogin("Apple");
            }
        });
    });

    // Manejar la entrada de "ayuda"
    helpInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter" && helpInput.value.trim() !== "") {
            alert(`Buscando ayuda para: ${helpInput.value}`);
            helpInput.value = ""; // Limpia el campo
        }
    });

    // --- Funciones de Lógica ---

    function handleRegister() {
        console.log("Redirigiendo al formulario de registro...");
        alert("Abriendo ventana de registro...");
    }

    function handleLogin() {
        console.log("Redirigiendo al login...");
        alert("Cargando pantalla de inicio de sesión...");
    }

    function handleSocialLogin(platform) {
        console.log(`Iniciando sesión con ${platform}`);
        alert(`Conectando con la cuenta de ${platform}...`);
    }
});