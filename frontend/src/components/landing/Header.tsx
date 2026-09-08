import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X } from "lucide-react";
import Button from "@/components/ui/Button";
import Logo from "./Logo";

const nav = [
  { label: "Características", href: "#caracteristicas" },
  { label: "Cómo funciona", href: "#como-funciona" },
  { label: "Asistente", href: "#chatbot" },
  { label: "Planes", href: "#planes" },
  { label: "FAQ", href: "#faq" },
];

export default function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [abierto, setAbierto] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 16);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -40, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
        scrolled || abierto
          ? "bg-white/75 backdrop-blur-xl shadow-[0_1px_0_rgba(17,24,39,0.06)]"
          : "bg-transparent"
      }`}
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-[72px]">
          <Logo />

          <nav className="hidden lg:flex items-center gap-1 rounded-full bg-white/60 backdrop-blur px-2 py-1 ring-1 ring-gray-100">
            {nav.map((n) => (
              <a
                key={n.href}
                href={n.href}
                className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-dark-100 hover:bg-gray-100 rounded-full transition"
              >
                {n.label}
              </a>
            ))}
          </nav>

          <div className="hidden lg:flex items-center gap-2">
            <Link to="/login">
              <Button variante="ghost" tamano="md">Iniciar sesión</Button>
            </Link>
            <Link to="/register">
              <Button variante="primary" tamano="md" className="shadow-pill">Empezar gratis</Button>
            </Link>
          </div>

          <button
            className="lg:hidden p-2 rounded-xl text-gray-700 hover:bg-gray-100"
            onClick={() => setAbierto((v) => !v)}
            aria-label="Menú"
          >
            {abierto ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {abierto && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="lg:hidden overflow-hidden bg-white/95 backdrop-blur-xl border-t border-gray-100"
          >
            <div className="px-4 py-4 space-y-1">
              {nav.map((n) => (
                <a
                  key={n.href}
                  href={n.href}
                  onClick={() => setAbierto(false)}
                  className="block px-4 py-3 text-sm font-medium text-gray-700 rounded-xl hover:bg-gray-100"
                >
                  {n.label}
                </a>
              ))}
              <div className="pt-3 grid grid-cols-2 gap-2">
                <Link to="/login"><Button variante="outline" tamano="md" className="w-full">Iniciar sesión</Button></Link>
                <Link to="/register"><Button variante="primary" tamano="md" className="w-full">Empezar gratis</Button></Link>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
}
