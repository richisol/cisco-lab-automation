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
Scriptet spør om ulike inputs fortløpande når du kjører den. I dette tilfellet "python ssh_setup_cisco.py"  
COM-portane, baudrate, hostname, domenenamn, brukernamn og passord, enable-passord inne på router/switch, RSA-nøkkelstørrelse.  
Mot slutt kan du velge kva IP-adresse som skal vere på eit spesifikt interface. 

Køyr `python ssh_setup_cisco.py`. Scriptet spør om dette, i denne rekkefølgja:

| Spørsmål | Døme | Forklaring |
|---|---|---|
| COM-port | `COM1` | Porten PC-en bruker for å snakke med eininga |
| Baudrate | `9600` (Enter) | Farten på seriellforbindelsen. Må vere lik på begge sider. |
| Hostname | `rs-r02` | Namnet eininga får |
| Domenenamn | `richard.local` | Må finnast for at RSA-nøkkelen kan lagast |
| SSH-brukarnamn | `cisco` | Brukarnamn som brukast til innlogging til SSH |
| SSH-passord | (skjult) | Passord som brukast til innlogging til  |
| Enable-passord | (skjult) | Passord ein treng for å komme inn i priviligert modus over SSH|
| RSA-storleik | `2048` (Enter) | Størrelsen på RSA-nøkkelen , default er 2048|
| Multilayer med `ip routing`? | `j` / `n` | Slår på ruting, så switchen kan sende trafikk  
mellom nettverk. Svar n på ruter og vanleg switch. |
| Interface | `gi0/0/0`, `vlan 20` | Porten eller VLAN-et som skal få IP-adresse, til dømes gi0/0/0, eller vlan 20. |
| IP-adresse og maske | `172.16.1.2` / `255.255.255.252` | Adressa eininga får på interfacet, og storleiken på nettverket. |
| Routa port (`no switchport`)? | `j` / `n` | Gjer ein fysisk port på multilayer-switch om til ein ruteport, så den kan ha IP-adresse. |
| Default gateway | `172.16.1.1` | Adressa trafikk til andre nettverk blir sendt til. Trykk Enter om det ikkje trengs. |
| Vanleg layer 2-switch? | `j` / `n` | Layer 2-switch brukar ip default-gateway, ruter og multilayer bruker  
ip route. Sriptet trenger å vite kva som gjeld |
| Lagre (`write memory`)? | `j` | Lagrar konfigurasjonen, så den ikkje forsvinner ved omstart. |

# Kva konfigurerer scriptet
Scriptet "ssh_setup_cisco.py" konfigurerer hostname, domenenamn, og RSA-nøkkelpar, opprettar ein lokal brukar og enable-passord.  
SSH blir aktivert av vty-linjene slik at ein kan logge inn over nettverk istadenfor konsoll.


