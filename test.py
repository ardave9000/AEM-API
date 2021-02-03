# coding: utf-8

from ElectrolyteComposition import ElectrolyteComposition, AEM_API


solvents={'EMC': 0.7, 'EC': 0.3}
salts={}

# cid = ElectrolyeComposition.dicts_to_CompositionID(solvents=solvents,salts=salts)
# print(cid)

# dicts=ElectrolyeComposition.CompositionID_to_dicts(cid)
# print(dicts["solvents"]["EMC"])

# comp=ElectrolyeComposition.by_CompositionID(cid)
# print(comp.CompositionID)

comp2=ElectrolyteComposition.by_mass_fraction_and_molality(
	solvents=solvents,salts={"LiPF6":1})
print(comp2.CompositionID)

aem=AEM_API(electrolyte=comp2)
#aem.aem_exe_filename="AEM/"+aem.aem_exe_filename
aem.generate_cues()
print(aem.cues)
print(aem.aem_exe_filename)
aem.runAEM()
aem.process()
print(aem.data[30])