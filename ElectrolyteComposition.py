import subprocess as sp
import pandas as pd
import re
import collections
from collections import OrderedDict
import pdb
import datetime
import json
import os

delim1="|"
delim2="_"
default_salt_decimals=2
default_solvent_precision=100
vals2str = lambda ls : [str(x) for x in ls]

class ElectrolyteComposition:
    # * TODOs: 
    #     * Init by mass - solvent masses or mass fractions, salt mass or molality
    #     * Calculate molality, calculate mole fractions
    #     * Given bottle concentrations + densities, give volume fractions
    #     * init from JSON specifier
    def __init__(self,solvents=None,salts=None,specified_from=None,solvent_DB=None,salt_DB=None,CompositionID=None,
                solvent_precision=default_solvent_precision, salt_decimals=default_salt_decimals):
        self.solvents=dict() if solvents==None else solvents
        self.salts=dict() if salts==None else salts
        self.specified_from="" if specified_from==None else specified_from #will contain info from classmethod used to create
        self.solvent_DB=self.load_solvent_DB() if solvent_DB==None else solvent_DB
        self.salt_DB=self.load_salt_DB() if salt_DB==None else salt_DB
        self.CompositionID="" if CompositionID==None else CompositionID
        self.solvent_precision=solvent_precision
        self.salt_decimals=salt_decimals
        #Get date of composition made
        self.date=datetime.datetime.now().strftime("%m/%d/%Y")
        if len(salts)>1:
            raise NotImplementedError("Binary salts not implemented, yet - Ady")
    def dump_info(self):
        solvent_DB=self.solvent_DB
        salt_DB=self.salt_DB
        filt_solvent_info=solvent_DB[solvent_DB.name.isin(self.solvents.keys())].to_json(orient="records")
        filt_salt_info=salt_DB[salt_DB.name.isin(self.salts.keys())].to_json(orient="records")
        #r_d={"chemicals":{"solvents":filt_solvent_info,"salts":filt_salt_info}}
        return {"solvents":filt_solvent_info,"salts":filt_salt_info}
    def name_composition(self):
        rep=self.CompositionID.replace("_","")
        return rep.replace("|","")
    def to_solution_volume(self):
        return

    @staticmethod
    def cid_to_parsable(cid):
        rep=cid.replace("_","")
        return rep.replace("|","")
    @staticmethod
    def normalize_solvent_dictionary(solvents,solvent_precision):
        #pdb.set_trace()
        total=float(sum(solvents.values()))
        _solvents={solvent:int(round(solvents[solvent]/total*solvent_precision)) for i,solvent in enumerate(solvents.keys())}#round
        _solvents_nonzero={solvent:_solvents[solvent] for solvent in _solvents.keys() if _solvents[solvent]!=0}#filter
        ordered_solvents=OrderedDict(sorted(_solvents_nonzero.items(), key=lambda tup: tup[0]))
        return ordered_solvents
    @staticmethod
    def normalize_salt_dictionary(salts,salt_decimal):
        _salts={salt:round(salts[salt],salt_decimal) for salt in salts.keys()} #round
        _salts_nonzero={salt:_salts[salt] for salt in _salts.keys() if _salts[salt]!=0.0} #filter
        ordered_salts=OrderedDict(sorted(_salts.items(), key=lambda tup: tup[0]))
        return ordered_salts
    @staticmethod
    def load_solvent_DB(data_path=os.path.dirname(os.path.realpath(__file__)),filename="data/solventDB.csv"):
        path=os.path.join(os.path.dirname(os.path.realpath(__file__)),filename)
        return pd.read_csv(path)
    @staticmethod
    def load_salt_DB(data_path=os.path.dirname(os.path.realpath(__file__)),filename="data/saltDB.csv"):
        path=os.path.join(os.path.dirname(os.path.realpath(__file__)),filename)
        return pd.read_csv(path)
    @staticmethod
    def dicts_to_CompositionID(solvents={},salts={},solvent_precision=default_solvent_precision,salt_decimals=default_salt_decimals):
        #Filter
        solvents_normalized=ElectrolyteComposition.normalize_solvent_dictionary(solvents,solvent_precision)
        if len(salts)!=0:
            salts_normalized=ElectrolyteComposition.normalize_salt_dictionary(salts,salt_decimals)
            return delim1.join([delim2.join(x) for x in [solvents_normalized.keys(),vals2str(solvents_normalized.values()),salts_normalized.keys(),vals2str(salts_normalized.values())]])
        else:
            return delim1.join([delim2.join(x) for x in [solvents_normalized.keys(),vals2str(solvents_normalized.values())]])
    @staticmethod
    def CompositionID_to_dicts(CompositionID):
        ls=CompositionID.split(delim1)
        solvent_names=ls[0].split(delim2)
        solvent_mfs=[i for i in ls[1].split(delim2)] #normalize?
        assert len(solvent_names)==len(solvent_mfs), "CompositionID is invalid, different lengths for solvent_names vs solvent_mfs"
        assert 0 not in solvent_mfs, "Zeros not allowed in defining composition" #still caught by normalizing
        solvent_mfs_precisions=list(set([len(i) if len(i)>1 else 2 for i in solvent_mfs]))
        assert len(solvent_mfs_precisions)==1, "Length (precision) of solvent mass fractions must be identical: {}".format(solvent_mfs_precisions)
        #pdb.set_trace()
        solvent_precision=int(10**int(solvent_mfs_precisions[0]))
        solvent_mfs=[float(i) for i in solvent_mfs]
        solvents=ElectrolyteComposition.normalize_solvent_dictionary({solvent_names[i]:solvent_mfs[i] for i in range(len(solvent_names))},solvent_precision)
        salt_decimals=default_salt_decimals #temporary!
        if len(ls)>2:
            assert len(ls)==4, "If salts are added, must define molality"
            salt_names=ls[2].split(delim2)
            molality=[float(i) for i in ls[3].split(delim2)]
            assert len(salt_names)==len(molality), "CompositionID is invalid, different lengths for salt_names vs molality"
            salts=ElectrolyteComposition.normalize_salt_dictionary({salt_names[i]:molality[i] for i in range(len(salt_names))},salt_decimals)
        else:
            salts={}
        return {"solvents":solvents,"salts":salts,"solvent_precision":solvent_precision,"salt_decimals":salt_decimals}
    @classmethod
    def by_CompositionID(cls, CompositionID):
        dicts=cls.CompositionID_to_dicts(CompositionID)
        return cls(**dicts,CompositionID=CompositionID,specified_from=json.dumps({"CompositionID":CompositionID}))
    @classmethod
    def by_mass(cls,solvents={},salts={}): #solvent mass, salt mass
        raise NotImplementedError
    @classmethod
    def by_mass_fraction_and_molality(cls,solvents={},salts={},solvent_precision=default_solvent_precision,salt_decimals=default_salt_decimals): #solvent mass fraction, salt molality
        solvents_orig=solvents.copy()
        salts_orig=salts.copy()
        solvents_normalized=cls.normalize_solvent_dictionary(solvents,solvent_precision)
        if len(salts)!=0:
            salts_normalized=cls.normalize_salt_dictionary(salts,salt_decimals)
        else:
            salts_normalized=salts
        cid=cls.dicts_to_CompositionID(solvents=solvents_normalized,salts=salts_normalized,solvent_precision=solvent_precision,salt_decimals=salt_decimals)
        d={"solvents":solvents_normalized,"salts":salts_normalized,"CompositionID":cid,"solvent_precision":solvent_precision,"salt_decimals":salt_decimals}
        return cls(**d,specified_from=json.dumps({"by_mass_fraction_and_molality":{"solvents":solvents_orig,"salts":salts_orig}}))
    @classmethod
    def by_solution_volume(cls,volumes={},densities={},solvent_precision=default_solvent_precision,salt_decimals=default_salt_decimals):
        solvent_DB=cls.load_solvent_DB()
        salt_DB=cls.load_salt_DB()
        volumes={k:int(v) for k,v in volumes.items()}
        densities={k:float(v) for k,v in densities.items()}
        specified_from=json.dumps({"by_solution_volume":{"volumes":volumes.copy(),"densities":densities.copy()}})
        solvents={} #mass fraction
        salts={} #molality
        solvents_mass={}
        salts_moles={}
        assert set(volumes.keys())==set(densities.keys()), "Same keys must be in each of volumes and densities"
        total_dose_masses={solution:volumes[solution]/1000*densities[solution] for solution in volumes.keys()} #this is in grams
        for solution in total_dose_masses.keys():
            solution_comp=cls.CompositionID_to_dicts(solution) #solution_comp["solvents"] is m.f.; '' ["salts"] is molal
            source_solvent_precision=int(solution_comp["solvent_precision"])

            #BOTTLE LEVEL
            solution_total_salt_mass=0
            if len(solution_comp["salts"])!=0:
                for salt in solution_comp["salts"].keys():
                    assert salt in salt_DB.name.values, "Salt proposed that is not in salt_DB, please check! - {}".format(salt)
                    mm=float(salt_DB[salt_DB.name==salt]["molar mass"].iloc[0])
                    m=solution_comp["salts"][salt]
                    solution_total_salt_mass += mm*m #g/mol * molality of single salt = mass of this salt in bottle
            solution_salt_mass_fraction = solution_total_salt_mass / (solution_total_salt_mass+1000)
            solution_solvent_mass_fraction = 1-solution_salt_mass_fraction

            #DOSE LEVEL
            dose_total_solvent_mass=solution_solvent_mass_fraction*total_dose_masses[solution]
            for solvent in solution_comp["solvents"].keys():
                if solvent not in solvents_mass:
                    solvents_mass[solvent]=dose_total_solvent_mass*solution_comp["solvents"][solvent]/source_solvent_precision
                else:
                    solvents_mass[solvent]+=dose_total_solvent_mass*solution_comp["solvents"][solvent]/source_solvent_precision
            if len(solution_comp["salts"])!=0:
                for salt in solution_comp["salts"].keys():
                    m=solution_comp["salts"][salt]
                    if salt not in salts_moles:
                        salts_moles[salt]=m*dose_total_solvent_mass/1000
                    else:
                        salts_moles[salt]+=m*dose_total_solvent_mass/1000
        
        #EVERYTHING HAS BEEN TOTALED
        solvents=cls.normalize_solvent_dictionary(solvents_mass,solvent_precision)
        salts=cls.normalize_salt_dictionary({salt:salts_moles[salt]/(sum(list(solvents_mass.values())))*1000 for salt in salts_moles},salt_decimals)
        cid=cls.dicts_to_CompositionID(solvents=solvents,salts=salts,solvent_precision=solvent_precision,salt_decimals=salt_decimals)
        #total salts into moles each, total solvents into mass each, give molality.
        d={"solvents":solvents,"salts":salts,"CompositionID":cid,"solvent_precision":solvent_precision,"salt_decimals":salt_decimals}
        return cls(**d,specified_from=specified_from)

class AEM_API:
    #TODO: input temperature
    def read_AEM_data(self,salt_csv,solvent_csv):
        saltDF = pd.read_csv(salt_csv)
        solventDF = pd.read_csv(solvent_csv)
        salts = saltDF.set_index('string').T.to_dict('list')
        salts = {k.strip():[v[0],v[1].strip()] for k,v in salts.items()}
        solvents = solventDF.set_index('string').T.to_dict('list')
        solvents = {k.strip():[v[0],v[1].strip()] for k,v in solvents.items()}
        self.AEM_solvents = solvents
        self.AEM_salts = salts
    def __init__(self,electrolyte=None,
        salt_csv='data/AEM_salts.csv',solvent_csv='data/AEM_solvents.csv'):
        self.read_AEM_data(salt_csv,solvent_csv)
        assert isinstance(electrolyte, ElectrolyteComposition), "Pass ElectrolyteComposition object to this class"
        for solvent in electrolyte.solvents.keys():
            if solvent not in self.AEM_solvents:
                raise ValueError("solvent string input {} not in AEM system".format(solvent))
        for salt in electrolyte.salts.keys():
            if salt not in self.AEM_salts:
                raise ValueError("salt string input not in AEM system")
        #if len(salts) > 1:
        #   raise ValueError("binary salt mixture not yet supported")
        #self.solvents = {k:v for k,v in solvents.items() if v != 0}
        self.electrolyte=electrolyte
        self.cues = False
        self.run_yet = False
        self.data_processed=False
        self.aem_exe_filename="aem-2202.exe"
        self.report_string="Report1 -- Summary of Key Properties"
        self.surface_tension_string="Report16 -- Surface Tension and pore filling time over salt conc"
        self.tmin=20
        self.tmax=60
        self.salt_offset=0.1 #for ensuring equality in salt molality comparison
    def generate_cues(self):
        cues = []
        cues.append(1) #single fixed composition
        cues.append(2) #solvents on mass basis
        assert len(self.electrolyte.solvents)<=10, "Number of solvents must be no greater than 10"
        cues.append(len(self.electrolyte.solvents)) #number of solvents
        for solvent in self.electrolyte.solvents.keys():
            cues.append(self.AEM_solvents[solvent][0]) #append cues
        if len(self.electrolyte.solvents.keys())>1: #check if not pure
            #cues.append(1) #select fixed composition of solvent mixture
            for solvent in self.electrolyte.solvents:
                cues.append(self.electrolyte.solvents[solvent]) #append masses
        number_of_salts = len(self.electrolyte.salts)
        cues.append(number_of_salts)
        for salt in self.electrolyte.salts.keys():
            cues.append(self.AEM_salts[salt][0]) #append cues
        if number_of_salts>1: cues.append(1) #specify single fixed salt prop
        for salt in self.electrolyte.salts:
            cues.append(self.electrolyte.salts[salt]+self.salt_offset) #append molalities
        cues.append(self.tmin)
        cues.append(self.tmax)
        cues.append(10) #select 10 degree step-size
        cues.append(1) #Choose triple ion stability normal
        cues.append(90) #pore angle
        cues.append(50) #pore length
        cues.append(0.1) #max pore salt
        cues.append(0) #Surface-charge attenuated Electrolyte Permittivity
        cues.append(0) #Double layer calc
        cues.append(0) #end calculations
        #cues.append(0)
        self.cues = cues
    def runAEM(self,quiet=True):
        if self.cues == False:
            raise ValueError("cues not populated, run generate_cues first")
        #generate input byte string
        inp = [str(cue) for cue in self.cues]
        inpb = bytes('\n'.join(inp)+'\n',encoding="ascii")
    
        #launch AEM and pass input byte string
        if quiet:
            out=sp.DEVNULL
        else:
            out=sp.STDOUT
        p = sp.Popen(self.aem_exe_filename,stdin=sp.PIPE,stdout=out,stderr=sp.STDOUT)
        p.communicate(inpb)
        self.run_yet=True
        
    def process(self,surface_tension=False):
        if self.run_yet==False:
            raise ValueError("Run AEM first for this Electrolyte object")
        f = open(self.report_string,'r')
        lines = f.readlines()
        d={}
        for num1,line in enumerate(lines):
            if "Results" in line:
                num2 = num1 + 1
                arr = []
                reading = True
                while(reading==True):
                    if "TI Stability" in lines[num2]:
                        reading = False
                    else:
                        arr.append(lines[num2])
                        num2 += 1
                d[line] = arr

        #process keys down to temperature
        def get_key_single(string):
            string_in_list = string.strip().split()
            return float(string_in_list[string_in_list.index('Temp.')+2]) #TEMP ONLY

        def get_key_binary(string):
            k = string.strip().split()
            i=k.index("+")
            t=(k[i-1],k[i+2],float(k[i-2]),float(k[i+1])) #(salt1,salt2,frac1,frac2)
            T=float(k[k.index('Temp.')+2])
            return t+(T,) #(salt1,salt2,frac1,frac2,Temp)


        def find_data_in_txt(list_of_lines):
            expr = '\-{75,}'
            p = re.compile(expr)
            table_indices=[]
            for ind,line in enumerate(list_of_lines):
                if p.match(line.strip()):
                    table_indices.append(ind)
            string_data = list_of_lines[table_indices[0]+1:table_indices[1]]
            #print(string_data)
            def floator(val):
                try:
                    x=float(val)
                except ValueError:
                    x='>10000'
                return x
            return [[floator(val) for val in line.strip().split()] for line in string_data]

        #process values to pandas dataframe
        def data_lines_to_dataframe(list_of_lines,columns):
            return pd.DataFrame(list_of_lists,columns=columns)
        columns = ["m","c","wt fr salt","density (g/mL)","cP_mean","sig1 (eff)","sig2 (eff)","S(+)",
                    "Rational Act.Coef. y+-","Diff. Coeff. cm^2/s","Cond (mS) 2","t+(a)","t+(b)",
                    "dissoc (SI)","dissoc (TI)"]

        #cleaned = {get_temp_from_string(k):[s.strip for s in v] for k,v in d.items()}
        if len(self.electrolyte.salts)==1:
            self.data = {get_key_single(k):pd.DataFrame(find_data_in_txt(v),columns=columns) for k,v in d.items()}
        elif len(self.electrolyte.salts)==2:
            self.data = {get_key_binary(k):pd.DataFrame(find_data_in_txt(v),columns=columns) for k,v in d.items()}
        
        if surface_tension:
            st_columns=["m2","c2","Surface Tension (mN/m)", "Surface Tension / Viscosity (m/s)",
                "0.02 micron","0.05 micron","0.1 micron","0.2 micron","0.5 micron","1 micron","2 micron","5 micron","10 micron","20 micron"]
            #do the thing
            f = open(self.surface_tension_string,'r')
            lines = f.readlines()
            d={}
            for num1,line in enumerate(lines):
                if "Results" in line:
                    num2 = num1 + 1
                    arr = []
                    reading = True
                    while(reading==True):
                        if "Contact Angle" in lines[num2]:
                            reading = False
                        else:
                            arr.append(lines[num2])
                            num2 += 1
                    d[line] = arr
            #print(d.keys())
            if len(self.electrolyte.salts)==1:
                self.surface_tension_data = {get_key_single(k):pd.DataFrame(find_data_in_txt(v),columns=st_columns) for k,v in d.items()}
            elif len(self.electrolyte.salts)==2:
                self.surface_tension_data = {get_key_binary(k):pd.DataFrame(find_data_in_txt(v),columns=st_columns) for k,v in d.items()}
            
            for key in self.data.keys():
                st=self.surface_tension_data[key]
                self.data[key]["Surface Tension (mN/m)"]=st["Surface Tension (mN/m)"]

        self.data_processed=True


