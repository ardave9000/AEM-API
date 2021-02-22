import argparse
import os.path
import json
from ElectrolyteComposition import ElectrolyteComposition,AEM_API
import pandas as pd
import numpy as np
import pdb
import json

solvent_disc=100 #uL
mix_volume=1900
densities_all={"DMC_EC|60_40|LiPF6|1.5":1.296,"DEC_EC|60_40|LiPF6|1.5":1.226,"DMC_EC|60_40":1.166,"DEC_EC|60_40":1.097}
components=list(densities_all.keys())

#MAKE CONFIG JSON
if False:
	itemstr="0:{}:{}".format(solvent_disc,mix_volume+solvent_disc)
	axes={}
	for i,component in enumerate(components):
		ax_name="x{}".format(i)
		axes[ax_name]={"name":ax_name,"type":"discrete_numeric","items":itemstr}
	axes_names=[axes[ax]["name"] for ax in axes.keys()]
	constraints={"constraint_1":{"name":"total_volume", "constraint": "+".join(axes_names)+f"=={mix_volume}"}}

	config={}
	config["name"]="df_opt"
	config["domain"]=axes
	config["domain_constraints"]=constraints
	json.dump(config,open("df_config.json","w"))

#QUERY AEM AT THAT DISCRETIZATION
if True:
	dim1=[float(x) for x in '0.0-0.05-0.1-0.15-0.2-0.25-0.3-0.35-0.4-0.45-0.5-0.55-0.6-0.65-0.7-0.75-0.8-0.85-0.9-0.95-1.0'.split("-")]
	salt_m=1.5
	solvent="EC"
	cosolvent1="DMC"
	cosolvent2="DEC"
	salt="LiPF6"
	out_fn="aem_run.csv"
	dfs=[]
	for cosolvent_ratio in dim1:
		el=ElectrolyteComposition.by_mass_fraction_and_molality(solvents={solvent:0.4,cosolvent1:cosolvent_ratio*0.6,cosolvent2:(1-cosolvent_ratio)*0.6},
																salts={salt:salt_m})
		aem=AEM_API(electrolyte=el)
		aem.generate_cues()
		print("Querying AEM for {}".format(el.CompositionID))
		aem.runAEM()
		aem.process()
		aem20=aem.data[20]
		aem30=aem.data[30]
		aem20["T"]=[20]*len(aem20)
		aem30["T"]=[30]*len(aem30)
		curr_df=pd.concat([aem20,aem30])
		# by_row_index = df_concat.groupby(df_concat.index)
		# curr_df = by_row_index.mean()
		#Add addt'l columns
		#curr_df["CID"]=[el.CompositionID]*len(curr_df)
		curr_df["dim1"]=[cosolvent_ratio]*len(curr_df)
		dfs.append(curr_df)
		#print("Returned {} lines, {} columns from AEM".format(len(aem.data[30]),len(aem.data[30].columns)))

	df=pd.concat(dfs)
	df.to_csv(out_fn,index=False)
	print("Complete - {} rows in {}".format(len(df),out_fn))

