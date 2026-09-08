import { useRef, type ClipboardEvent, type KeyboardEvent } from "react";

interface Props {
  value: string;
  onChange: (v: string) => void;
  disabled?: boolean;
  longitud?: number;
}

/** Entrada de código numérico (6 casillas). Acepta pegar el código completo. */
export default function CodigoInput({ value, onChange, disabled, longitud = 6 }: Props) {
  const refs = useRef<Array<HTMLInputElement | null>>([]);
  const digitos = Array.from({ length: longitud }, (_, i) => value[i] ?? "");

  const setDigito = (i: number, d: string) => {
    const arr = [...digitos];
    arr[i] = d;
    onChange(arr.join("").slice(0, longitud));
  };

  const onInput = (i: number, raw: string) => {
    const limpio = raw.replace(/\D/g, "");
    if (!limpio) { setDigito(i, ""); return; }
    if (limpio.length > 1) {
      // Escribieron/pegaron varios dígitos en una casilla
      const nuevo = (value.slice(0, i) + limpio).slice(0, longitud);
      onChange(nuevo);
      refs.current[Math.min(nuevo.length, longitud - 1)]?.focus();
      return;
    }
    setDigito(i, limpio);
    if (i < longitud - 1) refs.current[i + 1]?.focus();
  };

  const onKey = (i: number, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !digitos[i] && i > 0) {
      refs.current[i - 1]?.focus();
      setDigito(i - 1, "");
      e.preventDefault();
    }
    if (e.key === "ArrowLeft" && i > 0) refs.current[i - 1]?.focus();
    if (e.key === "ArrowRight" && i < longitud - 1) refs.current[i + 1]?.focus();
  };

  const onPaste = (e: ClipboardEvent<HTMLInputElement>) => {
    const txt = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, longitud);
    if (txt) {
      e.preventDefault();
      onChange(txt);
      refs.current[Math.min(txt.length, longitud - 1)]?.focus();
    }
  };

  return (
    <div className="flex justify-center gap-2" onPaste={onPaste}>
      {digitos.map((d, i) => (
        <input
          key={i}
          ref={(el) => { refs.current[i] = el; }}
          value={d}
          onChange={(e) => onInput(i, e.target.value)}
          onKeyDown={(e) => onKey(i, e)}
          onFocus={(e) => e.target.select()}
          inputMode="numeric"
          autoComplete={i === 0 ? "one-time-code" : "off"}
          maxLength={longitud}
          disabled={disabled}
          aria-label={`Dígito ${i + 1}`}
          className="w-11 h-14 text-center text-2xl font-bold rounded-2xl border border-gray-200 bg-white
                     focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:opacity-60"
        />
      ))}
    </div>
  );
}
