# SSH-oppsett via konsollkabel

Scriptet automatiserar manuell oppsett gjennom terminal.  
Eininga blir kopla til over den serielle konsollkabelen og sender IOS-kommandoane som setter opp SSH-tilgang, i staden for å taste inn manuelt.

# Krav
Python 3, og biblioteket pyserial. Dette er det som faktisk lar Python snakke med ein seriellport. Uten den får ikkje den kontakt med portane.

# Fysisk tilkopling
Det blir brukt ein kabel med RJ45 i eine enden(koplast til konsollporten på switch/router).  
Her er det varierande frå kva kabel du brukar. Du kan bruke DB0-seriellport på PC, eller ein USB til seriell adapter.  
I seg sjølv er dette ikkje ein nettverkstilkopling.

# Finne riktig port
##Windows
Finne riktig port må du inn på enhetsbehandling.  
Enhetsbehandling -> Porter(COM og LPT) finn port med riktig tall, det er tallet eller namnet du oppgir i scriptet.
## Linux
På Linux heiter ein innebygd seriellport /dev/ttyS<tall>. Om det er ein USB-adapter, står det /dev/ttyUSB0,1 osv.  
Navngiving kan variere mellom Linux-distribusjonar, så ein må ta og sjekke, bruk kommando  
"dmesg | grep tty" for å sjekke kva som er riktig port.

# Installasjon
Installer pyserial "pip install pyserial"

# Bruk
Scriptet spør om ulike inputs fortløpande når du kjører den. I dette tilfellet "python ssh_setup_cisco.py"  
COM-portane, baudrate, hostname, domenenamn, brukernamn og passord, enable-passord inne på router/switch, RSA-nøkkelstørrelse.  
Mot slutt kan du velge kva IP-adresses skal vere på spesifikk interface. 

# Kva konfigurerer scriptet
Scriptet "ssh_setup_cisco.py" konfigurere hostname, domenenamn, nøkkelgenerering, RSA-nøkkelpar, opprettar ein lokal brukar og enable-passord.  
SSH blir aktivert av vty-linjene slik at ein kan logge inn over nettverk istadenfor konsoll.


