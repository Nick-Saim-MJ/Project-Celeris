"""VPN emulada: los parámetros de swanctl/frr salen de la sección `vpn` del inventario (D1.10)."""
import re

import pytest

from conftest import AWS_PEERS, comparar_snapshot
from gen import vpn


def test_propuestas_ike_y_esp(infra):
    assert vpn.propuestas(infra) == ("aes256gcm16-prfsha384-ecp384", "aes256gcm16-ecp384")


@pytest.mark.parametrize("lado", ["fw01", "vgw"])
def test_swanctl_cumple_d110(infra, lado):
    t = vpn.swanctl(infra, lado, AWS_PEERS)
    assert t.count("version = 2") == 2                                  # IKEv2, dos túneles
    assert t.count("proposals = aes256gcm16-prfsha384-ecp384") == 2     # AES-256-GCM-16, SHA2-384, DH 20
    assert t.count("esp_proposals = aes256gcm16-ecp384") == 2           # PFS grupo 20
    assert t.count("dpd_delay = 10s") == 2 and t.count("dpd_action = restart") == 2
    assert t.count("rekey_time = 28800s") == 2 and t.count("life_time = 3600s") == 2
    assert f"include psk-{lado}.conf" in t
    assert "secret" not in t                                            # la llave nunca va aquí


def test_el_campus_inicia_y_aws_responde(infra):
    assert vpn.swanctl(infra, "fw01", AWS_PEERS).count("start_action = start") == 2
    assert vpn.swanctl(infra, "vgw", AWS_PEERS).count("start_action = none") == 2


def test_frr_asn_temporizadores_y_prepending(infra):
    f = vpn.frr(infra, "fw01")
    assert "router bgp 65020" in f and f.count("remote-as 64512") == 2
    assert f.count("timers 10 30") == 2
    assert "neighbor 169.254.10.1 activate" in f and "neighbor 169.254.11.1 activate" in f
    assert "route-map PREPEND-TUNEL2 out" in f and "PREPEND-TUNEL1" not in f   # solo el túnel 2 es el de respaldo
    assert "set as-path prepend 65020" in f and "network 10.20.0.0/16" in f
    g = vpn.frr(infra, "vgw")
    assert "router bgp 64512" in g and g.count("remote-as 65020") == 2 and "network 10.30.0.0/16" in g
    assert "route-map" not in g


def test_vti_mtu_direcciones_y_extremos(infra):
    t = vpn.vti_up(infra, "fw01", AWS_PEERS)
    assert "ip tunnel add vti1 mode vti local 203.0.113.10 remote 198.51.100.21 key 1" in t
    assert "ip tunnel add vti2 mode vti local 203.0.113.10 remote 198.51.100.22 key 2" in t
    assert "ip addr add 169.254.10.2/30 dev vti1" in t and "ip addr add 169.254.11.2/30 dev vti2" in t
    assert t.count("mtu 1400") == 2 and "disable_policy=1" in t
    g = vpn.vti_up(infra, "vgw", AWS_PEERS)
    assert "ip tunnel add vti1 mode vti local 198.51.100.21 remote 203.0.113.10 key 1" in g
    assert "ip addr add 169.254.10.1/30 dev vti1" in g


def test_marcas_de_strongswan_coinciden_con_la_clave_del_vti(infra):
    t = vpn.swanctl(infra, "fw01", AWS_PEERS)
    assert "mark_in = 1" in t and "mark_out = 1" in t and "mark_in = 2" in t and "mark_out = 2" in t
    assert "install_routes = no" in vpn.strongswan_conf()
    assert "kernel-libipsec { load = no }" in vpn.strongswan_conf()      # si no, el IKE sale por la interfaz ipsec0


def test_un_parametro_nuevo_cambia_la_salida(infra, mutar):
    def cambiar(inv):
        inv["vpn"]["extremo_onpremise"]["asn"] = 65021
        inv["vpn"]["dpd"]["intervalo_s"] = 20
        inv["vpn"]["bgp"]["hold_s"] = 60
    x = mutar(cambiar)
    assert "router bgp 65021" in vpn.frr(x, "fw01") and "timers 10 60" in vpn.frr(x, "fw01")
    assert "dpd_delay = 20s" in vpn.swanctl(x, "fw01", AWS_PEERS)


def test_un_cifrado_sin_equivalente_falla_en_voz_alta(infra, mutar):
    x = mutar(lambda inv: inv["vpn"]["fase1"].__setitem__("cifrado", "AES-128-CBC"))
    with pytest.raises(ValueError, match="no tiene equivalente"):
        vpn.propuestas(x)


def test_numero_de_pares_aws(infra):
    with pytest.raises(ValueError, match="IP públicas de AWS"):
        vpn.swanctl(infra, "fw01", ["198.51.100.21"])


def test_psk_de_laboratorio_fuera_del_repo(infra, tmp_path):
    a = vpn.escribir_psk(tmp_path / "a", infra, AWS_PEERS)
    b = vpn.escribir_psk(tmp_path / "b", infra, AWS_PEERS)
    tx = [p.read_text(encoding="utf-8") for p in a]
    assert all('secret = "' in t for t in tx)

    def sec(t):
        return re.findall(r'secret = "([^"]+)"', t)
    assert sec(tx[0]) == sec(tx[1]) and len(set(sec(tx[0]))) == 2        # misma llave en ambos lados, una por túnel
    assert sec(tx[0]) != sec(b[0].read_text(encoding="utf-8"))           # aleatoria en cada ejecución
    assert all(len(s) >= 32 for s in sec(tx[0]))


def test_ningun_artefacto_versionado_contiene_llaves(infra):
    for lado in ("fw01", "vgw"):
        for t in (vpn.swanctl(infra, lado, AWS_PEERS), vpn.frr(infra, lado), vpn.vti_up(infra, lado, AWS_PEERS)):
            assert not re.search(r"(secret|psk)\s*=", t)


@pytest.mark.parametrize("lado", ["fw01", "vgw"])
def test_snapshots(infra, lado):
    comparar_snapshot(f"swanctl-{lado}.conf", vpn.swanctl(infra, lado, AWS_PEERS))
    comparar_snapshot(f"frr-{lado}.conf", vpn.frr(infra, lado))
    comparar_snapshot(f"vti-{lado}.sh", vpn.vti_up(infra, lado, AWS_PEERS))
