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
components=["DMC_EC|50_50|LiPF6|2","DMC_EC|70_30|LiPF6|2","DMC_EC|70_30","DMC_EC|50_50"]

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
	step=0.01
	dim1=np.arange(0.30,0.50+step,step)
	#dim1=[x/100.0 for x in [30,50]]
	salt_m=2
	solvent="EC"
	cosolvent="DMC"
	salt="LiPF6"
	out_fn="aem_run.csv"
	dfs=[]
	for solvent_mass_fraction in dim1:
		el=ElectrolyteComposition.by_mass_fraction_and_molality(solvents={solvent:solvent_mass_fraction,cosolvent:1-solvent_mass_fraction},
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
		curr_df["CID"]=[el.CompositionID]*len(curr_df)
		curr_df["EC_mass_frac"]=[solvent_mass_fraction]*len(curr_df)
		dfs.append(curr_df)
		#print("Returned {} lines, {} columns from AEM".format(len(aem.data[30]),len(aem.data[30].columns)))

	df=pd.concat(dfs)
	df.to_csv(out_fn,index=False)
	print("Complete - {} rows in {}".format(len(df),out_fn))

