function addEvent() {

    let event = prompt("Ingrese el evento:");

    if(event){

        let li = document.createElement("li");
        li.textContent = event;

        document.getElementById("eventList").appendChild(li);
    }
}

function removeEvent() {

    let list = document.getElementById("eventList");

    if(list.lastChild){
        list.removeChild(list.lastChild);
    }else{
        alert("No hay eventos");
    }
}

function toggleItem(element) {

    alert("Abriste: " + element.textContent);
}

/* CALENDARIO */

let currentDate = new Date();

function renderCalendar(){

    const monthYear = document.getElementById("monthYear");
    const calendarBody = document.getElementById("calendarBody");

    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    const months = [
        "Enero","Febrero","Marzo","Abril",
        "Mayo","Junio","Julio","Agosto",
        "Septiembre","Octubre","Noviembre","Diciembre"
    ];

    monthYear.textContent = months[month] + " " + year;

    calendarBody.innerHTML = "";

    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    let date = 1;

    for(let i = 0; i < 6; i++){

        let row = document.createElement("tr");

        for(let j = 0; j < 7; j++){

            let cell = document.createElement("td");

            if(i === 0 && j < firstDay){

                cell.textContent = "";

            }else if(date > daysInMonth){

                break;

            }else{

                cell.textContent = date;

                let today = new Date();

                if(
                    date === today.getDate() &&
                    month === today.getMonth() &&
                    year === today.getFullYear()
                ){
                    cell.classList.add("today");
                }

                date++;
            }

            row.appendChild(cell);
        }

        calendarBody.appendChild(row);
    }
}

function nextMonth(){

    currentDate.setMonth(currentDate.getMonth() + 1);
    renderCalendar();
}

function prevMonth(){

    currentDate.setMonth(currentDate.getMonth() - 1);
    renderCalendar();
}

renderCalendar();