import type { ButtonHTMLAttributes, ReactNode } from "react";
import { motion, type HTMLMotionProps } from "framer-motion";

type Variante = "primary" | "outline" | "ghost" | "danger" | "warning";
type Tamano = "sm" | "md" | "lg";

interface ButtonProps extends Omit<HTMLMotionProps<"button">, "children"> {
  variante?: Variante;
  tamano?: Tamano;
  children: ReactNode;
  to?: string;
}

const estilos: Record<Variante, string> = {
  primary: "bg-primary-500 text-white hover:bg-primary-600 shadow-sm",
  outline: "border border-gray-200 text-gray-700 bg-white hover:bg-gray-50",
  ghost: "text-gray-600 hover:bg-gray-100",
  danger: "bg-danger text-white hover:bg-red-600",
  warning: "bg-warning text-white hover:bg-amber-600",
};

const tamanos: Record<Tamano, string> = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2.5 text-sm",
  lg: "px-6 py-3.5 text-base",
};

const clases = (variante: Variante, tamano: Tamano) =>
  `btn ${estilos[variante]} ${tamanos[tamano]}`;

export default function Button({
  variante = "primary",
  tamano = "md",
  children,
  className = "",
  ...props
}: ButtonProps) {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.97 }}
      className={`${clases(variante, tamano)} ${className}`}
      {...(props as HTMLMotionProps<"button">)}
    >
      {children}
    </motion.button>
  );
}
