"""V-40 a V-43: cada chequeo detecta la alteración que dice detectar (no solo pasa sobre el estado actual)."""
import copy

import pytest

import validate as v
from celeris_infra import Infra
from gen import nftables, vpn

PARES = v.PARES_AWS_DOC


def errores(hallazgos):
    return [h.mensaje for h in hallazgos if h.nivel == "error"]


def ruleset(infra, modo="piloto", ventana=False):
    return nftables.generar(infra, modo=modo, ventana=ventana, aws_peers=PARES)


def revisar(infra, texto, modo="piloto", ventana=False):
    return errores(v.ruleset_contra_inventario(infra, texto, modo, ventana))


# ------------------------------------------------------------------------------------------ V-40

@pytest.mark.parametrize("modo,ventana", [("piloto", False), ("gestionado", False), ("piloto", True)])
def test_el_ruleset_actual_cumple_el_inventario(infra, modo, ventana):
    assert revisar(infra, ruleset(infra, modo, ventana), modo, ventana) == []


def test_v40_detecta_un_puerto_de_mas(infra):
    extra = '    iifname "vlan30" oifname "wan" tcp dport 22 counter accept comment "F1 LAB,LAB-TEST > EDGE01,EDGE02 proxy tcp/3128"\n'
    texto = ruleset(infra).replace("  chain forward {\n", "  chain forward {\n" + extra, 1)
    assert any("F1" in m and "puertos abiertos fuera del inventario" in m for m in revisar(infra, texto))


def test_v40_detecta_una_regla_que_acepta_todo(infra):
    texto = ruleset(infra).replace("  chain forward {\n", "  chain forward {\n    counter accept\n", 1)
    assert any("acepta todo sin condición" in m for m in revisar(infra, texto))


def test_v40_detecta_un_accept_sin_flujo_ni_rotulo(infra):
    texto = ruleset(infra).replace("  chain forward {\n", '  chain forward {\n    ip saddr 10.20.32.0/22 tcp dport 8080 counter accept comment "regla suelta"\n', 1)
    assert any("sin flujo F-nn" in m for m in revisar(infra, texto))


def test_v40_detecta_un_flujo_permitido_sin_regla(infra):
    texto = "\n".join(linea for linea in ruleset(infra).splitlines() if 'comment "F9 ' not in linea)
    assert any("F9" in m and "no tiene regla" in m for m in revisar(infra, texto))


def test_v40_detecta_un_bloqueo_convertido_en_accept(infra):
    texto = ruleset(infra).replace("counter drop comment \"F7", "counter accept comment \"F7")
    assert any("F7" in m and "lo acepta" in m for m in revisar(infra, texto))


def test_v40_detecta_f6_en_modo_gestionado(infra):
    assert any("F6" in m for m in revisar(infra, ruleset(infra, "piloto"), "gestionado"))


def test_v40_detecta_f24_sin_ventana(infra):
    assert any("F24" in m for m in revisar(infra, ruleset(infra, "piloto", True), "piloto", False))


def test_v40_detecta_politica_accept(infra):
    texto = ruleset(infra).replace("hook forward priority 0; policy drop;", "hook forward priority 0; policy accept;", 1)
    assert any("forward no tiene política drop" in m for m in revisar(infra, texto))


def test_v40_detecta_un_flujo_que_no_esta_en_el_inventario(infra):
    texto = ruleset(infra).replace("  chain forward {\n", '  chain forward {\n    tcp dport 99 counter accept comment "F99 inventado"\n', 1)
    assert any("F99" in m for m in revisar(infra, texto))


def test_v40_detecta_dnat_con_origen_no_internet(infra):
    texto = ruleset(infra).replace("  chain prerouting {\n", '  chain prerouting {\n    tcp dport 3128 dnat to 10.20.60.10:3128 comment "F1 LAB > EDGE"\n', 1)
    assert any("F1 tiene DNAT" in m for m in revisar(infra, texto))


def test_v40_responde_a_un_cambio_del_inventario(infra):
    """Si el inventario pasa F9 a otro puerto y el ruleset no se regenera, el validador lo ve."""
    viejo = ruleset(infra)
    inv = copy.deepcopy(infra.inv)
    f9 = next(f for f in inv["flujos"] if f["id"] == "F9")
    f9["protocolos"][0]["puertos"] = [9443]
    otro = Infra(inv, infra.pru, infra.traz)
    assert any("F9" in m for m in revisar(otro, viejo))


# ------------------------------------------------------------------------------------------ V-41

def archivos_vpn(infra, lado):
    return vpn.swanctl(infra, lado, PARES), vpn.frr(infra, lado), vpn.vti_up(infra, lado, PARES)


@pytest.mark.parametrize("lado", ["fw01", "vgw"])
def test_la_vpn_generada_cumple_el_inventario(infra, lado):
    assert errores(v.vpn_contra_inventario(infra, lado, *archivos_vpn(infra, lado))) == []


@pytest.mark.parametrize("lado,cambio,esperado", [
    ("fw01", ("swanctl", "dpd_delay = 10s", "dpd_delay = 30s"), "dpd_delay"),
    ("fw01", ("swanctl", "rekey_time = 28800s", "rekey_time = 3600s"), "rekey_time"),
    ("fw01", ("swanctl", "aes256gcm16-prfsha384-ecp384", "aes128gcm16-prfsha256-ecp256"), "proposals"),
    ("fw01", ("swanctl", "mark_in = 2", "mark_in = 7"), "mark_in"),
    ("vgw", ("swanctl", "start_action = none", "start_action = start"), "start_action"),
    ("fw01", ("frr", "router bgp 65020", "router bgp 65099"), "router bgp"),
    ("fw01", ("frr", "remote-as 64512", "remote-as 64999"), "remote-as"),
    ("fw01", ("frr", "  maximum-paths 1\n", ""), "maximum-paths"),
    ("fw01", ("frr", "timers 10 30", "timers 60 180"), "timers"),
    ("fw01", ("frr", "  network 10.20.0.0/16", "  network 10.20.0.0/14"), "redes anunciadas"),
    ("fw01", ("frr", "route-map PREPEND-TUNEL2 out", "route-map OTRO out"), "prepending"),
    ("fw01", ("vti", "mtu 1400 up", "mtu 1500 up"), "MTU"),
])
def test_v41_detecta_una_alteracion(infra, lado, cambio, esperado):
    sw, frr, vti = archivos_vpn(infra, lado)
    donde, viejo, nuevo = cambio
    if donde == "swanctl":
        assert viejo in sw, viejo
        sw = sw.replace(viejo, nuevo)
    elif donde == "frr":
        assert viejo in frr, viejo
        frr = frr.replace(viejo, nuevo)
    else:
        assert viejo in vti, viejo
        vti = vti.replace(viejo, nuevo)
    assert any(esperado in m for m in errores(v.vpn_contra_inventario(infra, lado, sw, frr, vti)))


def test_v41_responde_a_un_cambio_del_inventario(infra):
    sw, frr, vti = archivos_vpn(infra, "fw01")
    inv = copy.deepcopy(infra.inv)
    inv["vpn"]["dpd"]["intervalo_s"] = 15
    otro = Infra(inv, infra.pru, infra.traz)
    assert any("dpd_delay" in m for m in errores(v.vpn_contra_inventario(otro, "fw01", sw, frr, vti)))


# ------------------------------------------------------------------------------------------ V-42

def resultados(**estados):
    return {"meta": {"modo": "L (emulación local con containerlab)"}, "resultados": [{"id": k, "resultado": e} for k, e in estados.items()]}


def test_la_marca_critica_sigue_la_regla_documentada(infra):
    for t in infra.pruebas.values():
        assert isinstance(t["critica"], bool)
        assert t["critica"] == (t["categoria"] in {"segmentacion", "vpn", "cifrado"}), t["id"]


def test_v42_falla_con_una_prueba_critica_en_falla(infra):
    assert any("T10" in m for m in errores(v.evaluar_resultados(infra, resultados(T10="FALLA"), "x")))


def test_v42_una_falla_no_critica_es_advertencia(infra):
    hs = v.evaluar_resultados(infra, resultados(T07="FALLA"), "x")
    assert errores(hs) == [] and any(h.nivel == "advertencia" and "T07" in h.mensaje for h in hs)


def test_v42_una_critica_parcial_no_cuenta_como_pasa(infra):
    hs = v.evaluar_resultados(infra, resultados(T10="PARCIAL"), "x")
    assert errores(hs) == [] and any(h.nivel == "advertencia" and "T10" in h.mensaje for h in hs)


def test_v42_una_prueba_critica_fuera_del_modo_no_genera_aviso(infra):
    hs = v.evaluar_resultados(infra, resultados(T01="NO_APLICA"), "x")        # T01 es de los modos A y H
    assert not any("T01" in h.mensaje for h in hs)


def test_v42_una_prueba_desconocida_es_error(infra):
    assert any("T99" in m for m in errores(v.evaluar_resultados(infra, resultados(T99="PASA"), "x")))


def test_v42_cambiar_la_marca_critica_cambia_el_veredicto(infra):
    pru = copy.deepcopy(infra.pru)
    next(t for t in pru["pruebas"] if t["id"] == "T07")["critica"] = True
    otro = Infra(infra.inv, pru, infra.traz)
    assert any("T07" in m for m in errores(v.evaluar_resultados(otro, resultados(T07="FALLA"), "x")))


def test_v42_sobre_los_ultimos_resultados_versionados(infra):
    ruta, datos = v.resultados_mas_recientes(infra.raiz)
    assert datos is not None, "no hay evidencias/*/resultados.json versionado"
    assert errores(v.evaluar_resultados(infra, datos, ruta.parent.name)) == []


# ------------------------------------------------------------------------------------------ V-43

def test_v43_pasa_con_los_artefactos_versionados(infra):
    assert errores(v.v43(infra)) == []


def test_v43_detecta_un_artefacto_desactualizado(infra):
    inv = copy.deepcopy(infra.inv)
    inv["aws"]["etiquetas"]["Ttl_por_defecto"] = "8h"
    otro = Infra(inv, infra.pru, infra.traz)
    assert any("diseno.auto.tfvars.json" in m for m in errores(v.v43(otro)))
