import argparse
import os.path
import json

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

parser.add_argument('--name', type=str, nargs=1,dest="electrolyte_name",required=False,
					help="Name of electrolyte in inventory",metavar="STR")

#PROCESS
from ElectrolyteComposition import ElectrolyteComposition, AEM_API

# make CID
# get info from solventDB, salt DB
args = parser.parse_args()
specs=json.load(args.json_filename)
if specs["method"]=="by_mass_fraction_and_molality":
	el=ElectrolyteComposition.by_mass_fraction_and_molality(solvents=specs["solvents"],salts=specs["salts"])
else:
	raise ValueError("'method' in json file must be supported by ElectrolyteComposition")

aem=AEM_API(electrolyte=el)
aem.generate_cues()
print("Querying AEM for {}".format(el.CompositionID))
aem.runAEM()
aem.process()

default_volume=60000
salt_m=specs["salts"][list(specs["salts"].keys())[0]]
inventory_temp=20
df_all=aem.data[inventory_temp]
df=df_all[df_all.m2==salt_m]
print("Returned {} lines, {} columns from AEM".format(len(df),len(df.columns)))

#        columns = ["m2",density (g/cc)","visc. (cP)","Spec. Cond. (mS/cm)",...]

aem_visc=float(df["visc. (cP)"])
aem_density=float(df["density (g/cc)"])

if args.electrolye_name:
    name=args.electrolye_name[0]
else:
    name=el.CompositionID

#name, valve, serial, solventDB_json, saltDB_json, date_created, density, viscosity
#make dict
#chemical   concentration   volume  valve   serial  rpm_derate  density (g/mL)  viscosity (cP)
#pump 1 derate - visc*1.7*-3.5+350
records=[]
for valve in args.valve_list[0]:
    record={}
    record["chemical"]=name
    record["concentration"]=salt_m
    record["volume"]=default_volume
    record["valve"]=valve
    record["serial"]=el.CompositionID
    record["rpm_derate"]=aem_visc*1.7*-3.5+350
    record["density (g/mL)"]=aem_density
    record["viscosity (cP)"]=aem_viscosity
    records.append(record)

print(records)


