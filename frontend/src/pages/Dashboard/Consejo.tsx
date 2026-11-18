import { useMemo, useState } from "react";
import { FileText, Download, TrendingUp, TrendingDown, Wallet, Scale } from "lucide-react";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import ExportMenu from "@/components/ui/ExportMenu";
import { useFetch } from "@/hooks/useFetch";
import { descargarArchivo } from "@/lib/download";
import { API_BASE } from "@/lib/api";
import { moneda, fecha } from "@/lib/format";
import type { Documento } from "@/types";

interface Resumen {
  ingresos: number;
  gastos: number;
  saldo: number;
  pendiente: number;
  movimientos_pagados: number;
  movimientos_pendientes: number;
}

interface PuntoMes {
  mes: string;
  valor: number;
  ingresos?: number;
  gastos?: number;
}

const BASE = API_BASE;

/**
 * Panel del consejo de administración:
 * · Actas y transcripciones de la última asamblea (UH-22)
 * · Reporte de ingresos y egresos filtrado por periodo, con exportación PDF/Excel (UH-23)
 */
export default function Consejo() {
  // UH-23: el reporte se filtra por período (3, 6, 12 meses o todo el histórico).
  const [periodo, setPeriodo] = useState("6");
  const desde = useMemo(() => {
    if (periodo === "todo") return "";
    const d = new Date();
    d.setDate(1);
    d.setMonth(d.getMonth() - (Number(periodo) - 1));
    return d.toISOString().slice(0, 10);
  }, [periodo]);
  const filtro = desde ? `?desde=${desde}` : "";

  const { data: documentos } = useFetch<Documento[]>("/documentos");
  const { data: resumen } = useFetch<Resumen>(`/finanzas/resumen${filtro}`, [filtro]);
  const { data: serie } = useFetch<PuntoMes[]>(`/reportes/finanzas-por-mes${filtro}`, [filtro]);

  // Actas: los documentos oficiales de la asamblea (no editables por residentes).
  const actas = (documentos ?? []).filter((d) =>
    ["acta", "asamblea", "transcripcion"].includes((d.tipo_documento ?? "").toLowerCase()),
  );
  const maximo = Math.max(
    ...(serie ?? []).flatMap((s) => [s.ingresos ?? s.valor, s.gastos ?? 0]),
    1,
  );

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Reporte financiero del conjunto</h2>
            <p className="text-sm text-gray-500">
              Ingresos y egresos consolidados ·{" "}
              {periodo === "todo" ? "todo el histórico" : `últimos ${periodo} meses`}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <select
              className="input py-1.5 w-auto text-sm"
              value={periodo}
              onChange={(e) => setPeriodo(e.target.value)}
              aria-label="Filtrar el reporte por período"
            >
              <option value="3">Últimos 3 meses</option>
              <option value="6">Últimos 6 meses</option>
              <option value="12">Últimos 12 meses</option>
              <option value="todo">Todo el histórico</option>
            </select>
            <ExportMenu
              opciones={[
                { label: "Reporte del consejo (PDF)", ruta: `/reportes/exportar/consejo.pdf${filtro}`, tipo: "pdf" },
                { label: "Reporte del consejo (Excel)", ruta: `/reportes/exportar/consejo.xlsx${filtro}`, tipo: "xlsx" },
                { label: "Cartera por unidad (PDF)", ruta: `/reportes/exportar/cartera.pdf${filtro}`, tipo: "pdf" },
                { label: "Cartera por unidad (Excel)", ruta: `/reportes/exportar/cartera.xlsx${filtro}`, tipo: "xlsx" },
              ]}
            />
          </div>
        </div>

        <div className="grid sm:grid-cols-4 gap-3">
          <div className="border border-gray-100 rounded-xl p-4">
            <p className="text-xs text-gray-500 flex items-center gap-1"><TrendingUp className="w-3.5 h-3.5" /> Ingresos</p>
            <p className="text-lg font-bold text-emerald-700">{moneda(resumen?.ingresos ?? 0)}</p>
          </div>
          <div className="border border-gray-100 rounded-xl p-4">
            <p className="text-xs text-gray-500 flex items-center gap-1"><TrendingDown className="w-3.5 h-3.5" /> Egresos</p>
            <p className="text-lg font-bold text-danger">{moneda(resumen?.gastos ?? 0)}</p>
          </div>
          <div className="border border-gray-100 rounded-xl p-4">
            <p className="text-xs text-gray-500 flex items-center gap-1"><Wallet className="w-3.5 h-3.5" /> Saldo</p>
            <p className="text-lg font-bold text-gray-800">{moneda(resumen?.saldo ?? 0)}</p>
          </div>
          <div className="border border-gray-100 rounded-xl p-4">
            <p className="text-xs text-gray-500 flex items-center gap-1"><Scale className="w-3.5 h-3.5" /> Pendiente de cobro</p>
            <p className="text-lg font-bold text-amber-700">{moneda(resumen?.pendiente ?? 0)}</p>
          </div>
        </div>

        {/* Gráfica resumen: Ingresos vs Egresos por mes (UH-23) */}
        <div className="mt-5">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
            <p className="text-sm font-medium text-gray-600">Ingresos vs egresos por mes</p>
            <div className="flex items-center gap-3 text-xs text-gray-500">
              <span className="inline-flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500 inline-block" /> Ingresos
              </span>
              <span className="inline-flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-rose-500 inline-block" /> Egresos
              </span>
            </div>
          </div>
          <div className="flex items-stretch gap-3 h-40">
            {(serie ?? []).map((s) => {
              const ing = s.ingresos ?? s.valor;
              const gas = s.gastos ?? 0;
              return (
                <div key={s.mes} className="flex-1 h-full flex flex-col items-center justify-end gap-1">
                  <div className="w-full h-full flex items-end justify-center gap-1">
                    <div
                      className="w-5 max-w-[26px] rounded-t-md bg-emerald-500/85 min-h-[4px]"
                      style={{ height: `${Math.max(4, (ing / maximo) * 100)}%` }}
                      title={`Ingresos ${s.mes}: ${moneda(ing)}`}
                    />
                    <div
                      className="w-5 max-w-[26px] rounded-t-md bg-rose-500/85 min-h-[4px]"
                      style={{ height: `${Math.max(4, (gas / maximo) * 100)}%` }}
                      title={`Egresos ${s.mes}: ${moneda(gas)}`}
                    />
                  </div>
                  <span className="text-[11px] text-gray-400">{s.mes}</span>
                </div>
              );
            })}
            {!serie?.length && <p className="text-sm text-gray-400">Sin datos financieros para graficar.</p>}
          </div>
        </div>
      </Card>

      <Card>
        <div className="mb-4">
          <h2 className="text-lg font-bold text-gray-900">Actas y documentos oficiales</h2>
          <p className="text-sm text-gray-500">
            El acta de la última asamblea está disponible en PDF y no puede ser editada por los residentes.
          </p>
        </div>

        <div className="space-y-2">
          {actas.map((d) => (
            <div key={d.id} className="flex items-center justify-between gap-3 border border-gray-100 bg-gray-50/60 rounded-xl p-3">
              <div className="min-w-0 flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-red-50 text-danger flex items-center justify-center shrink-0">
                  <FileText className="w-4 h-4" />
                </div>
                <div className="min-w-0">
                  <p className="font-medium text-gray-800 truncate">{d.titulo}</p>
                  <p className="text-xs text-gray-400">{fecha(d.fecha_creacion)} · {d.tipo_documento}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Badge color="neutral">v{d.version}</Badge>
                <button
                  onClick={() => descargarArchivo(`${BASE}/documentos/${d.id}/descargar`)}
                  className="flex items-center gap-1 text-sm text-primary-600 hover:underline"
                >
                  <Download className="w-4 h-4" /> Descargar
                </button>
              </div>
            </div>
          ))}
          {!actas.length && (
            <p className="text-sm text-gray-400">
              Aún no hay actas publicadas. La administración puede subirlas desde Documentos con el tipo «acta».
            </p>
          )}
        </div>
      </Card>
    </div>
  );
}
