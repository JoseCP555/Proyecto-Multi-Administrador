import { Link } from "react-router-dom";
import logoUrl from "@/lib/logo";

/** Logo oficial (public/assets/logo.png) + nombre de marca. */
export default function Logo({ claro = false, tamano = 48 }: { claro?: boolean; tamano?: number }) {
  return (
    <Link to="/" className="flex items-center gap-2.5 shrink-0" aria-label="Multi.Admin - inicio">
      <span
        className={`rounded-full flex items-center justify-center ${claro ? "bg-white" : "bg-white shadow-sm ring-1 ring-gray-100"}`}
        style={{ width: tamano, height: tamano }}
      >
        <img src={logoUrl} alt="Multi.Admin" className="object-contain" style={{ width: tamano - 4, height: tamano - 4 }} />
      </span>
      <span className="leading-tight">
        <span className={`block text-xl font-extrabold tracking-tight ${claro ? "text-white" : "text-dark-100"}`}>
          Multi<span className="text-primary-500">.</span>Admin
        </span>
        <span className={`hidden sm:block text-[10px] font-medium ${claro ? "text-white/60" : "text-gray-400"}`}>
          Gestión de copropiedades
        </span>
      </span>
    </Link>
  );
}
