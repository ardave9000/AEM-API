import argparse
import os.path
import json
from ElectrolyteComposition import ElectrolyteComposition,AEM_API
import pandas as pd
import numpy as np
import pdb
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d

#dimension 1: EC mass fraction 0.30 : 0.05 :0.50
#dimension 2: LiPF6 molality (will be handled implicitly with LiPF6 molality)
step=0.05
dim1=np.arange(0.10,0.60+step,step)
salt_m=2
solvent="EC"
cosolvent="DMC"
salt="LiPF6"
out_fn="EC_demo_full.csv"

# dfs=[]
# for solvent_mass_fraction in dim1:
# 	el=ElectrolyteComposition.by_mass_fraction_and_molality(solvents={solvent:solvent_mass_fraction,cosolvent:1-solvent_mass_fraction},
# 															salts={salt:salt_m})
# 	aem=AEM_API(electrolyte=el)
# 	aem.generate_cues()
# 	print("Querying AEM for {}".format(el.CompositionID))
# 	aem.runAEM()
# 	aem.process()
# 	df_concat=pd.concat([aem.data[20],aem.data[30]])
# 	by_row_index = df_concat.groupby(df_concat.index)
# 	curr_df = by_row_index.mean()
# 	#Add addt'l columns
# 	curr_df["CID"]=[el.CompositionID]*len(curr_df)
# 	curr_df["EC_mass_frac"]=[solvent_mass_fraction]*len(curr_df)
# 	dfs.append(curr_df)
# 	#print("Returned {} lines, {} columns from AEM".format(len(aem.data[30]),len(aem.data[30].columns)))

# df=pd.concat(dfs)
# df.to_csv(out_fn,index=False)
# print("Complete - {} rows in {}".format(len(df),out_fn))

df=pd.read_csv(out_fn)
print("Plotting")
# Creating figure
fig = plt.figure(figsize = (10, 7))
ax = plt.axes(projection ="3d")
field="Cond (mS) 2"
# field="cP_mean"
# field="density (g/mL)"
x,y,z=df.m,df.EC_mass_frac,df[field]
# Creating plot
ax.scatter(x, y, z, c = z, cmap='inferno')
ax.set_xlabel("Salt molality")
ax.set_ylabel("EC mass fraction (vs. DMC)")
ax.set_zlabel(field)
plt.show()