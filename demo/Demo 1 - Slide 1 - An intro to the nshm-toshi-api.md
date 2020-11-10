# Introducing 'Toshi' nshm-toshi-api 

The National Seismic Hazard Model (NSHM) programme has many sub-teams consuming and producing data using various software and services. 

NSHM teams and need to share, explore and re-use these data artefacts over the programme life-cycle.Some may end up as publicly available assets.

Ideally a single service can provide a consistent, secure and cost-effective solution for needs. 

**Key goals** for this service are:

 - store, retrieve, search and browse the NSHM tasks and data sets (CFM, fault geometries, rupture sets, inversions, etc) 
 - it is low-cost, for both development and operational dimensions
 - API is easily extensible to cover new data and tasks
 - schema controls to provide validations as required
 - data is equally available to internally and externally (to GNS)
 - easy to integrate for both automated tasks and web applications
 - uses open authorisations standards (Oauth2 JWT-token)
