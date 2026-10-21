# SSH-oppsett via konsollkabel

Scriptet automatiserar manuell oppsett gjennom terminal.  
Eininga blir kopla til over den serielle konsollkabelen og sender IOS-kommandoane som setter opp SSH-tilgang, i staden for å taste inn manuelt.

# Krav
Python 3, og biblioteket pyserial. Dette er det som faktisk lar Python snakke med ein seriellport. Uten pyserial får ikkje Python kontakt med seriellportane.

# Fysisk tilkopling
Det blir brukt ein kabel med RJ45 i eine enden(koplast til konsollporten på switch/router).  
Her er det varierande frå kva kabel du brukar. Du kan bruke DB9-seriellport på PC, eller ein USB til seriell adapter.  
I seg sjølv er dette ikkje ein nettverkstilkopling.
## Instillingar
9600 baud, 8 databit, ingen paritet, 1 stoppbit, 8N1

# Finne riktig port
## Windows
For å finne riktig port må du inn på enhetsbehandling.  
Enhetsbehandling -> Porter(COM og LPT) finn port med riktig tall, det er tallet eller namnet du oppgir i scriptet.
## Linux
På Linux heiter ein innebygd seriellport /dev/ttyS<tall>. Om det er ein USB-adapter, står det /dev/ttyUSB0,1 osv.  
Navngiving kan variere mellom Linux-distribusjonar, så ein må ta og sjekke, bruk kommando:   
"dmesg | grep tty" for å sjekke kva som er riktig port.

# Installasjon
Installer pyserial "pip install pyserial"

# Bruk
Køyr `python ssh_setup_cisco.py`. Scriptet spør om dette, i denne rekkefølgja:

| Spørsmål | Døme | Forklaring |
|---|---|---|
| COM-port | `COM1` | Porten PC-en bruker for å snakke med eininga |
| Baudrate | `9600` (Enter) | Farten på seriellforbindelsen. Må vere lik på begge sider. |
| Hostname | `rs-r02` | Namnet eininga får |
| Domenenamn | `richard.local` | Må finnast for at RSA-nøkkelen kan lagast |
| SSH-brukarnamn | `cisco` | Brukarnamn som brukast til innlogging til SSH |
| SSH-passord | (skjult) | Passord som brukast til innlogging til SSH |
| Enable-passord | (skjult) | Passord ein treng for å komme inn i priviligert modus over SSH|
| RSA-storleik | `2048` (Enter) | Størrelsen på RSA-nøkkelen , default er 2048|
| Multilayer med `ip routing`? | `j` / `n` | Slår på ruting, så switchen kan sende trafikk mellom nettverk. Svar n på ruter og vanleg switch. |
| Interface | `gi0/0/0`, `vlan 20` | Porten eller VLAN-et som skal få IP-adresse, til dømes gi0/0/0, eller vlan 20. |
| IP-adresse og maske | `172.16.1.2` / `255.255.255.252` | Adressa eininga får på interfacet, og storleiken på nettverket. |
| Routa port (`no switchport`)? | `j` / `n` | Gjer ein fysisk port på multilayer-switch om til ein ruteport, så den kan ha IP-adresse. |
| Default gateway | `172.16.1.1` | Adressa trafikk til andre nettverk blir sendt til. Trykk Enter om det ikkje trengs. |
| Vanleg layer 2-switch? | `j` / `n` | Layer 2-switch brukar ip default-gateway, ruter og multilayer bruker ip route. Scriptet trenger å vite kva som gjeld |
| Lagre (`write memory`)? | `j` | Lagrar konfigurasjonen, så den ikkje forsvinner ved omstart. |

# Kva konfigurerer scriptet

| Kommando | Kva han gjer |
|---|---|
| `hostname`, `ip domain name` | Gir eininga eit namn. Domenenamnet må finnast før RSA-nøkkelen kan lagast. |
| `crypto key generate rsa modulus <storleik>` | Lagar RSA-nøkkelen som aktiverer SSH. |
| `username <namn> secret <passord>` | Lagar ein lokal brukar som ein loggar inn med over SSH. |
| `enable secret <passord>` | Passord for å kome inn i privilegert modus over nettverk. |
| `line vty 0 4`, `login local`, `transport input ssh` | Gjer at ein kan logge inn over SSH med den lokale brukaren, og berre SSH. |
| `ip routing` (valfri) | Slår på ruting på ein multilayer-switch. |
| `interface ...`, `ip address`, `no shutdown` | Set IP-adresse på interfacet. `no switchport` blir lagt til for ein routa port. |
| `ip default-gateway` eller `ip route 0.0.0.0 0.0.0.0` | Vegen ut til andre nettverk. |
| `write memory` (valfri) | Lagrar konfigurasjonen, så han ikkje forsvinn ved omstart. |

Ein vanleg layer 2-switch bruker `ip default-gateway`, medan ruter og multilayer-switch bruker ein default route (`ip route`). Derfor spør scriptet om eininga er ein vanleg layer 2-switch.

Scriptet gjer òg desse tinga av seg sjølv:
- Det prøver først `ip domain name`, og går til `ip domain-name` om eininga avviser den nye skrivemåten. Ulike IOS-versjonar bruker ulik skrivemåte.
- Det ventar lenge nok på at RSA-nøkkelen blir laga, og svarar `yes` om det alt finst ein nøkkel.
- Det fjernar gamle SSH-nøklar for IP-adressene du set frå `known_hosts` på PC-en (`ssh-keygen -R`). Då får du ikkje «host key»-feil etter at ei eining er nullstilt.

# Eksempel

## Ruter (rs-r02)
Ei ruter med to interface og ein default route:

| Spørsmål | Svar |
|---|---|
| COM-port | `COM1` |
| Baudrate | Enter (9600) |
| Hostname | `rs-r02` |
| Domenenamn | `richard.local` |
| Brukarnamn og passord | `cisco` og eit passord du vel |
| RSA-storleik | Enter (2048) |
| Multilayer med `ip routing`? | `n` |
| Interface 1 | `gi0/0/0`, `172.16.1.2`, `255.255.255.252`, routa port `n` |
| Interface 2 | `gi0/0/1`, `172.16.20.1`, `255.255.255.0`, routa port `n` |
| Default gateway | `172.16.1.1` |
| Vanleg layer 2-switch? | `n` (det er ei ruter) |
| Lagre | `j` |

## Multilayer-switch (rs-mls02)
Ein multilayer-switch med tre routa portar og ruting på:

| Spørsmål | Svar |
|---|---|
| Hostname | `rs-mls02` |
| Multilayer med `ip routing`? | `j` |
| Interface 1 | `gi1/0/1`, `172.16.98.2`, `255.255.255.248`, routa port `j` |
| Interface 2 | `gi1/0/2`, `172.16.1.1`, `255.255.255.252`, routa port `j` |
| Interface 3 | `gi1/0/3`, `172.16.1.5`, `255.255.255.252`, routa port `j` |
| Default gateway | Enter (ingen) |
| Lagre | `j` |

## Vanleg layer 2-switch (rs-sw04)
Ein switch med IP på `vlan 20`:

| Spørsmål | Svar |
|---|---|
| Hostname | `rs-sw04` |
| Multilayer med `ip routing`? | `n` |
| Interface | `vlan 20`, `172.16.20.11`, `255.255.255.0`, routa port `n` |
| Default gateway | `172.16.20.1` |
| Vanleg layer 2-switch? | `j` |

VLAN og porter på switchen blir sette opp med Ansible.

# Sjølvsjekk

Til slutt køyrer scriptet `show ip ssh` på eininga og skriv ut `OK: SSH er aktivt på enheten`, eller ein `ADVARSEL`.
Står det `ADVARSEL`, har noko feila på vegen. Sjå gjennom utskrifta frå scriptet etter feilmeldingar på hostname, domenenamn eller RSA-nøkkel. Køyr så dei same kommandoane manuelt i konsollen (for eksempel `crypto key generate rsa modulus 2048`) og sjekk med `show ip ssh` at det står `SSH Enabled`.

# Teste SSH
For å teste bruk: `ssh brukernamn@ip-adresse`
## Ved feilmeldinger
Eldre Cisco-einingar brukar gamle algoritmar som nye SSH-klientar har skrudd av. Då kan du få deil som `no matching key exhange method found`,`no matching cipher found`,`no matching MAC found`.  
Løysninga er å tillate dei gamle algoritmane for lab-nettverket, til dømes i fila `^/.ssh/config`(på Windows `C:\Users\<namn>\.ssh\config`):
Host 172.16.*
KexAlgorithms +diffie-hellman-group14-sha1
HostKeyAlgorithms +ssh-rsa
Ciphers +aes128-cbc,aes256-cbc
MACs +hmac-sha1

Instillingane gjeld berre adressen som startar på `172.16.`.
# Avgrensingar

- Scriptet set opp éi eining om gongen, over konsollkabel.
- Passord blir ikkje lagra. Dei blir spurt om og skrive inn skjult.
- Scriptet sjekkar ikkje kvar enkelt kommando. Det er berre sjølvsjekken til slutt som viser om SSH er aktivt.
- Eininga bør vere nullstilt. Scriptet svarar `no` på oppstartsdialogen som kjem etter nullstilling.
- Scriptet set IP-adresser, men ikkje VLAN, trunk, HSRP eller DHCP. Det gjer Ansible.
# Vidare

Når SSH og IP-adresser er på plass, tek Ansible over og konfigurerer resten av nettverket (VLAN, ruting, HSRP og DHCP). Sjå mappa `ansible/` i repoet.

