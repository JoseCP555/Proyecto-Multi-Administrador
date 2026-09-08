import type { ReactNode } from "react";

export default function Card({
  children,
  className = "",
  hover = false,
}: {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}) {
  return (
    <div className={`card ${hover ? "hover:-translate-y-1" : ""} ${className}`}>
      {children}
    </div>
  );
}

export function CardHeader({
  titulo,
  subtitulo,
  accion,
}: {
  titulo: string;
  subtitulo?: string;
  accion?: ReactNode;
}) {
  return (
    <div className="flex items-start justify-between mb-4">
      <div>
        <h3 className="text-lg font-semibold text-gray-800">{titulo}</h3>
        {subtitulo && <p className="text-sm text-gray-500 mt-0.5">{subtitulo}</p>}
      </div>
      {accion}
    </div>
  );
}
