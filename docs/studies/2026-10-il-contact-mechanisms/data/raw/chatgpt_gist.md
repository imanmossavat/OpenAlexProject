<!-- ChatGPT deep research, human gist prompt (the question only), output verbatim as supplied by the user on 2026-10-29. The output is in Dutch although the prompt was in English. -->
# Samenvatting  
In recente studies van imitatieleren voor contactrijke manipulatie zijn verschillende faalmechanismen geïdentificeerd en experimenteel aangepakt. Een terugkerend probleem is dat beleid dat alleen op zichttrends is getraind (visie-only) faalt bij taken met complexe contacten (bijv. strakke inpassingen of occlusie), terwijl toevoeging van tactiele waarneming dit grotendeels oplost. Evenzo faalt imitatie zonder krachtsensatie bij taken met hoekdruk, wat verbetert door een F/T-sensor en aangepaste architectuur te gebruiken. Andere faalmechanismen zijn gebrek aan algemene generalisatie bij variërende taakconfiguraties (opgelost met milieurichtsnoeren en online correcties) en gebrek aan reactie op verstoringen in eind-tot-eindbeleid (opgelost door een hiërarchische “slow-fast” aanpak met real-time feedback). In alle gevallen bleken interventies zoals sensoruitbreiding, architectuurwijzigingen, aangepaste leermethoden of data-augmentatie de prestaties spectaculair te verbeteren (bijv. succeskansen van ~35% naar ~80%, of van 0% naar 100%). Onderstaande tabel en figuur vatten de gevonden mechanismen, interventies, taken, effectgroottes en bronnen samen.

```mermaid
flowchart LR
    F1[Visie-only IL faalt (occlusies/strakke passing)] 
    I1[Tactiele sensoren + multimodale fusie (MiTaS)] 
    F1 --> I1 --> E1[Prestatie stijgt van 35% naar 80%]

    F2[Geen krachtfeedback ⟶ slip bij schroefdopopening] 
    I2[Voeg F/T-sensor en transformer toe] 
    F2 --> I2 --> E2[Succes ~83% (DA-force) vs falende ablaties]

    F3[IL-policy generaliseert niet naar nieuwe configuraties] 
    I3[Milieurichtsnoeren & correcties (EC-primitieven)] 
    F3 --> I3 --> E3[Baselines ~0% → 100% succes]

    F4[Visueel-only diffusiebeleid faalt bij nauw aansluitende montage] 
    I4[Kracht-geconditioneerde diffusie + data-augmentatie] 
    F4 --> I4 --> E4[Verbeterde succeskans vs standaard diffusie]

    F5[Open-loop IL reageert traag op verstoringen] 
    I5[Reactief “slow-fast” diffusiebeleid (RDP)] 
    F5 --> I5 --> E5[>35% betere prestaties vs alleen-visie IL]
```

| **Faalmechanisme** | **Interventie (type)** | **Taak (robot/sim)** | **Effect (maat)** | **Replicatie** | **Bron** |
|---|---|---|---|---|---|
| *Visie-only beleid* faalt door occlusie/complex contact | Multisensor-input: GelSight + event-tactiel, transformer-architectuur (MiTaS) | 5 contactrijke taken (e.g. tandwielmontage, sleutelinsteek, real-world, Flexiv Rizon) | Succes 35% → 80% | Geen gerapporteerd | Krohn *et al.* (2026, CoRL) |
| *Sleutel-in-slot*: geen generalisatie naar nieuwe geometriën | Gebruik van omgevingsconstraints (geometrische ‘milieuprimitieven’), zelf-exploratie en menselijke correcties | Multi-stage slots / montage (real-world) | Baseline 0% → 100% (10/10) | Niet gerpliseerd | Li & Brock (2026) |
| *Ontbrekende krachtfeedback* ⟶ slip tijdens cap-opening | Master-demo systeem met F/T-sensor, dual-action transformer, visuele aandacht (gaze) | Flesdop-opentaken (real-world) | 83.3% succes (DA-force); ablaties faalden | n.v.t. | Kim *et al.* (2023, TRO) |
| *Conventionele diffusiebeleid* faalt bij nauwsluitende montage | Diffusie-imitatie met forcementering en data-augmentatie | Bimanuële assemblage van batterijdeksel (real-world) | Verbeterd succes en efficiëntie t.o.v. standaard diffusie | n.v.t. | Shukla *et al.* (2025, NAMRC) |
| *Open-loop IL* reageert traag op verstoringen | “Slow-fast” reactief diffusiebeleid (RDP) + AR-tactiele feedback | Contactrijke taken (realiseren komkommer schillen, vegen, bimanueel tillen; real-world) | >35% prestatieverbetering vs visueel IL | n.v.t. | Xue *et al.* (2025, RSS) |

**Opmerkingen reproducerbaarheid:** Belangrijke experimentele details zijn opgenomen in de bronnen. Enkele voorbeelden: de MiTaS-studie gebruikte een Flexiv Rizon-arm met een Robotis-gripper, een RealSense-camera en GelSight+Evetac sensoren aan 30-demonstraties; evaluatie bestond uit 20 uitvoeringen per model. De single-demo-EC-benadering gebruikte slechts 1 demonstratie plus aanvullende correcties per taak (gerapporteerd: 10 trials per configuratie). Kim *et al.* (2023) splitste de dataset 90%/10% voor training/validatie en voerde ~18 proeven uit op fles A. Shukla *et al.* trainden op ~100 handgeleide demonstraties (bimanuele systeem). Xue *et al.* verzamelden 60–80 demonstraties voor de taken (3 taken) met realtime F/T-feedback. Gewichten, leersnelheden en seed-instellingen staan in de originele papers. 

**Bronnen:** Bovenstaande bevindingen zijn ontleend aan primaire literatuur en auteurs-code/publicaties. Deze omvatten recente peer-reviewed werken in robotica. Where necessary, exacte effectgroottes of niet-gevonden statistieken zijn expliciet vermeld.
