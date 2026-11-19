"""Generadores del laboratorio emulado (Modo L) a partir de la fuente única infra/*.yaml.

Ninguna cifra, IP, puerto ni nombre sale de estos módulos: todo se lee del inventario. Lo que el inventario
no define (IP públicas de la WAN del laboratorio, direcciones de host de los /30) llega por parámetro y se
registra en docs/infra/e1/CAMBIOS-INVENTARIO.md.

    nftables.py   ruleset de fw01-sim (política drop, una regla por flujo F-nn)
    vpn.py        swanctl.conf, frr.conf y script de interfaces de túnel para fw01-sim y vgw-sim
    pac.py        wpad.dat con EDGE01, EDGE02 y DIRECT (REQ-F-26)

Todo lo generado es EMULADO: fw01-sim no es OPNsense ni vgw-sim es el VGW de AWS (Parte F4.2).
"""
