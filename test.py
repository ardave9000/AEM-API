# coding: utf-8

from ElectrolyteComposition import ElectrolyteComposition, AEM_API


solvents={'EMC': 0.4314001, 'EC': 1.63333, "DMC":0.004}
salts={}

# cid = ElectrolyeComposition.dicts_to_CompositionID(solvents=solvents,salts=salts)
# print(cid)

# dicts=ElectrolyeComposition.CompositionID_to_dicts(cid)
# print(dicts["solvents"]["EMC"])

# comp=ElectrolyeComposition.by_CompositionID(cid)
# print(comp.CompositionID)

comp2=ElectrolyteComposition.by_mass_fraction_and_molality(solvents={'EC': 0.4314001, 'EMC': 1.63333, "DMC":0.004},salts={"LiPF6":1})
print(comp2.CompositionID)

aem=AEM_API(electrolyte=comp2)
aem.generate_cues()
print(aem.cues)