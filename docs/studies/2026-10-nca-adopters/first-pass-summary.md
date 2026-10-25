# Who uses Neural Cellular Automata: findings (25 Oct 2026)

**Method:** a short web pass, then a live ArticleCrawler/OpenAlex crawl. The crawl used 4 seeds and ran 3 iterations, with 25 papers sampled per iteration. It reached ~3,000 papers. Separately I pulled every direct citer of the seeds (239 unique papers) with their institutions.

## Adopters and fields

1. **Medical imaging: TU Darmstadt (Mukhopadhyay, Kalkhof).** This is the most concentrated group: 9 citing papers, across 3 of the 4 seeds. *Med-NCA* (MICCAI 2023, *Medical Image Analysis* 2025) matches UNet at ~500× fewer parameters and runs on a Raspberry Pi. Their follow-ups cover federated learning, edge training and diffusion. They also wrote the Sept 2026 applications survey (arXiv 2609.24595).
2. **Developmental biology and regeneration: Levin lab, Tufts / Wyss Institute (Levin, Hartl, Pio-Lopez).** 12 citing papers. NCAs serve as models of morphogenesis, bioelectric patterning and regeneration. Their review is arXiv 2509.11131; *BraiNCA* is arXiv 2604.01932.
3. **Robotics and artificial life: IT University of Copenhagen (Risi), with Trieste (Medvet) and OsloMet (Nichele).** ITU has the most citing papers of any institution (15). The work covers self-repairing soft robots ("Regenerating Soft Robots Through NCA") and growing 3D functional machines in Minecraft.
4. **Graphics and textures: EPFL (Pajouheshgar, Süsstrunk) with Google (Mordvintsev, Niklasson, Randazzo).** *MeshNCA* produces real-time animated textures on 3D meshes and runs in WebGL on phones. It is the closest thing to an interactive design tool. The Google authors are the original Distill team, so they count as originators rather than adopters.
5. **Games and procedural content: NYU (Togelius, Earle), USC, University of Malta (Khalifa).** This is the cluster you already knew about. The most-cited citer is the "Deep learning for procedural content generation" survey, with 161 citations.

## Surprising, outside games and reaction-diffusion

- **Photonic hardware.** At Caltech, Marandi's lab with NTT built *photonic* neural cellular automata, i.e. NCAs computed with light (*Light: Science & Applications* 2024).
- **Materials science.** Seoul National University used generative cellular automata to model the chiral growth of gold nanoparticles (*Nature Materials* 2024). Other work uses NCAs to reconstruct metal-solidification microstructures and to design disordered metamaterials (arXiv 2607.14475). The crawl's topic model picked up a separate "microstructure / solidification / metal" topic.
- **Molecular computing.** Caltech's Qian lab (DNA neural networks, *Nature* 2025) cites the seeds. This is adjacent to NCAs, not a direct use.
- **Edge and in-sensor vision.** UT Dallas runs real-time vision and depth estimation with NCAs on embedded systems (2026). There is also work on processing inside the image sensor itself (CUHK).
- **Industry is thin.** The only company I found is Brain-CA Technologies (Cincinnati, 2023), and the evidence is just a CB Insights profile. Google is the only industrial lab doing sustained work. I found no shipping NCA products.

## Caveats on the crawl results

- **The live crawl worked**, using about $0.05 of the $1/day OpenAlex key budget, with 0 API errors. Direct citations of the seeds are complete: 285 citation links, matching OpenAlex's own counts.
- **Integrity check:** none of the 2,944 DOIs matched Retraction Watch, and OpenAlex flagged none of the 239 citers as retracted.
- **OpenAlex coverage is probably low.** OpenAlex lists only 199 citers for *Growing NCA*. Distill and arXiv citations are known to be under-indexed, so treat the counts as relative, not absolute. I did not check them against Google Scholar.
