import argparse
import os.path
import json
import pandas as pd

def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return open(arg, 'r')  # return an open file handle


parser = argparse.ArgumentParser(description='Prepare data for input to CLIO inventory.csv!')

#INPUT
#electrolyte json file path
parser.add_argument("-f", dest="json_filename", required=True,
                    help="JSON input file specifying electrolyte", metavar="FILE",
                    type=lambda x: is_valid_file(parser, x))

parser.add_argument('--valves', type=int, nargs='+',dest="valve_list",required=True,
					help="Valves filled by electrolyte",metavar="INT")

# parser.add_argument('--name', type=str, nargs=1,dest="electrolyte_name",required=False,
# 					help="Name of electrolyte in inventory",metavar="STR")

from ElectrolyteComposition import ElectrolyteComposition, AEM_API

args = parser.parse_args()
specs=json.load(args.json_filename)
salt_m=specs["salts"][list(specs["salts"].keys())[0]]
if specs["method"]=="by_mass_fraction_and_molality":
	el=ElectrolyteComposition.by_mass_fraction_and_molality(solvents=specs["solvents"],salts=specs["salts"])
else:
	raise ValueError("'method' in json file must be supported by ElectrolyteComposition")

aem=AEM_API(electrolyte=el)
aem.generate_cues()
print("Querying AEM for {}".format(el.CompositionID))
aem.runAEM()
aem.process()

if salt_m==0: #grab the lowest value here
	aem_salt_m=0.025
else:
	aem_salt_m=salt_m

default_volume=60000
inventory_temp=20
aem_df_all=aem.data[inventory_temp]
aem_df=aem_df_all[aem_df_all.m==aem_salt_m]
print("Returned {} lines, {} columns from AEM".format(len(aem_df),len(aem_df.columns)))

if salt_m==0:
	el=ElectrolyteComposition.by_mass_fraction_and_molality(solvents=specs["solvents"],salts={})
#        columns = ["m2",density (g/cc)","visc. (cP)","Spec. Cond. (mS/cm)",...]
aem_visc=float(aem_df["cP_mean"])
aem_density=float(aem_df["density (g/mL)"])
name=el.CompositionID

#name, valve, serial, solventDB_json, saltDB_json, date_created, density, viscosity
#make dict
#chemical   concentration   volume  valve   serial  rpm_derate  density (g/mL)  viscosity (cP)
#pump 1 derate - visc*1.7*-3.5+350
records=[]
for valve in args.valve_list:
    record={}
    record["chemical"]=name
    record["concentration"]=salt_m
    record["volume"]=default_volume
    record["valve"]=valve
    record["serial"]=el.CompositionID
    record["rpm_derate"]=(aem_visc*1.7*-3.5+350)/350
    record["density (g/mL)"]=aem_density
    record["viscosity (cP)"]=aem_visc
    record["date_made"]=el.date
    infos=el.dump_info()
    record["solvent_info"]=infos["solvents"]
    record["salt_info"]=infos["salts"]
    records.append(record)

std_fn="prep_inventory_output.csv"
if os.path.exists(std_fn):
	curr_df=pd.read_csv(std_fn)
	df=pd.concat([curr_df,pd.DataFrame(records)])
else:
	df=pd.DataFrame(records)
df.to_csv(std_fn,index=False)
print("{} rows output to {}".format(len(df),std_fn))
