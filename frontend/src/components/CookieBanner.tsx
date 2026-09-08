import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import "./CookieBanner.css";

const COOKIE_CONSENT_KEY = "multiadmin_cookie_consent";

export default function CookieBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem(COOKIE_CONSENT_KEY);

    if (consent !== "accepted") {
      setVisible(true);
    }
  }, []);

  const acceptCookies = () => {
    localStorage.setItem(COOKIE_CONSENT_KEY, "accepted");
    setVisible(false);
  };

  if (!visible) {
    return null;
  }

  return (
    <section
      className="cookie-banner"
      role="dialog"
      aria-label="Aviso de cookies"
    >
      <div className="cookie-banner__content">
        <h2>Usamos cookies</h2>

        <p>
          Utilizamos cookies necesarias para que Multi-Administrador funcione
          correctamente y para mejorar tu experiencia en la plataforma 
          y asegurate de saber que estas aceptando.
        </p>

        <Link
          className="cookie-banner__link"
          to="/terminos-condiciones"
        >
          Leer términos y condiciones
        </Link>
      </div>

      <button
        type="button"
        className="cookie-banner__button"
        onClick={acceptCookies}
      >
        Aceptar
      </button>
    </section>
  );
}
