"""Arma docs/cambios_pr1.html: incrusta los SVG exportados de docs/diagramas/*.drawio en la plantilla.

Si se edita un diagrama en draw.io:
  1) exportar a SVG con el mismo nombre (Archivo > Exportar como > SVG, o la CLI: draw.io -x -f svg -o x.svg x.drawio);
  2) python docs/construir_cambios.py
Los pasos clicables del ciclo son las celdas s01..s13 del diagrama 01 (el id de celda debe coincidir con PASOS)."""
import json
import pathlib
import re

AQUI = pathlib.Path(__file__).parent
DIAG = AQUI / "diagramas"

PASOS = {
    "s01": dict(tipo="nuevo", titulo="1 · Abrir ciclo", archivos=["nb_ini_ciclo.py", "ddl/01_ctl_param.sql"],
        que="Cuaderno nuevo que registra en ctl.ciclo el corte, la fecha de corte y la versión de cada fuente. Rechaza un id_ciclo que ya existe.",
        porque="El §18.3 pide que el único parámetro de los cuadernos sea el id_ciclo. Faltaba un lugar donde vivieran los demás datos del ciclo.",
        paraque="Que cada cuaderno se pueda ejecutar con solo el id_ciclo y que el informe diga con qué versión de fuentes se generó.",
        aporte="Es la puerta de entrada trazable: todo lo que ocurre después se amarra a este registro.",
        limite="Repetir una corrida exige un id_ciclo nuevo (por ejemplo 2026-09-r1); reutilizarlo duplicaría filas."),
    "s02": dict(tipo="mod", titulo="2 · Bronce", archivos=["nb_e1_bronce.py"],
        que="El corte ya no es un parámetro propio: se lee de ctl.ciclo a partir del id_ciclo.",
        porque="Para cumplir que el id_ciclo sea el único parámetro, sin cambiar lo que Bronce guarda.",
        paraque="Que Bronce siga entregando evidencia probatoria (entidad, fecha, número de registros y SHA-256) sin depender de parámetros sueltos.",
        aporte="Mantiene intacta la evidencia de lo que llegó, que es lo que más pesa en una auditoría."),
    "s03": dict(tipo="mod", titulo="3 · Plata + cuarentena", archivos=["nb_e1_plata.py", "ciclo.py"],
        que="La etiqueta del corte pasa a la columna corte y la fecha de corte de la fuente ya no se sobreescribe. Las escrituras usan esquema explícito.",
        porque="Era un defecto: Plata pisaba fecha_corte y la fuente de validación perdía su fecha real, que los cruces necesitan. Además Spark no puede crear una tabla con una columna que solo trae None.",
        paraque="Que lo normalizado llegue completo a las etapas siguientes y que la cuarentena conserve la causa de cada rechazo.",
        aporte="Las cifras que verá el líder de datos en C1 salen de datos íntegros."),
    "s04": dict(tipo="mod", titulo="4 · MDM", archivos=["nb_e1_mdm.py", "mdm.py"],
        que="Mismos ajustes de corte y escritura. La lógica del maestro de personas y hogares ya estaba en el primer commit.",
        porque="Mantener una sola convención de corte en las cuatro capas.",
        paraque="Que cada persona y cada hogar tengan una clave estable aunque aparezcan en varias fuentes.",
        aporte="Sin una clave de persona confiable los cruces y el titular por hogar no serían posibles.",
        limite="Las reglas de coincidencia y supervivencia son ilustrativas hasta resolver el pendiente G6."),
    "s05": dict(tipo="mod", titulo="5 · Oro", archivos=["nb_e1_oro.py"],
        que="Filtra por la columna corte y escribe una tabla por fuente con id_persona e id_hogar ya asignados.",
        porque="Coherencia con el cambio de Plata.",
        paraque="Ser la única entrada de los cruces: ningún cuaderno posterior lee Bronce ni Plata.",
        aporte="Cierra la Etapa 1 con fuentes certificadas a nivel de registro."),
    "s06": dict(tipo="ctrl", titulo="6 · Control C1", archivos=["nb_ctl_resumen.py", "controles.py", "ctl.aprobaciones"],
        que="Cuaderno que arma el resumen del control (entregas con su huella, cuarentena por causa, registros en Oro), deja una solicitud PENDIENTE y devuelve el resumen al pipeline.",
        porque="El §19 exige un control humano entre etapas. Antes de este PR no existía ninguno.",
        paraque="Que el líder de datos decida con cifras y no a ciegas, y que quede registrado quién decidió y cuándo.",
        aporte="Evita gastar cómputo en cruces si las fuentes están mal.",
        limite="El aprobador depende de la actividad de aprobación de Data Factory o del plan B; falta probarlo en el trial (pendiente G10)."),
    "s07": dict(tipo="nuevo", titulo="7 · Base de cruces", archivos=["cruces.py", "nb_e2_cruce_poblacional.py", "nb_e2_cruce_validacion.py", "nb_e2_consolidacion.py"],
        que="Una fila por persona y ciclo con los campos de la Tabla 7: persona, hogar, Sisbén, marcas de validación (encontrado, valor, fecha) y trazabilidad.",
        porque="Es la Etapa 2 del §17. La base registra hechos, no decisiones.",
        paraque="Separar lo que se sabe de cada persona de lo que se decide después, para que las reglas de liquidación se puedan cambiar sin tocar los cruces.",
        aporte="Es el contrato de datos entre la ingesta y la liquidación.",
        limite="Rol en el hogar y datos financieros quedan vacíos: la PoC no tiene fuente para ellos y no se inventan."),
    "s08": dict(tipo="ctrl", titulo="8 · Control C2", archivos=["nb_ctl_resumen.py", "cruces.pct_coincidencia"],
        que="Resumen con el universo y el porcentaje de personas encontradas en la fuente de validación.",
        porque="Tabla 9: el analista líder revisa el porcentaje de coincidencia antes de liquidar.",
        paraque="Detectar una fuente de validación incompleta antes de que bloquee o deje pasar a la gente equivocada.",
        aporte="Segunda puerta humana, ahora sobre la calidad del cruce."),
    "s09": dict(tipo="nuevo", titulo="9 · Liquidación", archivos=["liquidacion.py", "nb_00_focalizacion.py", "nb_01_titular.py", "nb_02_medio_pago.py", "nb_03_monto.py", "nb_04_fuente_recursos.py"],
        que="Un motor que lee criterios y reglas de las tablas param.* y decide elegibles y excluidos con su causal, un titular por hogar, el medio de pago, el monto y la fuente de recursos con su techo.",
        porque="El §18 pide que los criterios sean datos y no código. El orden respeta la Tabla 8: el monto va antes de la fuente de recursos.",
        paraque="Cambiar una regla de focalización, un monto o un techo editando una tabla, sin tocar ni volver a probar el código.",
        aporte="Convierte los cruces en pagos liquidados y en exclusiones explicadas.",
        limite="Los criterios, las reglas de bloqueo, la regla de titular, los montos y los techos son de ejemplo (G3 a G5); el medio de pago es un stub porque no hay datos financieros."),
    "s10": dict(tipo="ctrl", titulo="10 · Control C3", archivos=["nb_ctl_resumen.py", "controles.resumen_c3"],
        que="Resumen con elegibles, exclusiones por causal, monto total frente al techo y número de pagos que superan el techo.",
        porque="Tabla 9: el líder funcional revisa causales y montos antes de generar los listados.",
        paraque="Atrapar un error de dinero antes de que quede en un archivo para el operador.",
        aporte="Es el control con más riesgo financiero del ciclo."),
    "s11": dict(tipo="nuevo", titulo="11 · Listados + informe", archivos=["nb_05_listados.py", "nb_06_informe.py", "liquidacion.armar_informe"],
        que="La sábana del ciclo y un informe con conteos, exclusiones por causal, totales por operador y fuente, la verificación de que la suma de los listados es igual a la liquidación y el registro de las aprobaciones.",
        porque="El §18.4 define el contenido del informe de generación.",
        paraque="Dar al responsable del programa algo concreto que aprobar, y dar al documento la evidencia para la Tabla 4.",
        aporte="El informe avisa si se usaron parámetros ilustrativos, para que no pasen por reales.",
        limite="El informe se genera antes de C4 y se regenera al cierre para incluir esa aprobación."),
    "s12": dict(tipo="ctrl", titulo="12 · Control C4", archivos=["nb_ctl_resumen.py", "nb_registrar_aprobacion.py", "nb_aprobar.py"],
        que="Resumen del informe y registro de la decisión final. Incluye el plan B: nb_aprobar para decidir cuando el tenant no tiene buzón de Microsoft 365.",
        porque="Tabla 9: el responsable del programa autoriza lo que se va a publicar.",
        paraque="Que nadie reciba un pago que el responsable no haya autorizado, con constancia de quién y cuándo.",
        aporte="Última puerta antes de la publicación. Si el plazo vence, cuenta como rechazo."),
    "s13": dict(tipo="nuevo", titulo="13 · Publicación", archivos=["nb_07_publicar.py", "liquidacion.publicar"],
        que="Publica un archivo por operador y fuente en una carpeta por ciclo, con un manifiesto de huellas SHA-256. Se niega a publicar si algún control no está aprobado.",
        porque="El §18.4 pide publicar de forma que se pueda verificar que el archivo no cambió.",
        paraque="Que el listado entregado al operador se pueda comprobar byte a byte contra lo aprobado.",
        aporte="Cierra el ciclo con una salida verificable.",
        limite="Se publica en OneLake y no en Azure Storage con inmutabilidad; es una diferencia deliberada con producción."),
}

ARCHIVOS = [
    ["img_lib/liquidacion.py", "Lógica (img_lib)", 166], ["img_lib/controles.py", "Lógica (img_lib)", 63],
    ["img_lib/cruces.py", "Lógica (img_lib)", 56], ["img_lib/ciclo.py", "Lógica (img_lib)", 55],
    ["img_lib/metricas.py", "Lógica (img_lib)", 53], ["img_lib/dag.py", "Lógica (img_lib)", 48],
    ["img_lib/ilustrativos.py", "Lógica (img_lib)", 25],
    ["nb_ctl_resumen.py", "Cuadernos nuevos", 44], ["nb_06_informe.py", "Cuadernos nuevos", 36], ["nb_07_publicar.py", "Cuadernos nuevos", 32],
    ["nb_ini_ciclo.py", "Cuadernos nuevos", 30], ["nb_registrar_aprobacion.py", "Cuadernos nuevos", 30], ["nb_aprobar.py", "Cuadernos nuevos", 27],
    ["nb_e2_consolidacion.py", "Cuadernos nuevos", 27], ["nb_00_focalizacion.py", "Cuadernos nuevos", 23], ["nb_04_fuente_recursos.py", "Cuadernos nuevos", 23],
    ["nb_05_listados.py", "Cuadernos nuevos", 23], ["nb_01_titular.py", "Cuadernos nuevos", 22], ["nb_e2_cruce_poblacional.py", "Cuadernos nuevos", 22],
    ["nb_e2_cruce_validacion.py", "Cuadernos nuevos", 22], ["nb_02_medio_pago.py", "Cuadernos nuevos", 21], ["nb_03_monto.py", "Cuadernos nuevos", 21],
    ["nb_orq_e1.py", "Cuadernos nuevos", 15], ["nb_orq_e2.py", "Cuadernos nuevos", 15], ["nb_orq_liq.py", "Cuadernos nuevos", 15],
    ["nb_orq_listados.py", "Cuadernos nuevos", 15],
    ["nb_e1_plata.py", "Cuadernos ajustados", 16], ["nb_e1_mdm.py", "Cuadernos ajustados", 15], ["nb_e1_bronce.py", "Cuadernos ajustados", 12],
    ["nb_e1_oro.py", "Cuadernos ajustados", 6],
    ["tests/test_e2e.py", "Pruebas", 109], ["tests/test_ctl.py", "Pruebas", 67],
    ["ddl/01_ctl_param.sql", "Datos y DDL", 8],
    ["docs/historial.html", "Documentación", 118], ["pipelines/README.md", "Documentación", 33], ["README.md", "Documentación", 11],
    ["CHANGELOG.md", "Documentación", 1],
]


def svg_incrustado(nombre: str) -> str:
    s = (DIAG / f"{nombre}.svg").read_text(encoding="utf-8")
    s = re.sub(r"<\?xml[^>]*\?>|<!DOCTYPE[^>]*>", "", s).strip()
    # imágenes PNG de respaldo del texto (pesan ~500 KB por diagrama); el texto real va en foreignObject
    s = re.sub(r'<image [^>]*xlink:href="data:image/png;base64,[^"]*"[^>]*/>', "", s)
    # tamaño fluido: se conserva el viewBox
    w = re.search(r'<svg[^>]*\swidth="([\d.]+)px"', s)
    h = re.search(r'<svg[^>]*\sheight="([\d.]+)px"', s)
    if "viewBox" not in s.split(">", 1)[0] and w and h:
        s = s.replace("<svg ", f'<svg viewBox="0 0 {w.group(1)} {h.group(1)}" ', 1)
    s = re.sub(r'(<svg[^>]*?)\swidth="[^"]*"', r"\1", s, count=1)
    s = re.sub(r'(<svg[^>]*?)\sheight="[^"]*"', r"\1", s, count=1)
    return s


def main():
    plantilla = (AQUI / "_plantilla_cambios.html").read_text(encoding="utf-8")
    html = (plantilla.replace("@@SVG1@@", svg_incrustado("01-ciclo-extremo-a-extremo"))
            .replace("@@SVG2@@", svg_incrustado("02-capas-del-repositorio"))
            .replace("@@SVG3@@", svg_incrustado("03-control-humano"))
            .replace("@@PASOS@@", json.dumps(PASOS, ensure_ascii=False))
            .replace("@@ARCHIVOS@@", json.dumps(ARCHIVOS, ensure_ascii=False)))
    (AQUI / "cambios_pr1.html").write_text(html, encoding="utf-8")
    print(f"cambios_pr1.html: {len(html) // 1024} KB")


if __name__ == "__main__":
    main()
