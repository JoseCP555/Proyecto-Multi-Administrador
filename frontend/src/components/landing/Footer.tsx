import { Link } from "react-router-dom";
import { Facebook, Instagram, Linkedin, Mail } from "lucide-react";
import Container from "@/components/ui/Container";
import Logo from "./Logo";

const cols = [
  { t: "Producto", links: [["Características", "#caracteristicas"], ["Cómo funciona", "#como-funciona"], ["Asistente virtual", "#chatbot"], ["Planes", "#planes"]] },
  { t: "Recursos", links: [["Preguntas frecuentes", "#faq"], ["Iniciar sesión", "/login"], ["Crear cuenta", "/register"]] },
  { t: "Legal", links: [["Políticas de privacidad", "#"], ["Términos y condiciones", "#"]] },
];

export default function Footer() {
  const anio = new Date().getFullYear();
  return (
    <footer className="bg-white border-t border-gray-100">
      <Container className="py-14">
        <div className="grid gap-10 md:grid-cols-2 lg:grid-cols-5">
          <div className="lg:col-span-2">
            <Logo />
            <p className="mt-4 text-sm text-gray-500 max-w-xs leading-relaxed">
              Plataforma para la administración integral de conjuntos residenciales y propiedades horizontales, con asistente virtual incluido.
            </p>
            <div className="mt-5 flex gap-2">
              {[Facebook, Instagram, Linkedin].map((I, k) => (
                <span key={k} className="w-9 h-9 rounded-full bg-gray-100 text-gray-500 hover:bg-primary-500 hover:text-white transition flex items-center justify-center cursor-pointer"><I className="w-4 h-4" /></span>
              ))}
            </div>
          </div>
          {cols.map((c) => (
            <div key={c.t}>
              <h4 className="text-sm font-bold text-dark-100 mb-4">{c.t}</h4>
              <ul className="space-y-2.5 text-sm text-gray-500">
                {c.links.map(([l, h]) => (
                  <li key={l}>{h.startsWith("/") ? <Link to={h} className="hover:text-primary-600">{l}</Link> : <a href={h} className="hover:text-primary-600">{l}</a>}</li>
                ))}
              </ul>
            </div>
          ))}
          <div>
            <h4 className="text-sm font-bold text-dark-100 mb-4">Contacto</h4>
            <a href="mailto:multiadmin6@gmail.com" className="flex items-center gap-2 text-sm text-gray-500 hover:text-primary-600"><Mail className="w-4 h-4" /> multiadmin6@gmail.com</a>
            <p className="mt-2 text-sm text-gray-500">Bogotá, Colombia</p>
          </div>
        </div>
        <div className="mt-12 pt-6 border-t border-gray-100 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-gray-400">
          <span>© {anio} Multi.Admin · Todos los derechos reservados.</span>
          <span>Hecho con React, FastAPI y PostgreSQL.</span>
        </div>
      </Container>
    </footer>
  );
}
