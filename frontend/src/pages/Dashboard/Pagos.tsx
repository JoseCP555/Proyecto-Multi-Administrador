import { useState, type FormEvent } from "react";
import { Wallet, Upload, Download, CheckCircle2, XCircle, FileDown } from "lucide-react";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Modal from "@/components/ui/Modal";
import ExportMenu from "@/components/ui/ExportMenu";
import { useFetch } from "@/hooks/useFetch";
import { usePermisos } from "@/lib/usePermisos";
import { api, API_BASE, getConjuntoActivo, getToken } from "@/lib/api";
import { descargarArchivo } from "@/lib/download";
import { moneda, fecha, fechaHora } from "@/lib/format";
import type { ComprobantePago, EstadoCuenta } from "@/types";

const BASE = API_BASE;

function estadoColor(estado: string) {
  if (estado === "aprobado") return "success";
  if (estado === "rechazado") return "danger";
  return "warning";
}

/** Comprobantes de pago (UH-13) y estado de cuenta del residente (UH-17). */
export default function Pagos() {
  const { puede } = usePermisos();
  const esRevisor = puede("pagos.revisar");
  const { data: estadoCuenta, cargar: cargarCuenta } = useFetch<EstadoCuenta>("/pagos/estado-cuenta");
  const { data: comprobantes, cargar, cargando } = useFetch<ComprobantePago[]>("/pagos/comprobantes");

  const [abierto, setAbierto] = useState(false);
  const [form, setForm] = useState({ monto: 0, periodo: "", movimiento_id: "", observacion: "" });
  const [archivo, setArchivo] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [subiendo, setSubiendo] = useState(false);
  const [revisando, setRevisando] = useState<ComprobantePago | null>(null);
  const [decision, setDecision] = useState("aprobado");
  const [observacion, setObservacion] = useState("");

  const subir = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (!archivo) {
      setError("Adjunta la imagen o PDF del comprobante.");
      return;
    }
    setSubiendo(true);
    try {
      const fd = new FormData();
      fd.append("monto", String(form.monto));
      if (form.periodo) fd.append("periodo", form.periodo);
      if (form.movimiento_id) fd.append("movimiento_id", form.movimiento_id);
      if (form.observacion) fd.append("observacion", form.observacion);
      fd.append("archivo", archivo);

      const token = getToken();
      const cid = getConjuntoActivo();
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (cid) headers["X-Conjunto-Id"] = String(cid);
      const res = await fetch(`${BASE}/pagos/comprobantes`, {
        method: "POST",
        headers,
        body: fd,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error((data as { detail?: string }).detail || "No se pudo subir el comprobante.");
      }
      setAbierto(false);
      setArchivo(null);
      setForm({ monto: 0, periodo: "", movimiento_id: "", observacion: "" });
      await Promise.all([cargar(), cargarCuenta()]);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubiendo(false);
    }
  };

  const guardarRevision = async (e: FormEvent) => {
    e.preventDefault();
    if (!revisando) return;
    setError("");
    try {
      await api.put(`/pagos/comprobantes/${revisando.id}/revisar`, { estado: decision, observacion });
      setRevisando(null);
      setObservacion("");
      await Promise.all([cargar(), cargarCuenta()]);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Estado de cuenta (UH-17) */}
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Estado de cuenta</h2>
            <p className="text-sm text-gray-500">
              {estadoCuenta?.unidades?.length
                ? `Unidad: ${estadoCuenta.unidades.map((u) => u.apartamento).join(", ")}`
                : "Pagos, fechas y saldo pendiente"}
            </p>
          </div>
          <Button variante="outline" tamano="sm" onClick={() => descargarArchivo(`${BASE}/pagos/estado-cuenta.pdf`)}>
            <FileDown className="w-4 h-4" /> Exportar PDF
          </Button>
        </div>

        <div className="grid sm:grid-cols-3 gap-3">
          <div className="border border-gray-100 rounded-xl p-4">
            <p className="text-xs text-gray-500">Total facturado</p>
            <p className="text-xl font-bold text-gray-800">{moneda(estadoCuenta?.total_facturado ?? 0)}</p>
          </div>
          <div className="border border-emerald-100 bg-emerald-50/50 rounded-xl p-4">
            <p className="text-xs text-emerald-700">Total pagado</p>
            <p className="text-xl font-bold text-emerald-700">{moneda(estadoCuenta?.total_pagado ?? 0)}</p>
          </div>
          <div className="border border-amber-100 bg-amber-50/50 rounded-xl p-4">
            <p className="text-xs text-amber-700">Saldo pendiente</p>
            <p className="text-xl font-bold text-amber-700">{moneda(estadoCuenta?.saldo ?? 0)}</p>
            {estadoCuenta?.proximo_vencimiento && (
              <p className="text-xs text-amber-600 mt-1">Próximo vencimiento: {fecha(estadoCuenta.proximo_vencimiento)}</p>
            )}
          </div>
        </div>

        {estadoCuenta?.sin_unidad && (
          <p className="text-xs text-gray-400 mt-3">
            Tu usuario aún no está vinculado a una unidad. La administración puede asociarlo desde Residentes.
          </p>
        )}

        {!!estadoCuenta?.movimientos?.length && (
          <div className="overflow-x-auto mt-4">
            <table className="w-full min-w-[620px] text-sm">
              <thead>
                <tr className="text-left text-gray-500">
                  <th className="py-2 font-medium">Concepto</th>
                  <th className="py-2 font-medium">Unidad</th>
                  <th className="py-2 font-medium">Vencimiento</th>
                  <th className="py-2 font-medium">Monto</th>
                  <th className="py-2 font-medium">Estado</th>
                </tr>
              </thead>
              <tbody>
                {estadoCuenta.movimientos.slice(0, 12).map((m) => (
                  <tr key={m.id} className="border-t border-gray-50">
                    <td className="py-2 text-gray-700">{m.concepto}</td>
                    <td className="py-2 text-gray-500">{m.propiedad ?? "—"}</td>
                    <td className="py-2 text-gray-500">{fecha(m.fecha_vencimiento)}</td>
                    <td className="py-2 text-gray-700">{moneda(m.monto)}</td>
                    <td className="py-2"><Badge color={m.estado === "pagado" ? "success" : m.estado === "vencido" ? "danger" : "warning"}>{m.estado}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Comprobantes (UH-13) */}
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
          <div>
            <h2 className="text-lg font-bold text-gray-900">{esRevisor ? "Comprobantes de pago" : "Mis comprobantes"}</h2>
            <p className="text-sm text-gray-500">
              {comprobantes?.length ?? 0} comprobante(s) · quedan «En revisión» hasta que la administración los confirme
            </p>
          </div>
          <div className="flex items-center gap-2">
            {esRevisor && (
              <ExportMenu opciones={[{ label: "Comprobantes (Excel)", ruta: "/pagos/comprobantes.xlsx", tipo: "xlsx" }]} />
            )}
            {puede("pagos.crear") && (
              <Button variante="primary" tamano="sm" onClick={() => setAbierto(true)}>
                <Upload className="w-4 h-4" /> Subir comprobante
              </Button>
            )}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[620px] text-sm">
            <thead>
              <tr className="text-left text-gray-500">
                <th className="py-2 font-medium">Fecha</th>
                {esRevisor && <th className="py-2 font-medium">Residente</th>}
                <th className="py-2 font-medium">Periodo</th>
                <th className="py-2 font-medium">Monto</th>
                <th className="py-2 font-medium">Estado</th>
                <th className="py-2 font-medium">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {(comprobantes ?? []).map((c) => (
                <tr key={c.id} className="border-t border-gray-50">
                  <td className="py-2.5 text-gray-500">{fechaHora(c.fecha_creacion)}</td>
                  {esRevisor && <td className="py-2.5 text-gray-700">{c.solicitante ?? "—"}</td>}
                  <td className="py-2.5 text-gray-500">{c.periodo ?? "—"}</td>
                  <td className="py-2.5 text-gray-700">{moneda(c.monto)}</td>
                  <td className="py-2.5">
                    <Badge color={estadoColor(c.estado)}>{c.estado.replace("_", " ")}</Badge>
                    {c.observacion && <p className="text-xs text-gray-400 mt-1">{c.observacion}</p>}
                  </td>
                  <td className="py-2.5">
                    <div className="flex flex-wrap items-center gap-1">
                      <button title="Descargar" onClick={() => descargarArchivo(`${BASE}/pagos/comprobantes/${c.id}/descargar`)}
                        className="p-1.5 rounded-full text-primary-600 hover:bg-blue-50"><Download className="w-4 h-4" /></button>
                      {esRevisor && c.estado === "en_revision" && (
                        <>
                          <button title="Aprobar" onClick={() => { setRevisando(c); setDecision("aprobado"); }}
                            className="p-1.5 rounded-full text-emerald-600 hover:bg-emerald-50"><CheckCircle2 className="w-4 h-4" /></button>
                          <button title="Rechazar" onClick={() => { setRevisando(c); setDecision("rechazado"); }}
                            className="p-1.5 rounded-full text-danger hover:bg-red-50"><XCircle className="w-4 h-4" /></button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {!comprobantes?.length && (
                <tr>
                  <td colSpan={esRevisor ? 6 : 5} className="py-8 text-center text-gray-400">
                    {cargando ? "Cargando..." : <span className="flex items-center justify-center gap-2"><Wallet className="w-4 h-4" /> Sin comprobantes.</span>}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {error && <div className="mt-4 text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
      </Card>

      <Modal abierto={abierto} onCerrar={() => setAbierto(false)} titulo="Subir comprobante de pago">
        <form onSubmit={subir} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Monto</label>
              <input type="number" min={1} step="0.01" className="input" required value={form.monto || ""}
                onChange={(e) => setForm({ ...form, monto: Number(e.target.value) })} />
            </div>
            <div>
              <label className="label">Periodo</label>
              <input type="month" className="input" value={form.periodo}
                onChange={(e) => setForm({ ...form, periodo: e.target.value })} />
            </div>
          </div>
          <div>
            <label className="label">Cuota asociada (opcional)</label>
            <select className="input" value={form.movimiento_id}
              onChange={(e) => setForm({ ...form, movimiento_id: e.target.value })}>
              <option value="">Sin asociar</option>
              {(estadoCuenta?.movimientos ?? [])
                .filter((m) => m.estado !== "pagado")
                .map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.concepto} · {fecha(m.fecha_vencimiento)} · {moneda(m.monto)}
                  </option>
                ))}
            </select>
          </div>
          <div>
            <label className="label">Observación</label>
            <input className="input" value={form.observacion}
              onChange={(e) => setForm({ ...form, observacion: e.target.value })} />
          </div>
          <div>
            <label className="label">Comprobante (PDF o imagen)</label>
            <input type="file" required accept=".pdf,.png,.jpg,.jpeg,.webp" className="input py-2"
              onChange={(e) => setArchivo(e.target.files?.[0] ?? null)} />
          </div>
          <Button variante="primary" className="w-full" type="submit" disabled={subiendo}>
            {subiendo ? "Subiendo…" : "Enviar comprobante"}
          </Button>
        </form>
      </Modal>

      <Modal abierto={!!revisando} onCerrar={() => setRevisando(null)} titulo="Revisar comprobante">
        <form onSubmit={guardarRevision} className="space-y-4">
          <p className="text-sm text-gray-600">
            {revisando?.solicitante} · {moneda(revisando?.monto ?? 0)} · {revisando?.periodo}
          </p>
          <div>
            <label className="label">Decisión</label>
            <select className="input" value={decision} onChange={(e) => setDecision(e.target.value)}>
              <option value="aprobado">Aprobar (marca la cuota como pagada)</option>
              <option value="rechazado">Rechazar</option>
            </select>
          </div>
          <div>
            <label className="label">Observación</label>
            <textarea className="input" rows={3} value={observacion} onChange={(e) => setObservacion(e.target.value)} />
          </div>
          <Button variante="primary" className="w-full" type="submit">Guardar revisión</Button>
        </form>
      </Modal>
    </div>
  );
}
