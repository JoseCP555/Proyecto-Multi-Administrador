const express = require("express");

const cors = require("cors");

const app = express();

app.use(cors());

app.use(express.json());


// LOGIN
app.post("/login", (req, res) => {

    const { email, password } = req.body;

    console.log(email, password);

    // Usuario de prueba
    if(email === "admin@gmail.com" && password === "1234"){

        res.json({
            success: true,
            message: "Login correcto"
        });

    }else{

        res.json({
            success: false,
            message: "Datos incorrectos"
        });

    }

});


app.listen(3000, () => {

    console.log("Servidor corriendo en puerto 3000");

});