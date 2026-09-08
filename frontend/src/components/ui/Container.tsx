import type { ReactNode } from "react";

// Contenedor centrado con ancho máximo y padding responsive.
export default function Container({
  children,
  className = "",
  ancho = "max-w-7xl",
}: {
  children: ReactNode;
  className?: string;
  ancho?: string;
}) {
  return (
    <div className={`mx-auto px-4 sm:px-6 lg:px-8 ${ancho} ${className}`}>
      {children}
    </div>
  );
}
