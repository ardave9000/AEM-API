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
from ElectrolyteComposition import ElectrolyteComposition

# make CID
# get info from solventDB, salt DB
args = parser.parse_args()
specs=json.load(args.json_filename)
if specs["method"]=="by_mass_fraction_and_molality":
	el=ElectrolyteComposition.by_mass_fraction_and_molality(solvents=specs["solvents"],salts=specs["salts"])
	#name, valve, serial, solventDB_json, saltDB_json, date_created, density, viscosity
	
else:
	raise ValueError("'method' in json file must be supported by ElectrolyteComposition")

