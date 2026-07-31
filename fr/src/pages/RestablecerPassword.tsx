import { useParams, useNavigate } from "react-router-dom"
import { useState } from "react"
import "./RestablecerPassword.css"

export default function RestablecerPassword() {

    const { token } = useParams()

    const navigate = useNavigate()

    const [password, setPassword] = useState("")
    const [confirmPassword, setConfirmPassword] = useState("")

    const [mensaje, setMensaje] = useState("")
    const [error, setError] = useState("")

    const [showPassword, setShowPassword] = useState(false)
    const [showConfirmPassword, setShowConfirmPassword] = useState(false)

    const cambiar = async () => {

        setMensaje("")
        setError("")

        if (!password || !confirmPassword) {
            setError("Completa ambos campos.")
            return
        }

        if (password.length < 9) {
            setError("La contraseña debe tener mínimo 9 caracteres.")
            return
        }

        if (!/[A-Z]/.test(password)) {
            setError("Debe contener una letra mayúscula.")
            return
        }

        if (!/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?`~]/.test(password)) {
            setError("Debe contener un carácter especial.")
            return
        }

        if (password !== confirmPassword) {
            setError("Las contraseñas no coinciden.")
            return
        }

        try {

            const res = await fetch("http://localhost:8000/restablecer-password", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    token: token,

                    nueva_password: password

                })

            })

            const data = await res.json()

            setMensaje(data.mensaje)

            if (data.mensaje.includes("actualizada")) {

                setTimeout(() => {

                    navigate("/login")

                }, 2000)

            }

        } catch {

            setError("No fue posible conectar con el servidor.")

        }

    }

    return (

        <div className="restablecer-root">

            <div className="restablecer-card">

                <h1>Restablecer contraseña</h1>

                {error && (
                    <div className="bienvenidos-error">
                        {error}
                    </div>
                )}

                {mensaje && (
                    <div className="bienvenidos-success">
                        {mensaje}
                    </div>
                )}

                <div className="pwd-input-wrapper">

                    <input

                        type={showPassword ? "text" : "password"}

                        placeholder="Nueva contraseña"

                        value={password}

                        onChange={(e) => setPassword(e.target.value)}

                    />

                    <button

                        type="button"

                        className="pwd-toggle-btn"

                        onClick={() => setShowPassword(!showPassword)}

                    >

                        <i className={showPassword ? "fa-solid fa-eye-slash" : "fa-solid fa-eye"}></i>

                    </button>

                </div>

                <div className="pwd-input-wrapper">

                    <input

                        type={showConfirmPassword ? "text" : "password"}

                        placeholder="Confirmar contraseña"

                        value={confirmPassword}

                        onChange={(e) => setConfirmPassword(e.target.value)}

                    />

                    <button

                        type="button"

                        className="pwd-toggle-btn"

                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}

                    >

                        <i className={showConfirmPassword ? "fa-solid fa-eye-slash" : "fa-solid fa-eye"}></i>

                    </button>

                </div>

                <button
                    className="restablecer-btn"
                    onClick={cambiar}
                >
                    Cambiar contraseña
                </button>

            </div>

        </div>

    )

}