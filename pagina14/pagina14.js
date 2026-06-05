// MENU PRINCIPAL

const botones = document.querySelectorAll(".menu button");

botones.forEach(btn => {

    btn.addEventListener("click", () => {

        botones.forEach(b => {

            b.classList.remove("active");

        });

        btn.classList.add("active");

    });

});

// MENU DOCUMENTOS

const docButtons = document.querySelectorAll(".doc-btn");

docButtons.forEach(btn => {

    btn.addEventListener("click", () => {

        docButtons.forEach(b => {

            b.classList.remove("active-doc");

        });

        btn.classList.add("active-doc");

    });

});

// BOTON SUBIR

const uploadBtn = document.querySelector(".upload-btn");

uploadBtn.addEventListener("click", () => {

    alert("Subiendo documento...");

});

// BOTON BORRAR

const deleteBtn = document.querySelector(".delete-btn");

deleteBtn.addEventListener("click", () => {

    alert("Acta eliminada");

});