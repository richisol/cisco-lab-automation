"""
ssh_setup.py

Konfigurerer SSH-tilgang på en Cisco switch ELLER router via konsollkabel
(seriell tilkobling) - samme script fungerer på begge, siden IOS-kommandoene
for SSH-oppsett er identiske. Alle verdier (COM-port, hostname, brukernavn,
passord osv.) hentes fra brukeren ved kjøring - ingenting er hardkodet.
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

    key_modulus = input("RSA-nøkkelstørrelse [1024]: ").strip() or "1024"

    # Valgfri IP-adressering - samme felt funker for switch (interface vlan 1)
    # og router (f.eks interface GigabitEthernet0/0), siden det bare er et
    # interface-navn som skrives inn.
    configure_ip = input(
        "Vil du også sette IP-adresse på et interface? [j/n]: "
    ).strip().lower() == "j"

    if configure_ip:
        interface_name = input(
            "Interface (f.eks 'vlan 1' for switch, 'GigabitEthernet0/0' for router): "
        ).strip()
        ip_address = input("IP-adresse: ").strip()
        subnet_mask = input("Subnettmaske (f.eks 255.255.255.0): ").strip()

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

    # IP-adressering, hvis brukeren ba om det
    if configure_ip:
        send_command(ser, f"interface {interface_name}")
        send_command(ser, f"ip address {ip_address} {subnet_mask}")
        send_command(ser, "no shutdown")
        send_command(ser, "exit")

        # Fjern evt. gammel SSH-nøkkel for denne IP-en lokalt på PC-en.
        # Trygt her spesifikt: vi VET nøkkelen er utdatert, siden vi nettopp
        # (re)genererte en ny på enheten. Host key checking er fortsatt aktivt
        # for alle fremtidige tilkoblinger - vi fjerner bare denne ene kjente
        # utdaterte oppføringen, ikke sikkerhetssjekken generelt.
        try:
            subprocess.run(
                ["ssh-keygen", "-R", ip_address],
                check=True, capture_output=True, text=True,
            )
            print(f"Fjernet evt. gammel SSH-nøkkel for {ip_address} fra known_hosts.")
        except Exception as e:
            print(f"Kunne ikke automatisk rydde known_hosts for {ip_address}: {e}")

    send_command(ser, "end")

    # Valgfritt: lagre konfigurasjonen til flash
    save = input("\nLagre konfigurasjonen (write memory)? [j/n]: ").strip().lower()
    if save == "j":
        send_command(ser, "write memory", wait=3)

    ser.close()
    print("\nFerdig. Sjekk output over for å bekrefte at hvert steg gikk gjennom uten feil.")


if __name__ == "__main__":
    main()
