"""El evaluador es lo que decide PASA/FALLA: se prueba sin laboratorio."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "infra"))

from evaluar import Medicion, evaluar  # noqa: E402

C_EXIT0 = {"tipo": "exit_code", "valor": 0}
C_EXIT_NO0 = {"tipo": "exit_code", "valor": "distinto_de_0"}


def test_exit_code_cero_pasa_y_distinto_de_cero_falla():
    assert evaluar([C_EXIT0], Medicion(codigos={"principal": 0}))[0] == "PASA"
    assert evaluar([C_EXIT0], Medicion(codigos={"principal": 1}))[0] == "FALLA"
    assert evaluar([C_EXIT_NO0], Medicion(codigos={"principal": 1}))[0] == "PASA"
    assert evaluar([C_EXIT_NO0], Medicion(codigos={"principal": 0}))[0] == "FALLA"


def test_exit_code_con_comando_adicional_usa_su_propio_codigo():
    c = {"tipo": "exit_code", "valor": "distinto_de_0", "comando_adicional": "nc -zv x 22"}
    assert evaluar([c], Medicion(codigos={"principal": 0, "nc -zv x 22": 1}))[0] == "PASA"
    assert evaluar([c], Medicion(codigos={"principal": 0}))[0] == "NO_APLICA"     # no se midió: no se da por cumplido


def test_regex_con_y_sin_coincidencia_esperada():
    pos = {"tipo": "regex", "sobre": "stdout", "patron": r"^403$"}
    neg = {"tipo": "regex", "sobre": "stdout", "patron": r"open", "debe_coincidir": False}
    assert evaluar([pos], Medicion(salidas={"stdout": "403"}))[0] == "PASA"
    assert evaluar([pos], Medicion(salidas={"stdout": "200"}))[0] == "FALLA"
    assert evaluar([neg], Medicion(salidas={"stdout": "22/tcp closed"}))[0] == "PASA"
    assert evaluar([neg], Medicion(salidas={"stdout": "22/tcp open ssh"}))[0] == "FALLA"


def test_regex_sobre_una_fuente_ausente_no_se_da_por_cumplida():
    c = {"tipo": "regex", "sobre": "alerta_wazuh", "patron": "level"}
    r, rs, motivo = evaluar([c], Medicion(no_evaluable={"alerta_wazuh": "Wazuh no desplegado"}))
    assert r == "NO_APLICA" and "Wazuh no desplegado" in motivo


def test_umbral_y_contador():
    u = {"tipo": "umbral", "metrica": "convergencia_s", "operador": "<=", "valor": 60}
    assert evaluar([u], Medicion(medidas={"convergencia_s": 31.2}))[0] == "PASA"
    assert evaluar([u], Medicion(medidas={"convergencia_s": 75}))[0] == "FALLA"
    k = {"tipo": "contador", "metrica": "paquetes", "operador": ">", "valor": 0}
    assert evaluar([k], Medicion(medidas={"paquetes": 0}))[0] == "FALLA"
    assert evaluar([k], Medicion(medidas={"paquetes": 7}))[0] == "PASA"


def test_un_criterio_manual_nunca_cuenta_como_cumplido():
    r, _, motivo = evaluar([C_EXIT0, {"tipo": "manual", "descripcion": "navegador"}], Medicion(codigos={"principal": 0}))
    assert r == "PARCIAL" and "intervención humana" in motivo


def test_una_falla_gana_sobre_lo_no_evaluado():
    r, _, _ = evaluar([C_EXIT0, {"tipo": "manual"}], Medicion(codigos={"principal": 2}))
    assert r == "FALLA"


def test_una_medicion_vacia_es_parcial_aunque_todo_pase():
    r, _, motivo = evaluar([C_EXIT0], Medicion(codigos={"principal": 0}, vacia="nada cruzó la VPN"))
    assert r == "PARCIAL" and "nada cruzó la VPN" in motivo


def test_todo_lo_definido_en_pruebas_yaml_es_evaluable_por_tipo():
    from celeris_infra import Infra
    tipos = {c["tipo"] for t in Infra.cargar().pruebas.values() for c in t["criterio_aprobacion"]}
    assert tipos <= {"exit_code", "regex", "umbral", "contador", "manual"}


def test_toda_prueba_vigente_del_modo_l_tiene_caso_o_un_no_aplica_con_motivo():
    """v0.4: ninguna prueba con L en sus modos queda sin caso ni motivo; no hay casos de pruebas retiradas; T50, T53 y T54 nunca se ejecutan en el Modo L."""
    import sys
    from pathlib import Path
    raiz = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(raiz / "infra"))
    from celeris_infra import Infra
    import casos
    infra = Infra.cargar()
    con_l = {t["id"] for t in infra.pruebas.values() if "L" in t["modos"]}
    assert con_l - set(casos.CASOS) - set(casos.NO_APLICA_L) == set(), "pruebas del Modo L sin caso ni motivo"
    assert set(casos.CASOS) <= set(infra.pruebas), "hay casos de pruebas retiradas"
    for tid in ("T50", "T53", "T54"):
        motivo, donde = casos.NO_APLICA_L[tid]
        assert "requiere la consola (CE02, S2)" in motivo and tid not in casos.CASOS and "L" not in donde
    for tid in ("T51", "T52", "T55", "T56", "T57", "T58", "T60"):
        assert tid in casos.CASOS
