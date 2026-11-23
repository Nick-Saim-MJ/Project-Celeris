"""Ruleset de fw01-sim: política drop, una regla por flujo, bloqueos explícitos y regresión por snapshot."""
import re

import pytest

from conftest import AWS_PEERS, comparar_snapshot
from gen import nftables


def gen(x, **kw):
    kw.setdefault("aws_peers", AWS_PEERS)
    return nftables.generar(x, **kw)


def reglas(texto):
    return [l.strip() for l in texto.splitlines() if l.strip() and not l.strip().startswith("#")]


def test_politica_drop_en_input_forward_output(infra):
    t = gen(infra)
    for cadena in ("input", "forward", "output"):
        bloque = re.search(rf"chain {cadena} \{{\n(.*?)\n  \}}", t, re.S).group(1)
        assert "policy drop;" in bloque
        assert 'log prefix "fw01sim DENEGADO' in bloque          # registro de denegaciones
        assert bloque.rstrip().endswith("counter drop")


def test_cada_flujo_permitido_tiene_regla_o_nota(infra):
    t = gen(infra, ventana=True)
    con_regla = nftables.flujos_con_regla(t)
    for f in infra.flujos.values():
        if f["estado"] != "activo":
            continue
        assert f["id"] in con_regla or re.search(rf"# {f['id']}:", t), f"{f['id']} no tiene regla ni nota en el ruleset"


def test_no_hay_reglas_de_flujos_inexistentes(infra):
    t = gen(infra, ventana=True)
    assert nftables.flujos_con_regla(t) <= {f["id"] for f in infra.flujos.values() if f["estado"] == "activo"}
    assert "F4" not in nftables.flujos_con_regla(t)            # F4 está reservado


def test_toda_regla_accept_tiene_comentario_y_no_es_any_any(infra):
    t = gen(infra, ventana=True)
    forward = re.search(r"chain forward \{\n(.*?)\n  \}", t, re.S).group(1)
    for r in reglas(t):
        if "counter accept" in r:
            assert "comment" in r, f"regla accept sin comentario: {r}"
    for r in reglas(forward):
        if "counter accept" in r and "(sin F-nn" not in r:
            # ninguna regla «any → any» entre zonas internas (D1.13, criterio 2)
            assert ("saddr" in r or "iifname" in r) and ("daddr" in r or "oifname" in r), f"regla demasiado amplia: {r}"


def test_f7_se_bloquea_explicitamente_antes_de_los_accept(infra):
    t = gen(infra)
    fwd = re.search(r"chain forward \{\n(.*?)\n  \}", t, re.S).group(1).splitlines()
    idx_f7 = [i for i, l in enumerate(fwd) if 'comment "F7' in l]
    idx_accept = [i for i, l in enumerate(fwd) if "counter accept" in l and 'comment "F' in l]
    assert len(idx_f7) == 2 and all("counter drop" in fwd[i] for i in idx_f7)   # udp/443+853 e IPv6
    assert max(idx_f7) < min(idx_accept)
    assert "udp . 443" in fwd[idx_f7[0]] and "tcp . 853" in fwd[idx_f7[0]] and "meta nfproto ipv6" in fwd[idx_f7[1]]


def test_modo_gestionado_omite_f6_y_piloto_lo_incluye(infra):
    assert "F6" in nftables.flujos_con_regla(gen(infra, modo="piloto"))
    assert "F6" not in nftables.flujos_con_regla(gen(infra, modo="gestionado"))
    assert "F7" in nftables.flujos_con_regla(gen(infra, modo="gestionado"))   # F7 aplica en ambos modos


def test_f24_solo_con_ventana_autorizada(infra):
    sin, con = gen(infra), gen(infra, ventana=True)
    assert "F24" not in nftables.flujos_con_regla(sin) and "ventana autorizada" in sin
    assert "dnat to 10.20.41.20:2222" in con and "dnat to 10.20.41.20:23" in con
    assert "F24" in nftables.flujos_con_regla(con)


def test_dnat_del_portal_apunta_a_portal01(infra):
    """v0.4: el FortiGate hace NAT 1:1 de 203.0.113.10 hacia la WAN de FW01 (10.20.0.2); FW01 hace DNAT hacia PORTAL01."""
    t = gen(infra)
    assert "ip daddr 10.20.0.2 tcp dport 443 dnat to 10.20.40.10:443" in t
    assert "ip daddr 10.20.0.2 tcp dport 80 dnat to 10.20.40.10:80" in t


def test_flujos_retirados_y_que_no_pasan_por_fw01_no_generan_regla(infra):
    """v0.4: F15, F19 y F22 (intra-VLAN) están retirados; F29 entra por la IP pública de EC2-GW y no pasa por FW01."""
    t = gen(infra)
    for fid in ("F9", "F11", "F12", "F15", "F16", "F17", "F19", "F22", "F29"):
        assert fid not in nftables.flujos_con_regla(t)
    assert "# F29: no pasa por FW01" in t


def test_lab_no_tiene_reglas_hacia_mgmt_storage_backup_aws(infra):
    """Prueba negativa estática (matriz D1.8): ninguna regla accept con origen LAB (10.20.32.0/22) llega a esas zonas."""
    revisadas = 0
    for r in reglas(gen(infra, ventana=True)):
        m = re.search(r"ip saddr (\{[^}]*\}|\S+) ip daddr (\{[^}]*\}|\S+)", r)
        if "counter accept" not in r or not m or "10.20.32.0/22" not in m.group(1):
            continue
        revisadas += 1
        for prohibido in ("10.20.10.", "10.20.70.", "10.20.71.", "10.30."):
            assert prohibido not in m.group(2), r
    assert revisadas >= 3          # F1, F2 y F3 al menos


def test_origen_internet_solo_en_f21_y_f24(infra):
    for r in reglas(gen(infra, ventana=True)):
        if 'iifname "wan"' in r and "counter accept" in r and "VPN" not in r:
            assert re.search(r'comment "F(21|24) ', r), r


def test_regresion_cambiar_un_flujo_cambia_el_ruleset(infra, mutar):
    base = gen(infra)

    def cambiar(inv):
        next(f for f in inv["flujos"] if f["id"] == "F5")["protocolos"][0]["puertos"][0] = 8443
    nuevo = gen(mutar(cambiar))
    assert nuevo != base
    assert 'tcp dport 8443 counter accept comment "F5 ' in nuevo and 'tcp dport 443 counter accept comment "F5 ' not in nuevo


def test_regresion_quitar_un_flujo_quita_su_regla(infra, mutar):
    x = mutar(lambda inv: inv["flujos"].__setitem__(slice(None), [f for f in inv["flujos"] if f["id"] != "F10"]))
    assert "F10" in nftables.flujos_con_regla(gen(infra))
    assert "F10" not in nftables.flujos_con_regla(gen(x))


def test_regresion_un_flujo_nuevo_aparece_en_el_ruleset(infra, mutar):
    def agregar(inv):
        f = next(f for f in inv["flujos"] if f["id"] == "F4")
        f.update({"estado": "activo", "origen": ["LAB"], "destino": ["MGMT"], "protocolos": [{"proto": "tcp", "puertos": [22]}],
                  "accion": "permitir", "modo": "ambos", "regla_fw": "F4 LAB > MGMT ssh tcp/22"})
    assert "F4" in nftables.flujos_con_regla(gen(mutar(agregar)))
    assert "F4" not in nftables.flujos_con_regla(gen(infra))


@pytest.mark.parametrize("nombre,kw", [("fw01sim_piloto.nft", {}), ("fw01sim_gestionado.nft", {"modo": "gestionado"}),
                                        ("fw01sim_piloto_ventana.nft", {"ventana": True})])
def test_snapshot_del_ruleset(infra, nombre, kw):
    comparar_snapshot(nombre, gen(infra, **kw))


def test_la_salida_es_determinista(infra):
    assert gen(infra) == gen(infra)


def test_antispoofing_de_la_wan_excluye_el_transito_y_el_wifi(infra):
    """D1.13 v0.4: se bloquean bogons y redes privadas entrantes, excepto 10.20.0.0/29 y 172.16.0.0/16 (solo F31/F32)."""
    import ipaddress
    linea = next(l for l in gen(infra).splitlines() if "Anti-spoofing WAN" in l and "{" in l)
    redes = [ipaddress.ip_network(r.strip()) for r in linea.split("{")[1].split("}")[0].split(",")]
    cubre = lambda ip: any(ipaddress.ip_address(ip) in r for r in redes)
    assert not cubre("10.20.0.1") and not cubre("172.16.0.50")
    assert cubre("172.17.0.1") and cubre("192.168.1.1") and cubre("10.20.60.10") and cubre("10.1.1.1")


def test_portal01_no_sale_a_la_wan_y_f33_abre_de_fw01_al_portal(infra):
    """CI-52: F23 retirado (sin regla de PORTAL01 hacia la WAN); F33 FW01 → PORTAL01 TCP 22 es una regla de salida local de FW01."""
    t = gen(infra)
    assert not any("10.20.40.10" in l and "oifname \"wan\"" in l for l in reglas(t)), "PORTAL01 no debe tener ninguna regla hacia la WAN"
    assert "F23" not in t
    f33 = [l for l in reglas(t) if "F33" in l]
    assert len(f33) == 1 and 'oifname "vlan40"' in f33[0] and "ip daddr 10.20.40.10 tcp dport 22" in f33[0]
