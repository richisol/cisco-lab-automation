"""
ssh_setup.py

Konfigurerer SSH-tilgang på en Cisco switch ELLER router via konsollkabel
(seriell tilkobling) - samme script fungerer på begge, siden IOS-kommandoene
for SSH-oppsett er identiske. Alle verdier (COM-port, hostname, brukernavn,
passord osv.) hentes fra brukeren ved kjøring - ingenting er hardkodet.

Støtter også multilayer-switch: valgfri 'ip routing', flere interfaces med
IP-adresse, og routede porter (no switchport).
"""

import serial
import time
import getpass
import subprocess


def send_command(ser, command, wait=1.5):
    """Sender en kommando til enheten og returnerer/skriver ut svaret."""
    ser.write((command + "\r\n").encode())
    time.sleep(wait)
    response = ser.read(ser.in_waiting or 1000).decode(errors="ignore")
    print(response)
    return response


def main():
    # --- Hent inn variabler fra brukeren (ingenting hardkodet) ---
    port = input("COM-port (f.eks COM1): ").strip()
    baudrate = input("Baudrate [9600]: ").strip() or "9600"

    hostname = input("Ønsket hostname (switch eller router): ").strip()
    domain_name = input("Domenenavn (f.eks lab.local): ").strip()

    username = input("SSH-brukernavn: ").strip()
    password = getpass.getpass("SSH-passord: ")

    # Kreves for å kunne bruke "enable" over SSH/vty - uten denne nekter IOS
    # deg inn i privilegert modus på en remote-sesjon (fungerer fint uten på
    # konsollet, men det holder ikke over nettverket).
    enable_secret = getpass.getpass("Enable-passord (for 'enable' over SSH): ")

    key_modulus = input("RSA-nøkkelstørrelse [2048]: ").strip() or "2048"

    # Valgfritt: multilayer-switch som skal rute mellom subnett
    enable_routing = input(
        "\nEr dette en multilayer-switch som skal rute ('ip routing')? [j/n]: "
    ).strip().lower() == "j"

    # Valgfri IP-adressering. Du kan legge inn flere interfaces etter hverandre,
    # siden multilayer-switch og routere ofte trenger flere IP-adresser.
    interfaces = []
    while input(
        "\nVil du sette IP-adresse på et interface? [j/n]: "
    ).strip().lower() == "j":
        name = input(
            "Interface (f.eks 'vlan 1', 'gi1/0/1' på switch, 'gi0/0/0' på router): "
        ).strip()
        ip = input("IP-adresse: ").strip()
        mask = input("Subnettmaske (f.eks 255.255.255.0): ").strip()
        routed = input(
            "Er dette en fysisk port på en multilayer-switch som skal være "
            "routet port (no switchport)? [j/n]: "
        ).strip().lower() == "j"
        interfaces.append((name, ip, mask, routed))

    # Valgfri default gateway. Uten den svarer ikke enheten på trafikk fra andre
    # subnett (for eksempel SSH fra management-PC-en).
    gateway = input(
        "\nDefault gateway / neste hopp (Enter hvis ingen): "
    ).strip()
    is_layer2 = False
    if gateway and not enable_routing:
        is_layer2 = input(
            "Er dette en vanlig layer 2-switch (ikke router eller multilayer)? [j/n]: "
        ).strip().lower() == "j"

    # --- Åpne serieforbindelsen ---
    ser = serial.Serial(
        port=port,
        baudrate=int(baudrate),
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=1,
    )

    print(f"\nKoblet til {port} @ {baudrate} baud. Starter konfigurasjon...\n")

    # Svar "no" i tilfelle enheten står i "initial configuration dialog"
    # (skjer typisk rett etter erase startup-config + reload, når det ikke
    # finnes noen lagret konfig). Harmløst å sende selv om dialogen ikke vises.
    send_command(ser, "no")

    # Vekk opp linja og gå inn i privilegert / konfigurasjonsmodus
    send_command(ser, "")
    send_command(ser, "enable")
    send_command(ser, "configure terminal")

    # Grunnleggende identitet - kreves før RSA-nøkkel kan genereres
    send_command(ser, f"hostname {hostname}")
    # Nyere IOS-XE (17.x) bruker 'ip domain name', eldre IOS 'ip domain-name'.
    # Prøv den nye først, og falle tilbake til den gamle hvis den blir avvist.
    out = send_command(ser, f"ip domain name {domain_name}")
    if "%" in out:
        send_command(ser, f"ip domain-name {domain_name}")

    # Generer RSA-nøkkelpar (dette er det som faktisk aktiverer SSH på IOS)
    send_command(ser, f"crypto key generate rsa modulus {key_modulus}", wait=5)

    # Lokal bruker, enable-passord, og selve SSH-aktiveringen på vty-linjene
    send_command(ser, f"username {username} secret {password}")
    send_command(ser, f"enable secret {enable_secret}")
    send_command(ser, "line vty 0 4")
    send_command(ser, "login local")
    send_command(ser, "transport input ssh")
    send_command(ser, "exit")

    # Multilayer-switch: slå på ruting før interfacene settes opp
    if enable_routing:
        send_command(ser, "ip routing")

    # IP-adressering, ett interface om gangen
    for name, ip, mask, routed in interfaces:
        send_command(ser, f"interface {name}")
        if routed:
            # Fysiske porter på en multilayer-switch er switch-porter som
            # standard og godtar ikke 'ip address' før de gjøres om til routet port.
            send_command(ser, "no switchport")
        send_command(ser, f"ip address {ip} {mask}")
        send_command(ser, "no shutdown")
        send_command(ser, "exit")

        # Fjern evt. gammel SSH-nøkkel for denne IP-en lokalt på PC-en.
        # Trygt her spesifikt: vi VET nøkkelen er utdatert, siden vi nettopp
        # (re)genererte en ny på enheten. Host key checking er fortsatt aktivt
        # for alle fremtidige tilkoblinger - vi fjerner bare denne ene kjente
        # utdaterte oppføringen, ikke sikkerhetssjekken generelt.
        try:
            subprocess.run(
                ["ssh-keygen", "-R", ip],
                check=True, capture_output=True, text=True,
            )
            print(f"Fjernet evt. gammel SSH-nøkkel for {ip} fra known_hosts.")
        except Exception as e:
            print(f"Kunne ikke automatisk rydde known_hosts for {ip}: {e}")

    # Default gateway: layer 2-switch bruker 'ip default-gateway', mens router
    # og multilayer-switch (med ip routing) bruker en default route.
    if gateway:
        if is_layer2:
            send_command(ser, f"ip default-gateway {gateway}")
        else:
            send_command(ser, f"ip route 0.0.0.0 0.0.0.0 {gateway}")

    send_command(ser, "end")

    # Valgfritt: lagre konfigurasjonen til flash
    save = input("\nLagre konfigurasjonen (write memory)? [j/n]: ").strip().lower()
    if save == "j":
        send_command(ser, "write memory", wait=3)

    ser.close()
    print("\nFerdig. Sjekk output over for å bekrefte at hvert steg gikk gjennom uten feil.")


if __name__ == "__main__":
    main()
