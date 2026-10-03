"""Arma docs/pr1_changes.html: incrusta los SVG exportados de docs/diagrams/*.drawio en la plantilla.

Si se edita un diagrama en draw.io:
  1) exportar a SVG con el mismo nombre (Archivo > Exportar como > SVG, o la CLI: draw.io -x -f svg -o x.svg x.drawio);
  2) python docs/build_pr1_changes.py
Los pasos clicables del ciclo son las celdas s01..s13 del diagrama 01 (el id de celda debe coincidir con STEPS)."""
import json
import pathlib
import re

HERE = pathlib.Path(__file__).parent
DIAG = HERE / "diagrams"

STEPS = {
    "s01": dict(type="new", title="1 · Abrir ciclo", files=["nb_init_cycle.py", "ddl/01_ctl_param.sql"],
        what="Cuaderno nuevo que registra en ctl.cycle el corte, la fecha de corte y la versión de cada fuente. Rechaza un cycle_id que ya existe.",
        why="El §18.3 pide que el único parámetro de los cuadernos sea el cycle_id. Faltaba un lugar donde vivieran los demás datos del ciclo.",
        purpose="Que cada cuaderno se pueda ejecutar con solo el cycle_id y que el informe diga con qué versión de fuentes se generó.",
        contribution="Es la puerta de entrada trazable: todo lo que ocurre después se amarra a este registro.",
        limit="Repetir una corrida exige un cycle_id nuevo (por ejemplo 2026-09-r1); reutilizarlo duplicaría filas."),
    "s02": dict(type="mod", title="2 · Bronce", files=["nb_e1_bronze.py"],
        what="El corte ya no es un parámetro propio: se lee de ctl.cycle a partir del cycle_id.",
        why="Para cumplir que el cycle_id sea el único parámetro, sin cambiar lo que Bronce guarda.",
        purpose="Que Bronce siga entregando evidencia probatoria (entidad, fecha, número de registros y SHA-256) sin depender de parámetros sueltos.",
        contribution="Mantiene intacta la evidencia de lo que llegó, que es lo que más pesa en una auditoría."),
    "s03": dict(type="mod", title="3 · Plata + cuarentena", files=["nb_e1_silver.py", "cycle.py"],
        what="La etiqueta del corte pasa a la columna corte y la fecha de corte de la fuente ya no se sobreescribe. Las escrituras usan esquema explícito.",
        why="Era un defecto: Plata pisaba cutoff_date y la fuente de validación perdía su fecha real, que los cruces necesitan. Además Spark no puede crear una tabla con una columna que solo trae None.",
        purpose="Que lo normalizado llegue completo a las etapas siguientes y que la cuarentena conserve la causa de cada rechazo.",
        contribution="Las cifras que verá el líder de datos en C1 salen de datos íntegros."),
    "s04": dict(type="mod", title="4 · MDM", files=["nb_e1_mdm.py", "mdm.py"],
        what="Mismos ajustes de corte y escritura. La lógica del maestro de personas y hogares ya estaba en el primer commit.",
        why="Mantener una sola convención de corte en las cuatro capas.",
        purpose="Que cada persona y cada hogar tengan una clave estable aunque aparezcan en varias fuentes.",
        contribution="Sin una clave de persona confiable los cruces y el titular por hogar no serían posibles.",
        limit="Las reglas de coincidencia y supervivencia son ilustrativas hasta resolver el pendiente G6."),
    "s05": dict(type="mod", title="5 · Oro", files=["nb_e1_gold.py"],
        what="Filtra por la columna corte y escribe una tabla por fuente con person_id e household_id ya asignados.",
        why="Coherencia con el cambio de Plata.",
        purpose="Ser la única entrada de los cruces: ningún cuaderno posterior lee Bronce ni Plata.",
        contribution="Cierra la Etapa 1 con fuentes certificadas a nivel de registro."),
    "s06": dict(type="ctrl", title="6 · Control C1", files=["nb_ctl_summary.py", "controls.py", "ctl.approvals"],
        what="Cuaderno que arma el resumen del control (entregas con su huella, cuarentena por causa, registros en Oro), deja una solicitud PENDIENTE y devuelve el resumen al pipeline.",
        why="El §19 exige un control humano entre etapas. Antes de este PR no existía ninguno.",
        purpose="Que el líder de datos decida con cifras y no a ciegas, y que quede registrado quién decidió y cuándo.",
        contribution="Evita gastar cómputo en cruces si las fuentes están mal.",
        limit="El aprobador depende de la actividad de aprobación de Data Factory o del plan B; falta probarlo en el trial (pendiente G10)."),
    "s07": dict(type="new", title="7 · Base de cruces", files=["crosschecks.py", "nb_e2_crosscheck_population.py", "nb_e2_crosscheck_validation.py", "nb_e2_consolidation.py"],
        what="Una fila por persona y ciclo con los campos de la Tabla 7: persona, hogar, Sisbén, marcas de validación (encontrado, valor, fecha) y trazabilidad.",
        why="Es la Etapa 2 del §17. La base registra hechos, no decisiones.",
        purpose="Separar lo que se sabe de cada persona de lo que se decide después, para que las reglas de liquidación se puedan cambiar sin tocar los cruces.",
        contribution="Es el contrato de datos entre la ingesta y la liquidación.",
        limit="Rol en el hogar y datos financieros quedan vacíos: la PoC no tiene fuente para ellos y no se inventan."),
    "s08": dict(type="ctrl", title="8 · Control C2", files=["nb_ctl_summary.py", "crosschecks.match_pct"],
        what="Resumen con el universo y el porcentaje de personas encontradas en la fuente de validación.",
        why="Tabla 9: el analista líder revisa el porcentaje de coincidencia antes de liquidar.",
        purpose="Detectar una fuente de validación incompleta antes de que bloquee o deje pasar a la gente equivocada.",
        contribution="Segunda puerta humana, ahora sobre la calidad del cruce."),
    "s09": dict(type="new", title="9 · Liquidación", files=["settlement.py", "nb_00_targeting.py", "nb_01_holder.py", "nb_02_payment_method.py", "nb_03_amount.py", "nb_04_funding_source.py"],
        what="Un motor que lee criterios y reglas de las tablas param.* y decide elegibles y excluidos con su causal, un titular por hogar, el medio de pago, el monto y la fuente de recursos con su techo.",
        why="El §18 pide que los criterios sean datos y no código. El orden respeta la Tabla 8: el monto va antes de la fuente de recursos.",
        purpose="Cambiar una regla de focalización, un monto o un techo editando una tabla, sin tocar ni volver a probar el código.",
        contribution="Convierte los cruces en pagos liquidados y en exclusiones explicadas.",
        limit="Los criterios, las reglas de bloqueo, la regla de titular, los montos y los techos son de ejemplo (G3 a G5); el medio de pago es un stub porque no hay datos financieros."),
    "s10": dict(type="ctrl", title="10 · Control C3", files=["nb_ctl_summary.py", "controls.summary_c3"],
        what="Resumen con elegibles, exclusiones por causal, monto total frente al techo y número de pagos que superan el techo.",
        why="Tabla 9: el líder funcional revisa causales y montos antes de generar los listados.",
        purpose="Atrapar un error de dinero antes de que quede en un archivo para el operador.",
        contribution="Es el control con más riesgo financiero del ciclo."),
    "s11": dict(type="new", title="11 · Listados + informe", files=["nb_05_payment_lists.py", "nb_06_report.py", "settlement.build_report"],
        what="La sábana del ciclo y un informe con conteos, exclusiones por causal, totales por operador y fuente, la verificación de que la suma de los listados es igual a la liquidación y el registro de las aprobaciones.",
        why="El §18.4 define el contenido del informe de generación.",
        purpose="Dar al responsable del programa algo concreto que aprobar, y dar al documento la evidencia para la Tabla 4.",
        contribution="El informe avisa si se usaron parámetros ilustrativos, para que no pasen por reales.",
        limit="El informe se genera antes de C4 y se regenera al cierre para incluir esa aprobación."),
    "s12": dict(type="ctrl", title="12 · Control C4", files=["nb_ctl_summary.py", "nb_record_approval.py", "nb_approve.py"],
        what="Resumen del informe y registro de la decisión final. Incluye el plan B: nb_approve para decidir cuando el tenant no tiene buzón de Microsoft 365.",
        why="Tabla 9: el responsable del programa autoriza lo que se va a publicar.",
        purpose="Que nadie reciba un pago que el responsable no haya autorizado, con constancia de quién y cuándo.",
        contribution="Última puerta antes de la publicación. Si el plazo vence, cuenta como rechazo."),
    "s13": dict(type="new", title="13 · Publicación", files=["nb_07_publish.py", "settlement.publish"],
        what="Publica un archivo por operador y fuente en una carpeta por ciclo, con un manifiesto de huellas SHA-256. Se niega a publicar si algún control no está aprobado.",
        why="El §18.4 pide publicar de forma que se pueda verificar que el archivo no cambió.",
        purpose="Que el listado entregado al operador se pueda comprobar byte a byte contra lo aprobado.",
        contribution="Cierra el ciclo con una salida verificable.",
        limit="Se publica en OneLake y no en Azure Storage con inmutabilidad; es una diferencia deliberada con producción."),
}

FILES = [
    ["img_lib/settlement.py", "Lógica (img_lib)", 166], ["img_lib/controls.py", "Lógica (img_lib)", 63],
    ["img_lib/crosschecks.py", "Lógica (img_lib)", 56], ["img_lib/cycle.py", "Lógica (img_lib)", 55],
    ["img_lib/metrics.py", "Lógica (img_lib)", 53], ["img_lib/dag.py", "Lógica (img_lib)", 48],
    ["img_lib/illustrative.py", "Lógica (img_lib)", 25],
    ["nb_ctl_summary.py", "Cuadernos nuevos", 44], ["nb_06_report.py", "Cuadernos nuevos", 36], ["nb_07_publish.py", "Cuadernos nuevos", 32],
    ["nb_init_cycle.py", "Cuadernos nuevos", 30], ["nb_record_approval.py", "Cuadernos nuevos", 30], ["nb_approve.py", "Cuadernos nuevos", 27],
    ["nb_e2_consolidation.py", "Cuadernos nuevos", 27], ["nb_00_targeting.py", "Cuadernos nuevos", 23], ["nb_04_funding_source.py", "Cuadernos nuevos", 23],
    ["nb_05_payment_lists.py", "Cuadernos nuevos", 23], ["nb_01_holder.py", "Cuadernos nuevos", 22], ["nb_e2_crosscheck_population.py", "Cuadernos nuevos", 22],
    ["nb_e2_crosscheck_validation.py", "Cuadernos nuevos", 22], ["nb_02_payment_method.py", "Cuadernos nuevos", 21], ["nb_03_amount.py", "Cuadernos nuevos", 21],
    ["nb_orch_e1.py", "Cuadernos nuevos", 15], ["nb_orch_e2.py", "Cuadernos nuevos", 15], ["nb_orch_settlement.py", "Cuadernos nuevos", 15],
    ["nb_orch_payment_lists.py", "Cuadernos nuevos", 15],
    ["nb_e1_silver.py", "Cuadernos ajustados", 16], ["nb_e1_mdm.py", "Cuadernos ajustados", 15], ["nb_e1_bronze.py", "Cuadernos ajustados", 12],
    ["nb_e1_gold.py", "Cuadernos ajustados", 6],
    ["tests/test_e2e.py", "Pruebas", 109], ["tests/test_ctl.py", "Pruebas", 67],
    ["ddl/01_ctl_param.sql", "Datos y DDL", 8],
    ["docs/timeline.html", "Documentación", 118], ["pipelines/README.md", "Documentación", 33], ["README.md", "Documentación", 11],
    ["CHANGELOG.md", "Documentación", 1],
]


def embedded_svg(name: str) -> str:
    s = (DIAG / f"{name}.svg").read_text(encoding="utf-8")
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
    template = (HERE / "_pr1_changes_template.html").read_text(encoding="utf-8")
    html = (template.replace("@@SVG1@@", embedded_svg("01-end-to-end-cycle"))
            .replace("@@SVG2@@", embedded_svg("02-repository-layers"))
            .replace("@@SVG3@@", embedded_svg("03-human-control"))
            .replace("@@STEPS@@", json.dumps(STEPS, ensure_ascii=False))
            .replace("@@FILES@@", json.dumps(FILES, ensure_ascii=False)))
    (HERE / "pr1_changes.html").write_text(html, encoding="utf-8")
    print(f"pr1_changes.html: {len(html) // 1024} KB")


if __name__ == "__main__":
    main()
