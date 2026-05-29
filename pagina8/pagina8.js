// MENU ACTIVO
const menuButtons = document.querySelectorAll(".menu button");

menuButtons.forEach(button => {

    button.addEventListener("click", () => {

        menuButtons.forEach(btn => {
            btn.classList.remove("active");
        });

        button.classList.add("active");

        mostrarMensaje("Entraste a: " + button.textContent);

    });

});

// BUSCADOR
const searchInput = document.getElementById("searchInput");

searchInput.addEventListener("keyup", () => {

    const text = searchInput.value.toLowerCase();

    const cards = document.querySelectorAll(".card-content p");

    cards.forEach(item => {

        if(item.textContent.toLowerCase().includes(text)){

            item.style.display = "block";

        }else{

            item.style.display = "none";

        }

    });

});

// MENSAJE
function mostrarMensaje(texto){

    const mensaje = document.createElement("div");

    mensaje.textContent = texto;

    mensaje.style.position = "fixed";
    mensaje.style.bottom = "20px";
    mensaje.style.right = "20px";
    mensaje.style.background = "#2563eb";
    mensaje.style.color = "white";
    mensaje.style.padding = "14px 20px";
    mensaje.style.borderRadius = "12px";
    mensaje.style.boxShadow = "0 5px 15px rgba(0,0,0,0.2)";
    mensaje.style.zIndex = "999";

    document.body.appendChild(mensaje);

    setTimeout(() => {
        mensaje.remove();
    }, 2000);

}