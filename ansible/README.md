# Ansible-automatisering av STUD2

Playbooks som konfigurere nettverket for STUD2 på Cisco-utstyr med `cisco.ios`-samlinga.  
Alt som er ulikt frå eining til eining ligg i variabelfiler, så playbookane kan brukast på nytt utan å endrast. Er kun variabler i variabel fila som må endrast.

# Oversikt over nettverket

| Eining | Type | Rolle | Management-IP |
|---|---|---|---|
| `rs-mls02` | Multilayer-switch | Ruting mellom nettverka | `172.16.98.2` |
| `rs-r02` | Ruter | HSRP primær (prioritet 110), DHCP `.100–.149` | `172.16.1.2` |
| `rs-r04` | Ruter | HSRP sekundær (prioritet 100), DHCP `.150–.200` | `172.16.1.6` |
| `rs-sw04` | Layer 2-switch | VLAN 20, access- og trunk-portar | `172.16.20.11` |
| `rs-sw03` | Layer 2-switch | VLAN 20, access- og trunk-port | `172.16.20.12` |

HSRP virtuell IP (gateway for VLAN 20) er `172.16.20.254`.

# Krav

- Ansible, med `paramiko` under versjon 5 (nyare versjon støttar ikkje dei gamle SSH-algoritmane Cisco brukar, ender opp med å ikkje køyre gjennom playbooks)
- Samlingane `cisco.ios` og `ansible.netcommon`
- SSH må vere sett opp på alle einingane (sjå `python-ssh-setup/`), uten SSH vil ikkje noko funke.
- PC-en må ha nettverkstilgang til `172.16.x.x`

```
pip install ansible "paramiko<5"
ansible-galaxy collection install cisco.ios ansible.netcommon
```

# Mappestruktur

| Fil / mappe | Innhald |
|---|---|
| `inventory.ini` | Liste over einingane, IP-adressene deira og grupper |
| `group_vars/all.yml.example` | Mal for tilkopling og passord. Kopier til `all.yml` |
| `group_vars/all.yml` | Dine eigne passord. Ligg i `.gitignore` og skal **ikkje** ut på GitHub |
| `vars/network.yml` | Variablar som gjeld heile nettverket (VLAN, DNS, DHCP-leasetid) |
| `host_vars/<eining>.yml` | Variablar for ei eining (ruter, porter, HSRP, DHCP-pool) |
| `playbooks/` | Mappen playbooks ligger |
| `backups/` | Backup frå `backup_config.yml`. Ligg i `.gitignore`. Om einingar skal gjennoppretast. |

# Oppsett før første køyring

1. Kopier malen: `cp group_vars/all.yml.example group_vars/all.yml`
2. Opne `group_vars/all.yml` og skriv inn brukarnamn og passord du sette med SSH-scriptet.
3. Sjekk at IP-adressene i `inventory.ini` stemmer.
4. Test at Ansible kjem inn på alle einingane med `test_connections.yml` playbook:

```
ansible-playbook -i inventory.ini playbooks/test_connection.yml
```

# Inventory

Gruppene i `inventory.ini` bestemmer kva playbooks køyrer på:

| Gruppe | Einingar | Brukt til |
|---|---|---|
| `routers` | `rs-r02`, `rs-r04` | Ruting, HSRP, DHCP |
| `switches_l3` | `rs-mls02` | Ruting |
| `switches_l2` | `rs-sw03`, `rs-sw04` | VLAN, access- og trunk-portar |
| `cisco_devices` | Alle | Test og backup |

# Playbooks
Playbooksa er markert med tall for rekkefølge. Utan riktig rekkefølge vil playbooks køyre med feilmelding.
HSRP må vere oppe før switchane kan bruke virtuell IP som gateway. DHCP-poolen peikar mot samme virtuell-IP.
## Køyring av ein playbook
Viss du vil køyre ein ting om gangen, kan du enkelt køyre ein av playbooksa.
Du endrer variable fila for spesifikk eining og køyrer definert playbook.

##Køyring av alle playbooks.
Vi har ein hovudplaybook med namnet `site.yml`. Den inneholder null konfigurasjon, og køyrer berre dei andre playbooksa i rekkefølge.
Køyr alle stegene i rekkefølge:

```
ansible-playbook -i inventory.ini playbooks/site.yml
```

Eller eitt og eitt steg:

| Playbook | Køyrer på | Kva han gjer |
|---|---|---|
| `01_routing.yml` | `routers`, `switches_l3` | Slår på `ip routing` på multilayer-switchen og set statiske ruter (inkludert default route og floating static route) |
| `02_vlans.yml` | `switches_l2` | Opprettar VLAN, set access-portar og trunk-portar |
| `03_hsrp.yml` | `routers`, `switches_l2` | Set opp HSRP på ruterne, ventar til dei er Active/Standby, og peikar så switchane mot den virtuelle IP-en som default gateway |
| `04_dhcp.yml` | `routers` | Utelet adresser som ikkje skal delast ut, og lagar ein DHCP-pool per VLAN |
| `05_verify.yml` | Alle | Hentar status (`show ip interface brief`, `show standby brief`, `show ip dhcp pool`, `show ip route`) for å sjekke at alt stemmer |
| `site.yml` | Alle | Køyrer steg 01–05 etter kvarandre |
| `test_connection.yml` | `cisco_devices` | Sjekkar at Ansible kjem inn på einingane, og viser hostname og IOS-versjon |
| `backup_config.yml` | `cisco_devices` | Tek backup av `running-config` til mappa `backups/`, ei fil per eining |

Konfigurasjonen blir lagra automatisk (`save_when: modified`) når noko er endra.


# Variabelfiler

## Tilkopling: `group_vars/all.yml`

| Variabel | Døme | Forklaring |
|---|---|---|
| `ansible_connection` | `network_cli` | Kva måte Ansible snakkar med eininga på (SSH mot CLI) |
| `ansible_network_os` | `ios` | Kva type utstyr det er |
| `ansible_user` | `cisco` | Brukarnamn |
| `ansible_password` | (hemmeleg) | SSH-passord |
| `ansible_become` / `ansible_become_method` | `yes` / `enable` | Går inn i privilegert modus |
| `ansible_become_password` | (hemmeleg) | Enable-passord |
| `ansible_host_key_checking` | `false` | Hoppar over sjekk av host key (labben får nye nøklar ved nullstilling) |
| `ansible_command_timeout` | `60` | Kor lenge Ansible ventar på svar frå eininga |

## Felles for nettverket: `vars/network.yml`

| Variabel | Døme | Forklaring |
|---|---|---|
| `vlans` | `[{id: 20, name: VLAN20}]` | Liste over VLAN som skal finnast på layer 2-switchane |
| `dns_server` | `8.8.8.8` | DNS-tenar som DHCP deler ut |
| `dhcp_lease` | `"0 8"` | Leasetid (dagar timar), her 8 timar |

Vil du ha eit nytt VLAN, legg du berre til ei linje i `vlans` her.

## Per eining: `host_vars/<eining>.yml`

| Variabel | Brukt av | Forklaring |
|---|---|---|
| `ip_routing` | `01_routing.yml` | `true` slår på `ip routing` (berre multilayer-switch) |
| `static_routes` | `01_routing.yml` | Liste med `network`, `mask`, `next_hop` og valfri `distance` |
| `access_ports` | `02_vlans.yml` | VLAN-nummer og liste over portar som skal vere access |
| `trunk_ports` | `02_vlans.yml` | Interface og kva VLAN (`allowed_vlans`) trunken slepp gjennom |
| `hsrp` | `03_hsrp.yml` | Interface, gruppe, virtuell IP (`vip`) og `priority` |
| `default_gateway` | `03_hsrp.yml` | Gateway switchen får (HSRP virtuell IP) |
| `dhcp_pools` | `04_dhcp.yml` | Namn, nettverk, maske, `default_router` og `excluded` (adresser som ikkje skal delast ut) |

Kva fil som har kva:

| Fil | Variablar |
|---|---|
| `host_vars/rs-mls02.yml` | `ip_routing`, `static_routes` (til VLAN 20 via `rs-r02`, og floating route via `rs-r04` med distance 10) |
| `host_vars/rs-r02.yml` | `static_routes` (default route), `hsrp` (prioritet 110), `dhcp_pools` |
| `host_vars/rs-r04.yml` | `static_routes` (default route), `hsrp` (prioritet 100), `dhcp_pools` |
| `host_vars/rs-sw04.yml` | `default_gateway`, `access_ports`, `trunk_ports` |
| `host_vars/rs-sw03.yml` | `default_gateway`, `access_ports`, `trunk_ports` |

# Utvide eller bruke på nye einingar
Viss du ønsker å bruke det på ein ny eining:
| Eg vil... | Gjer dette |
|---|---|
| Legge til eit VLAN | Legg det til i `vlans` i `vars/network.yml`, og lag ein DHCP-pool og HSRP-gruppe i `host_vars` om det trengs |
| Flytte ein port til eit anna VLAN | Endre `access_ports` i `host_vars/<switch>.yml` |
| Legge til ei ny eining | Legg den i `inventory.ini` i riktig gruppe, og lag `host_vars/<namn>.yml` |
| Endre kven som er HSRP-primær | Endre `priority` i `hsrp` i `host_vars` |
| Endre DHCP-område | Endre `excluded` i `dhcp_pools` i `host_vars` |

Ingen av endringane krev at playbookane blir endra.

# Sjekke og feilsøke

| Kommando | Kva han gjer |
|---|---|
| `ansible-playbook -i inventory.ini playbooks/site.yml --check --diff` | Viser kva som ville blitt endra, utan å endre noko |
| `ansible-playbook -i inventory.ini playbooks/site.yml` (andre køyring) | Skal gi `changed=0`, så veit du at playbookane er idempotente |
| `ansible-playbook -i inventory.ini playbooks/05_verify.yml` | Viser status frå alle einingane |
| `ansible-playbook -i inventory.ini playbooks/backup_config.yml` | Tek backup av konfigurasjonen |

Vanlege feil:

| Feilmelding | Årsak og løysing |
|---|---|
| `no acceptable kex algorithm` | For ny `paramiko`. Køyr `pip install "paramiko<5"` |
| `host key mismatch` / `REMOTE HOST IDENTIFICATION HAS CHANGED` | Eininga er nullstilt og har ny nøkkel. Fjern den gamle: `ssh-keygen -R <ip>` |
| `Invalid input detected` | Feil interface-namn i `host_vars` for den eininga. Sjekk med `show ip interface brief` |
| `Authentication failed` | Feil brukarnamn eller passord i `group_vars/all.yml` |
| Timeout | Feil IP i `inventory.ini`, eller PC-en når ikkje eininga |
| `02_vlans.yml` viser `changed` kvar gong | VLAN på ein 2960 står ikkje i `running-config`. Det er normalt |

## Sjekke IP og kontakt i Linux/WSL
Får ikkje SSH eller Ansible kontakt med einingane, sjekk først kva IP-adresse PC-en brukar og om han når nettverket.

| Kommando | Kva han viser |
|---|---|
| `ip -br a` | IP-adressene til alle nettverkskort på maskina. Brukt adresse skal vere i `172.16.x.x` om du er kopla rett til labben |
| `ip route` | Rutetabellen, og kva som er default gateway |
| `ip route get 172.16.1.2` | Kva interface og kva kjelde-IP maskina brukar for å nå akkurat den eininga |
| `ping 172.16.1.2` | Om eininga svarar. Test og `172.16.98.2` (multilayer-switchen) |
| `nc -zv 172.16.1.2 22` | Om SSH-porten (22) er open på eininga |
| `ssh -v cisco@172.16.1.2` | Detaljert utskrift av SSH-tilkoplinga, viser kvar hen det stoppar |

I WSL får Linux ein eigen intern IP (`ip -br a` viser ofte `172.x.x.x` på `eth0`), og trafikken går ut via Windows. Sjekk derfor og Windows-adressa i PowerShell:

```
ipconfig
```

Det er Windows-adressa som må vere i same nettverk som labben (til dømes `172.16.98.x`). Slå av Wi-Fi om det blir brukt som standard veg ut, ellers går trafikken feil veg.

# Sikkerheit

- `group_vars/all.yml` inneheld passord og blir ikkje lasta opp (`.gitignore`). Berre `all.yml.example` ligg på GitHub.
- `backups/` ligg også i `.gitignore`, fordi `running-config` inneheld hasha passord.