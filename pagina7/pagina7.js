// DATOS INICIALES
let residentes = JSON.parse(localStorage.getItem("residentes")) || [
    { nombre: "Juan Pérez", conjunto: "Marensa" },
    { nombre: "María Gómez", conjunto: "Época II" }
];

const conjuntos = [
    "Marensa",
    "Época II",
    "Miraflores",
    "Chamizo"
];

let seleccionado = null;

// ELEMENTOS
const lista = document.getElementById("lista");
const detalle = document.getElementById("detalle");
const inputNombre = document.getElementById("nombre");
const selectConjunto = document.getElementById("conjunto");
const mensaje = document.getElementById("mensaje");
const search = document.getElementById("search");

// MENSAJE
function mostrarMensaje(texto){

    mensaje.textContent = texto;
    mensaje.style.display = "block";

    setTimeout(() => {
        mensaje.style.display = "none";
    }, 2000);
}

// GUARDAR
function guardar(){
    localStorage.setItem(
        "residentes",
        JSON.stringify(residentes)
    );
}

// CARGAR CONJUNTOS
function cargarConjuntos(){

    selectConjunto.innerHTML = "";

    conjuntos.forEach(c => {

        const option = document.createElement("option");

        option.value = c;
        option.textContent = c;

        selectConjunto.appendChild(option);

    });
}

// RENDER
function render(){

    lista.innerHTML = "";

    residentes.forEach((r, index) => {

        const li = document.createElement("li");

        li.textContent =
            `${r.nombre} - ${r.conjunto}`;

        li.onclick = () =>
            seleccionar(index, li);

        lista.appendChild(li);

    });
}

// SELECCIONAR
function seleccionar(index, elemento){

    seleccionado = index;

    document
    .querySelectorAll("#lista li")
    .forEach(li => li.classList.remove("selected"));

    elemento.classList.add("selected");

    const r = residentes[index];

    detalle.innerHTML = `
        <strong>Nombre:</strong> ${r.nombre}<br>
        <strong>Conjunto:</strong> ${r.conjunto}
    `;

    inputNombre.value = r.nombre;
    selectConjunto.value = r.conjunto;
}

// AGREGAR
document
.getElementById("btnAgregar")
.onclick = () => {

    const nombre = inputNombre.value.trim();
    const conjunto = selectConjunto.value;

    if(!nombre){
        mostrarMensaje("Escribe un nombre");
        return;
    }

    residentes.push({
        nombre,
        conjunto
    });

    guardar();
    render();

    inputNombre.value = "";

    mostrarMensaje(
        "Residente agregado correctamente"
    );
};

// EDITAR
document
.getElementById("btnEditar")
.onclick = () => {

    if(seleccionado === null){

        mostrarMensaje(
            "Selecciona un residente"
        );

        return;
    }

    residentes[seleccionado].nombre =
        inputNombre.value;

    residentes[seleccionado].conjunto =
        selectConjunto.value;

    guardar();
    render();

    mostrarMensaje(
        "Datos actualizados"
    );
};

// ELIMINAR
document
.getElementById("btnEliminar")
.onclick = () => {

    if(seleccionado === null){

        mostrarMensaje(
            "Selecciona un residente"
        );

        return;
    }

    if(!confirm(
        "¿Seguro que deseas eliminar?"
    )) return;

    residentes.splice(seleccionado, 1);

    seleccionado = null;

    guardar();
    render();

    detalle.textContent =
        "Selecciona un residente";

    inputNombre.value = "";

    mostrarMensaje(
        "Residente eliminado"
    );
};

// BUSCADOR
search.addEventListener("input", e => {

    const texto =
        e.target.value.toLowerCase();

    const items =
        lista.getElementsByTagName("li");

    Array.from(items).forEach(li => {

        const nombre =
            li.textContent.toLowerCase();

        li.style.display =
            nombre.includes(texto)
            ? "block"
            : "none";

    });

});

// MENU ACTIVO
const botones =
document.querySelectorAll(".menu-item");

botones.forEach(btn => {

    btn.addEventListener("click", () => {

        botones.forEach(b =>
            b.classList.remove("active")
        );

        btn.classList.add("active");

        mostrarMensaje(
            "Entraste a: " +
            btn.textContent
        );

    });

});

// INICIAR
cargarConjuntos();
render();