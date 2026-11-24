"""Gancho V-90+ — Centro de datos híbrido (CE0331): infra/centro_datos.yaml contra infra/inventory.yaml.

    V-90  centro_datos.yaml cumple su esquema; toda referencia (componente, S-xx, CI-nn, zona) existe y ningún ID retirado reaparece.
    V-91  Las VM del YAML son 1 a 1 las del inventario y con los mismos vCPU, RAM, disco, SO, fase y port group; ninguna pasa de 8 vCPU.
    V-92  Sumas de vCPU, RAM y disco = tablas de D2.4; dimensionamiento (núcleos 2:1 y 4:1, RAM × 1,1 × 1,2, disco × 1,3 + copia
          local) recalculado; holgura ≥ 15 % en CPU, RAM y disco; la caché cabe en su NVMe.
    V-93  Hipervisor y rack: NIC ↔ vSwitch ↔ port group ↔ VLAN de la zona; teaming; seguridad de los port groups; rack de 12U y energía.
    V-94  AWS y continuidad: CIDR dentro de la VPC, tipos de instancia citados por el inventario, costo mensual ≤ US$ 75 y lab < US$ 0,10/h;
          cada servicio con RTO y RPO coherentes con su criticidad; 3-2-1-1-0 sin contradecir a S3.
"""
import re
import sys
from pathlib import Path

GRUPO = "E2"
PRIMER_ID = "V-90"
DESCRIPCION = "Centro de datos híbrido: centro_datos.yaml contra el inventario (VM, dimensionamiento, hipervisor, AWS, continuidad)"

_INFRA = Path(__file__).resolve().parents[1]
for _p in (str(_INFRA), str(_INFRA / "gen")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

RETIRADOS_SERVICIO = re.compile(r"\b(DB01|OBS01|SVC01|WAF01|WEB01|IDS01|PROBE01|NAS01|EC2-SHIELD|EC2-CTRLR|NAT01)\b")


def _texto_yaml(infra) -> str:
    import centro_datos as cdm
    return cdm.RUTA.read_text(encoding="utf-8")


def _cis_registrados(infra) -> set[str]:
    md = (infra.raiz / "docs" / "infra" / "e1" / "CAMBIOS-INVENTARIO.md").read_text(encoding="utf-8")
    return set(re.findall(r"^### (CI-\d+)", md, re.M))


def run(infra):
    from validate import E, Resultado, W, I, estado_de
    import centro_datos as cdm

    res = []

    def resultado(cid, titulo, hs, detalle=""):
        res.append(Resultado(cid, titulo, estado_de(hs), hs, detalle))

    # ------------------------------------------------------------------ V-90
    h = []
    errores = cdm.CentroDatos.errores_esquema()
    for e in errores:
        h.append(E(f"centro_datos.yaml no cumple el esquema: {e}", "Corrija infra/centro_datos.yaml (esquema en infra/schema/centro_datos.schema.json)"))
    if errores:
        resultado("V-90", "centro_datos.yaml: esquema, referencias e IDs", h)
        return res + [Resultado(f"V-9{i}", "Omitido: V-90 falló", "FALLA", [E("No se evalúa con un YAML inválido")]) for i in range(1, 5)]
    cd = cdm.CentroDatos.cargar(infra)
    txt = _texto_yaml(infra)
    ids_s = set(re.findall(r"\[(S-\d+)\]", txt)) | {s for lst in re.findall(r"supuestos?: \[([^\]]+)\]", txt) for s in re.findall(r"S-\d+", lst)} \
        | set(re.findall(r"supuesto: (S-\d+)", txt))
    for s in sorted(ids_s):
        if s not in infra.supuestos:
            h.append(E(f"{s} no existe en trazabilidad.yaml", "Use un supuesto vigente S-01…S-32"))
        elif infra.supuestos[s].get("estado") == "retirado":
            h.append(E(f"{s} está retirado", "Un ID retirado no se reutiliza"))
    registrados = _cis_registrados(infra)
    for ci in sorted(set(re.findall(r"CI-\d+", txt))):
        if ci not in registrados:
            h.append(E(f"{ci} se cita en centro_datos.yaml pero no está en CAMBIOS-INVENTARIO.md", "Registre el CI en docs/infra/e1/CAMBIOS-INVENTARIO.md"))
    for m in RETIRADOS_SERVICIO.finditer(txt):
        linea = txt[:m.start()].count("\n") + 1
        contexto = txt.splitlines()[linea - 1]
        if not re.search(r"(?i)retirad|no hay|sin |ninguna", contexto):
            h.append(E(f"línea {linea}: {m.group(1)} está retirado en v0.4 y no puede citarse como vigente", "Quite el ID o dilo explícitamente («retirado»)"))
    for v in cd.vms:
        if v["componente"] not in infra.componentes:
            h.append(E(f"VM {v['componente']} no es un componente vigente del inventario", "Use un ID de infra/inventory.yaml"))
    for sv in cd.servicios.values():
        for c in sv["componentes"]:
            if c not in infra.componentes:
                h.append(E(f"{sv['id']}: componente {c} inexistente", "Use un ID vigente del inventario"))
    for pg in cd.port_groups.values():
        if pg["zona"] and pg["zona"] not in infra.zonas:
            h.append(E(f"{pg['id']}: zona {pg['zona']} inexistente", "Use una zona vigente"))
    ex = cd.extras()
    for i in ex:
        if i in infra.componentes:
            h.append(E(f"{i} figura como elemento nuevo y como componente del inventario", "Un ID, un solo origen"))
    resultado("V-90", "centro_datos.yaml: esquema, referencias (componentes, zonas, S-xx, CI-nn) e IDs retirados", h,
              f"{len(cd.vms)} VM · {len(cd.port_groups)} port groups · {len(ex)} elementos propios · {len(cd.servicios)} servicios")

    # ------------------------------------------------------------------ V-91
    h = []
    con_vm = {c for c, comp in infra.componentes.items() if comp.get("vm")}
    en_yaml = set(cd.vm_por_id)
    for c in sorted(con_vm - en_yaml):
        h.append(E(f"{c} tiene `vm` en el inventario y no está en centro_datos.yaml", "Agréguelo a maquinas_virtuales"))
    for c in sorted(en_yaml - con_vm):
        h.append(E(f"{c} está en centro_datos.yaml y el inventario no lo define como VM", "Quítelo o corrija el inventario por CI-nn"))
    for c in sorted(en_yaml & con_vm):
        v, iv = cd.vm_por_id[c], infra.componentes[c]["vm"]
        if v["fase"] != iv["fase"]:
            h.append(E(f"{c}: fase {v['fase']} ≠ inventario {iv['fase']}", "Manda el inventario"))
        for k in ("vcpu", "ram_gb"):
            if v[k] != iv[k]:
                h.append(E(f"{c}: {k} {v[k]} ≠ inventario {iv[k]}", "Manda el inventario"))
        if v["so"] != iv["so"]:
            h.append(E(f"{c}: SO {v['so']} ≠ inventario {iv['so']}", "Manda el inventario"))
        disco_inv = iv["disco_gb"]
        m = re.fullmatch(r"(\d+)(?: \+ (\d+) caché)?", str(disco_inv))
        d_inv, c_inv = (int(m.group(1)), int(m.group(2) or 0)) if m else (None, None)
        if (v["disco_gb"], v["cache_gb"]) != (d_inv, c_inv):
            h.append(E(f"{c}: disco {cd.vm_texto_disco(v)} ≠ inventario «{disco_inv}»", "Manda el inventario"))
        norm_inv = sorted(cdm.plano(p) for p in re.split(r"\s*\+\s*", re.sub(r"^PG-", "", iv["port_group"])) if p)
        norm_yaml = sorted(cdm.plano(p) for p in v["port_groups"])
        if norm_inv != norm_yaml:
            h.append(E(f"{c}: port group {v['port_groups']} ≠ inventario «{iv['port_group']}»", "Manda el inventario"))
        for pg in v["port_groups"]:
            if pg not in cd.port_groups:
                h.append(E(f"{c}: el port group {pg} no existe en hipervisor_red", "Defínalo en un vSwitch"))
        if v["datastore"] not in cd.datastores:
            h.append(E(f"{c}: datastore {v['datastore']} inexistente", "Use DS-VM"))
        if v["cache_gb"] and v.get("datastore_cache") not in cd.datastores:
            h.append(E(f"{c}: lleva caché y no indica un datastore de caché válido", "Agregue datastore_cache"))
        if v["vcpu"] > cd.host["hipervisor"]["vcpu_max_por_vm"]:
            h.append(E(f"{c}: {v['vcpu']} vCPU supera el máximo de ESXi gratuito ({cd.host['hipervisor']['vcpu_max_por_vm']})", "Reduzca los vCPU de la VM"))
        if v["vcpu"] > 8:
            h.append(E(f"{c}: más de 8 vCPU", "ESXi gratuito: máximo 8 vCPU por VM"))
    por_zona = {}
    for v in cd.vms:
        comp = infra.componentes.get(v["componente"], {})
        pgs = [p for p in v["port_groups"] if p not in ("PG-TRANSITO", "PG-FW-TRUNK")]
        for p in pgs:
            z = cd.port_groups[p]["zona"]
            if z and z not in comp.get("zonas", []):
                h.append(E(f"{v['componente']}: el port group {p} es de la zona {z} y el componente no está en esa zona", "Revise el port group"))
            por_zona.setdefault(z, []).append(v["componente"])
    resultado("V-91", "VM: 1 a 1 con el inventario, mismos recursos, port group y zona; ninguna > 8 vCPU", h,
              f"{len(en_yaml)} VM en el YAML · {len(con_vm)} en el inventario · máx. {max(v['vcpu'] for v in cd.vms)} vCPU")

    # ------------------------------------------------------------------ V-92
    h = []
    for fase, esp in cd.raw["totales_d24"].items():
        t = cd.totales(fase)
        for k in ("vcpu", "ram_gb", "disco_gb"):
            if t[k] != esp[k]:
                h.append(E(f"Total {fase} de {k}: {t[k]} calculado ≠ {esp[k]} de D2.4", "Corrija las VM o la tabla de referencia por CI-nn"))
    d = cd.dimensionar()
    min_h = cd.raw["dimensionamiento"]["holgura_minima"]
    if d["nucleos_necesarios"] > d["nucleos_host"]:
        h.append(E(f"Núcleos necesarios {d['nucleos_necesarios']:.2f} > {d['nucleos_host']} del host", "Reduzca la sobreasignación o aumente el host"))
    for nombre, clave in (("CPU", "holgura_cpu"), ("RAM", "holgura_ram"), ("disco", "holgura_disco")):
        if d[clave] < min_h:
            h.append(E(f"Holgura de {nombre} {d[clave]:.1%} < {min_h:.0%} (D2.3)", "Aumente la capacidad del host o reduzca las VM"))
    if d["ram_con_crecimiento"] > d["ram_host"]:
        h.append(E(f"RAM con crecimiento {d['ram_con_crecimiento']:.1f} GB > {d['ram_host']} GB del host", "Aumente la RAM del host"))
    if d["margen_ram_tras_crecimiento"] < min_h:
        h.append(W(f"Margen de RAM tras reservar el 20 % de crecimiento: {d['margen_ram_tras_crecimiento']:.1%} < {min_h:.0%} "
                   f"({d['ram_libre_tras_crecimiento']:.1f} GB libres de {d['ram_host']} GB). Abierto en CI-78", "Decisión del equipo: RAM de 128 GB o aceptar el margen"))
    if d["disco_con_copia"] > d["disco_capacidad"]:
        h.append(E("El disco requerido excede el datastore", "Aumente el datastore"))
    for k, c in d["cache"].items():
        if c["usado"] > c["cap"]:
            h.append(E(f"{k}: la caché ({c['usado']} GB) no cabe en {c['cap']} GB", "Reduzca la caché"))
    resultado("V-92", "Dimensionamiento: sumas = tablas D2.4; núcleos, RAM y disco recalculados; holgura ≥ 15 % y la caché cabe", h,
              f"F2: {d['vcpu']} vCPU → {d['nucleos_necesarios']:.2f} núcleos de {d['nucleos_host']} (holgura {d['holgura_cpu']:.1%}) · "
              f"RAM {d['ram_con_crecimiento']:.1f} de {d['ram_host']} GB (holgura {d['holgura_ram']:.1%}; tras crecimiento {d['margen_ram_tras_crecimiento']:.1%}) · "
              f"disco {d['disco_con_copia']:.0f} de {d['disco_capacidad']} GB (holgura {d['holgura_disco']:.1%})")

    # ------------------------------------------------------------------ V-93
    h = []
    host = cd.host
    esx = infra.componentes.get(host["componente"])
    if not esx:
        h.append(E("host.componente no está en el inventario", "Use ESX01"))
    else:
        ip_vmk0 = next((i["ip"] for i in esx["ips"] if i["interfaz"] == "vmk0"), None)
        v0 = next((v for v in host["vmk"] if v["id"] == "vmk0"), None)
        if not v0 or v0["ip"] != ip_vmk0:
            h.append(E(f"vmk0 {v0 and v0['ip']} ≠ inventario {ip_vmk0}", "Manda el inventario"))
        if v0 and v0["port_group"] not in cd.port_groups:
            h.append(E("vmk0 apunta a un port group inexistente", "Corrija vmk"))
        for token in ("vmnic0", "vmnic1", "vmnic2", "PG-MGMT", "PG-FW-TRUNK", "PG-TRANSITO", "vSwitch0", "vSwitch1"):
            if token not in esx["aporta"] and token not in esx["por_que"]:
                h.append(W(f"{token} no aparece en ESX01.aporta del inventario", "Revise la coherencia con el inventario"))
    usadas = {}
    for s in cd.vswitches.values():
        for u in s["uplinks"]:
            if u not in cd.nics:
                h.append(E(f"{s['id']}: uplink {u} no es una NIC del host", "Defínalo en host.nic"))
            elif cd.nics[u]["vswitch"] != s["id"]:
                h.append(E(f"{u}: el host dice vSwitch {cd.nics[u]['vswitch']} y {s['id']} la usa", "Una NIC, un vSwitch"))
            usadas[u] = usadas.get(u, 0) + 1
    for u, n in usadas.items():
        if n > 1:
            h.append(E(f"{u} está en más de un vSwitch", "Una NIC, un vSwitch"))
    if len(cd.nics) != 4:
        h.append(E("ESX01 debe tener 4 NIC (D2.4)", "Corrija host.nic"))
    if sorted(cd.vswitches["vSwitch0"]["uplinks"]) != ["vmnic0", "vmnic1"] or not cd.vswitches["vSwitch0"]["teaming"]:
        h.append(E("vSwitch0 debe llevar vmnic0 + vmnic1 con teaming (D2.4)", "Corrija vSwitch0"))
    if cd.vswitches["vSwitch1"]["uplinks"] != ["vmnic2"]:
        h.append(E("vSwitch1 debe usar solo vmnic2 (D2.4)", "Corrija vSwitch1"))
    if cd.vswitches["vSwitch1"]["port_groups"][0].get("solo") != ["FW01"]:
        h.append(E("PG-TRANSITO es solo de FW01", "Corrija vSwitch1"))
    for n in cd.nics.values():
        if n["destino"] and n["destino"] not in infra.componentes:
            h.append(E(f"{n['id']}: destino {n['destino']} inexistente", "Use un ID del inventario"))
    for s in cd.vswitches.values():
        for pg in s["port_groups"]:
            z = infra.zonas.get(pg["zona"]) if pg["zona"] else None
            if z is not None and z.get("vlan") != pg["vlan"]:
                h.append(E(f"{pg['id']}: VLAN {pg['vlan']} ≠ VLAN {z.get('vlan')} de la zona {pg['zona']}", "Manda el inventario"))
            if z is None and pg["zona"] is None and pg["vlan"] != 4095:
                h.append(E(f"{pg['id']}: un port group sin zona debe ser el trunk VLAN 4095", "Corrija el port group"))
            if not [v for v in cd.vms if pg["id"] in v["port_groups"]]:
                h.append(E(f"{pg['id']} no tiene ninguna VM", "Quite el port group o conecte una VM (v0.4: sin port groups de captura)"))
    vlans_inv = {z["vlan"] for z in infra.zonas.values() if z.get("vlan") not in (None, 999)}
    vlans_pg = {pg["vlan"] for pg in cd.port_groups.values() if pg["vlan"] not in (None, 4095)}
    if vlans_inv != vlans_pg:
        h.append(E(f"VLAN del inventario {sorted(vlans_inv)} ≠ VLAN de los port groups {sorted(vlans_pg)}", "Un port group por VLAN vigente"))
    sec = cd.raw["hipervisor_red"]["seguridad_por_defecto"]
    if set(sec.values()) != {"rechazar"}:
        h.append(E("Modo promiscuo, cambios de MAC y transmisiones falsificadas deben estar en «rechazar» (v0.4: sin excepciones)", "Corrija seguridad_por_defecto"))
    # rack
    ocup = cd.raw["rack"]["ocupacion"]
    usadas_u = set()
    for o in ocup:
        for u in range(o["u"][0], o["u"][1] + 1):
            if u in usadas_u:
                h.append(E(f"U{u} del rack está ocupada dos veces", "Corrija rack.ocupacion"))
            usadas_u.add(u)
    libres = sorted(set(range(1, cd.raw["rack"]["unidades"] + 1)) - usadas_u)
    esperadas = [u for r in cd.raw["rack"]["libres_derivado"] for u in range(r[0], r[1] + 1)]
    if libres != esperadas:
        h.append(E(f"U libres {libres} ≠ libres_derivado {esperadas}", "Corrija rack"))
    e = cd.raw["energia"]
    if e["ups"] not in infra.componentes:
        h.append(E("energia.ups inexistente", "Use UPS01"))
    elif not re.search(rf"≈ {e['consumo_w']} W", infra.componentes[e["ups"]]["por_que"]):
        h.append(E(f"El consumo {e['consumo_w']} W no coincide con UPS01.por_que del inventario", "Manda el inventario (CI-77)"))
    if e["nut"]["servidor"] != "JMP01" or e["nut"]["tarjeta_ups"] != next(i["ip"] for i in infra.componentes["UPS01"]["ips"]):
        h.append(E("NUT: JMP01 y la IP de la tarjeta de UPS01 deben coincidir con el inventario", "Corrija energia.nut"))
    arranque = [c for g in cd.raw["orden_arranque"] for c in g if c != "resto"]
    if arranque != ["FW01", "CTRL01", "EDGE01", "EDGE02", "SIEM01"]:
        h.append(E("Orden de arranque distinto de FW01 → CTRL01 → EDGE01/02 → SIEM01 → resto (D2.4)", "Corrija orden_arranque"))
    resultado("V-93", "Hipervisor: NIC → vSwitch → port group → VLAN de la zona; teaming; seguridad; rack de 12U y energía", h,
              f"{len(cd.vswitches)} vSwitch · {len(cd.port_groups)} port groups · {len(cd.nics)} NIC · rack: U libres {libres} · UPS {e['consumo_w']} W")

    # ------------------------------------------------------------------ V-94
    h = []
    aws_inv = infra.inv["aws"]
    inv_comp = infra.componentes
    if aws_inv["region"]["laboratorio"] != cd.aws["region"]["laboratorio"]:
        h.append(E("Región de laboratorio distinta del inventario", "Manda el inventario"))
    if aws_inv["region"]["produccion_candidata"] != cd.aws["region"]["produccion_candidata"]:
        h.append(E("Región de producción distinta del inventario", "Manda el inventario (CI-81)"))
    import ipaddress
    vpc = ipaddress.ip_network(inv_comp["AWS-VPC"]["cidr"])
    subs = [ipaddress.ip_network(inv_comp[s]["cidr"]) for s in ("AWS-PUB-A", "AWS-APP-A")]
    for s in subs:
        if not s.subnet_of(vpc):
            h.append(E(f"{s} no está dentro de la VPC {vpc}", "Corrija el CIDR"))
    if subs[0].overlaps(subs[1]):
        h.append(E("pub-a y app-a se solapan", "Corrija los CIDR"))
    reserva = next(r for r in infra.inv["reservas"] if r["id"] == "RES-AWS-CRECIMIENTO")
    if any(ipaddress.ip_network(reserva["cidr"]).overlaps(s) for s in subs):
        h.append(E("Una subred se solapa con la reserva de crecimiento", "Corrija los CIDR"))
    for i in cd.aws["instancias"]:
        c = inv_comp.get(i["componente"])
        if not c:
            h.append(E(f"{i['componente']} no está en el inventario", "Use un ID vigente"))
            continue
        if i["tipo"] not in c["aporta"] and i["tipo"] not in c["funcion"]:
            h.append(E(f"{i['componente']}: el tipo {i['tipo']} no aparece en su `aporta` del inventario", "Manda el inventario (D2.5)"))
        if bool(i.get("temporal")) != (c["estado"] == "temporal"):
            h.append(E(f"{i['componente']}: «temporal» no coincide con el estado del inventario", "Manda el inventario"))
    if aws_inv["simulacro_recuperacion"]["instancias"] != ["EC2-DR", "NAT-DR"]:
        h.append(E("El simulacro del inventario no usa EC2-DR y NAT-DR", "Manda el inventario"))
    rt = {t["id"]: t for t in aws_inv["tablas_de_rutas"]}
    nat_rutas = [r for r in rt["rt-private"]["rutas"] if str(r["salto"]).startswith("nat:")]
    if cd.aws["nat"]["permanente"] or not all(r.get("solo_en_simulacro") for r in nat_rutas):
        h.append(E("Ninguna ruta por NAT puede ser permanente", "La ruta por NAT-DR existe solo en el simulacro (D2.5)"))
    # integración híbrida idéntica a CE0311: las rutas de la VPC hacia el campus son las redes que anuncia la VPN
    vpn = infra.inv["vpn"]
    dest = {infra.inv["supernets"][[s["id"] for s in infra.inv["supernets"]].index(r["destino"].split(":", 1)[1])]["cidr"]
            for t in aws_inv["tablas_de_rutas"] for r in t["rutas"] if r["salto"] == "vgw"}
    if dest != set(vpn["extremo_onpremise"]["redes_anunciadas"]):
        h.append(E(f"Las rutas hacia el VGW {sorted(dest)} ≠ redes anunciadas por el campus {vpn['extremo_onpremise']['redes_anunciadas']}", "Misma VPN que CE0311"))
    if vpn["extremo_aws"]["redes_anunciadas"] != [inv_comp["AWS-VPC"]["cidr"]]:
        h.append(E("La red que anuncia el VGW no es el CIDR de la VPC", "Misma VPN que CE0311"))
    s3 = aws_inv["s3"]
    inm = cd.continuidad["regla_3_2_1_1_0"]["inmutable"]
    if (inm["dias"], inm["mecanismo"].split()[-1]) != (s3["object_lock"]["dias"], s3["object_lock"]["modo"]):
        h.append(E("Object Lock de la regla 3-2-1-1-0 distinto del de S3 en el inventario", "Manda el inventario"))
    c = cd.costo()
    if c["total"] > c["meta"]:
        h.append(E(f"Costo mensual {c['total']:.2f} > meta US$ {c['meta']}", "Reduzca el diseño AWS"))
    if abs(c["total"] - c["referencial"]) > 1.0:
        h.append(E(f"El costo recalculado {c['total']:.2f} no es ≈ {c['referencial']} de D2.5", "Corrija las líneas de costo"))
    if c["lab_hora"] >= c["lab_meta"]:
        h.append(E(f"Laboratorio efímero {c['lab_hora']:.4f} US$/h ≥ {c['lab_meta']}", "Reduzca el laboratorio"))
    eg = cd.ec2_gw()
    if eg["margen_cpu"] < 0 or eg["margen_ram"] < 0:
        h.append(E("EC2-GW no soporta su carga de diseño", "Suba el tipo de instancia"))
    if eg["margen_cpu"] < cd.raw["dimensionamiento"]["holgura_minima"] or eg["margen_ram"] < cd.raw["dimensionamiento"]["holgura_minima"]:
        h.append(W("Margen de EC2-GW < 15 %", "Revise la carga de diseño (CI-82)"))
    h.append(W("La carga de diseño de EC2-GW son valores propuestos y sin medir (CI-82 abierto)", "Medir en S2 con el piloto"))
    # continuidad
    lim = cd.continuidad["limites_por_criticidad"]
    for s in cd.servicios.values():
        crit = cd.criticidad_servicio(s)
        if s["rto_min"] is None or "rpo_texto" not in s or not s["rto_texto"] or not s["rpo_texto"]:
            h.append(E(f"{s['id']} {s['servicio']}: falta RTO o RPO", "Todo servicio lleva RTO y RPO (o «No aplica» con motivo)"))
        if crit in lim:
            if s["rto_min"] > lim[crit]["rto_max_min"]:
                h.append(E(f"{s['id']}: RTO {s['rto_min']} min excede el máximo de la clase {crit} ({lim[crit]['rto_max_min']} min)", "Mejore la recuperación o reclasifique"))
            if s["rpo_min"] is not None and s["rpo_min"] > lim[crit]["rpo_max_min"]:
                h.append(E(f"{s['id']}: RPO {s['rpo_min']} min excede el máximo de la clase {crit}", "Mejore el respaldo o reclasifique"))
        if s["rpo_min"] is None and not s["rpo_texto"]:
            h.append(E(f"{s['id']}: RPO sin valor ni texto", "Escriba el RPO"))
        if s["prueba"] if "prueba" in s and s["prueba"] else False:
            if s["prueba"] not in infra.pruebas:
                h.append(E(f"{s['id']}: la prueba {s['prueba']} no existe", "Use una T-xx vigente"))
    consola = cd.servicios["CT-03"]
    if consola["rto_min"] > 120 or consola["rpo_min"] != 15:
        h.append(E("La consola debe tener RTO ≤ 2 h (D2.3) y RPO 15 min (D2.9)", "Corrija CT-03"))
    d_crit = {s["id"]: cd.criticidad_servicio(s) for s in cd.servicios.values()}
    regla = cd.continuidad["regla_3_2_1_1_0"]
    if len(regla["copias"]) != 3 or len(regla["medios"]) != 2 or sum(c["fuera_del_sitio"] for c in regla["copias"]) != 1 \
            or sum(c["inmutable"] for c in regla["copias"]) != 1:
        h.append(E("La regla 3-2-1-1-0 exige 3 copias, 2 medios, 1 fuera del sitio y 1 inmutable", "Corrija regla_3_2_1_1_0"))
    h.append(I(f"Criticidad derivada de los servicios: {d_crit}"))
    resultado("V-94", "AWS y continuidad: CIDR, instancias, NAT temporal, costo ≤ US$ 75, RTO/RPO coherentes con la criticidad y 3-2-1-1-0", h,
              f"costo {c['total']:.2f} US$/mes · lab {c['lab_hora']:.4f} US$/h · {len(cd.servicios)} servicios con RTO y RPO")
    return res
