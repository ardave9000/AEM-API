import argparse
import os.path
import json
from ElectrolyteComposition import ElectrolyteComposition,AEM_API
import pandas as pd

def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return open(arg, 'r')  # return an open file handle


parser = argparse.ArgumentParser(description='Query AEM with JSON input file, create CSV of AEM output')

#INPUT
#electrolyte json file path
parser.add_argument("-f", dest="json_filename", required=True,
                    help="JSON input file specifying electrolyte", metavar="FILE",
                    type=lambda x: is_valid_file(parser, x))

parser.add_argument('-o', type=str, nargs=1,dest="output_filename",required=False,
					help="Name of electrolyte in inventory",metavar="STR")

parser.add_argument('-T', type=int, nargs=1,dest="temperature",required=False,
					help="Temperature (C) for AEM model, if not supplied assume 25C",metavar="STR")
#PROCESS
from ElectrolyteComposition import ElectrolyteComposition

# make CID
# get info from solventDB, salt DB
args = parser.parse_args()
specs=json.load(args.json_filename)
assert len(specs["salts"])>0, "Must supply salt in electrolyte to query AEM"

if args.temperature:
	assert args.temperature<=60 and args.temperature>=20,"Temperature selected must be between 20, 60"

if specs["method"]=="by_mass_fraction_and_molality":
	el=ElectrolyteComposition.by_mass_fraction_and_molality(solvents=specs["solvents"],salts=specs["salts"])
	#name, valve, serial, solventDB_json, saltDB_json, date_created, density, viscosity
else:
	raise ValueError("'method' in json file must be supported by ElectrolyteComposition")

aem=AEM_API(electrolyte=el)
aem.generate_cues()
print("Querying AEM for {}".format(el.CompositionID))
aem.runAEM()
aem.process()
print("Returned {} lines, {} columns from AEM".format(len(aem.data[30]),len(aem.data[30].columns)))

if args.output_filename:
	out_fn=args.output_filename[0]
	if out_fn[-4:]!=".csv":
		out_fn=out_fn+".csv"
else:
	out_fn="output.csv"

if args.temperature:
	df=aem.data[args.temperature[0]]

else:
	df_concat=pd.concat(aem.data[20],aem.data[30])
	by_row_index = df_concat.groupby(df_concat.index)
	df = by_row_index.mean()

df.to_csv(out_fn)

print("Complete - results in {}".format(out_fn))