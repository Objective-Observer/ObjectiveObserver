from random import randint
from random import random
from random import seed
import math
import sys

def stdev(data):                    # standard deviation
    avg = sum(data)/float(len(data))
    stq=0
    for item in data:
        stq+=(item-avg)*(item-avg)
    return math.sqrt(stq)

def correlation(vec1,vec2):
    cov=0
    avg1 = sum(vec1)/float(len(vec1))
    avg2 = sum(vec2)/float(len(vec2))
    if len(vec1)==len(vec2):
        for i in range(len(vec1)):
            cov=cov+(vec1[i]-avg1)*(vec2[i]-avg2)
        devmult = stdev(vec1)*stdev(vec2)
        if devmult==0: return 0
        else: return cov/devmult
    else: print ("ERROR in correlation: length of vectors are not equal")

class Param:                                # read model parameters from file
    def __init__(self,pfilename):
        self.name="test"
        self.population = 1                 # number of people
        self.contentcount = 1               # number of contents
        self.opinions = 5                   # number of opinions
        self.neutral = 0.2                  # threshold for approve-disapprove values
        self.iteration = 1                  # how many tries to generate 1 person
        self.propertycount = 0              # number of properties including randomness
        self.approve = []                   # target: probabiolity of approvel őper property
        self.disapprove = []                # target: probability of disapproval per property
        self.correl = []                    # correlation targets for property x with all properties > x
        self.capprove = []                  # content target: approve
        self.cdisapprove = []               # content tartget: disapprove
        self.ccorrel = []                   # content target: correlations
        try:
            self.testf = open(pfilename, "r")   # open parameter file
        except:
            print ("ERROR: input file coiuld not be opened: "+pfilename)
        self.read_test()                    # read parameters from input file

# parameter file conventions:
# 1. support and oppose go to approve and disapprove, valiues are between 0 and 1
# 2. correlation values between -1 and 1, separated with comma (,)
# 3. correlation list must have at least 1 item, max an item for all properties to come, default is zero
# 4. first property is objectivity, last is randomness ( for content as well)
# 5. content has the same number of properties as people
# 6. a property mustz have a support and oppose row, then followed by correlation row, except for the last one
# 7. for contents use the keys content_supp, content_opp, content_corr

    def read_test(self):                            # read the parameter file
        pc = 0  ; cc = 0                            # property counter for people and content
        for line in self.testf:
            i = 0; value = 0; epos = -1; cpos = -1
            while i < len(line):                    # all characters in this row
                if "=" in line[i:i + 1]: epos = i   # after = we have the parameter value
                if "//" in line[i:i + 2]: cpos = i   # after // we have comment
                i+=1
            if epos>-1:
                if cpos>-1:
                    value = line[epos+1:cpos].strip()
                else: value = line[epos+1:i].strip()
                try:
                    if "name" in line: self.name=value      # find parameter keyword and apply the value from this row
                    if "population" in line: self.population=int(value)
                    if "contentcount" in line: self.contentcount=int(value)
                    if "opinions" in line: self.opinions=int(value)
                    if "iteration" in line: self.iteration=int(value)
                    if "neutral" in line: self.neutral=float(value)
                    if "propertycount" in line: self.propertycount=int(value)
                    if "support" in line:
                        pc=pc+1                             # count properties found
                        self.approve.append(float(value))   # next approve value added
                    if "oppose" in line: self.disapprove.append(float(value))
                    if "correlation" in line:
                        corr=value.split(","); corrs=[]     # correlations miust be separated by ,
                        for _ in range(pc): corrs.append(0)  # filling zeros for diagonal and lower half of matrix
                        for coritem in corr:
                            corrs.append(float(coritem))    # add next correlation
                        self.correl.append(corrs)
                    if "content_supp" in line:              # reading content parameters
                        cc=cc+1                             # count content parameters
                        self.capprove.append(float(value))
                    if "content_opp" in line: self.cdisapprove.append(float(value))
                    if "content_corr" in line:
                        corr=value.split(","); corrs=[]     # correlations miust be separated by ,
                        for _ in range(cc): corrs.append(0)  # filling zeros for diagonal and lower half of matrix
                        for coritem in corr:
                            corrs.append(float(coritem))    # add next correlation
                        self.ccorrel.append(corrs)          # content correlations
                except:
                    print("ERROR: incorrect input fomat. Line: "+line)
        self.correct_correlation()                          # if not enough correlations provided, add zeros
        if pc != self.propertycount: print ("ERROR: propertycount does not match people properties found. Values: "+str(self.propertycount)+" "+str(pc))
        if cc != self.propertycount: print ("ERROR: propertycount does not match content properties found. Values: "+str(self.propertycount)+" "+str(pc))

    def correct_correlation(self):                          # if not enough correlations provided, zeros will be added
        for i,cor in enumerate(self.correl):
            for _ in range(self.propertycount-len(cor)):
                self.correl[i].append(0)                    # add default zero to make list complete
        for i,cor in enumerate(self.ccorrel):               # for content
            for _ in range(self.propertycount-len(cor)):
                self.ccorrel[i].append(0)                    # add default zero to make list complete

class Opinion:                                              # result of simulation: opinion about contents
    def __init__(self):
        self.opinion = []                                   # OUTPUT: list of {} maps, indexed by people, content mapped to opinion
        self.oprogress = 0

    def generate_opinion(self):
        for _ in range(params.population): self.opinion.append({})   # all people get an empty map
        opc=0; opctry=0
        while opc<params.opinions and opctry<10*params.opinions:     # opinion target met, or 10 times more tried
            peo = randint(1,params.population)-1            # which person
            cont = randint(1,params.contentcount)-1         # which content
            new=self.make_opin(peo,cont)                    # create opinion
            if new==1: opc+=1                               # count new opinions
            opctry+=1
        self.oprogress=opc

    def make_opin(self,peo,cont):                           # create opinion of given person for given content
        new=0
        if cont not in self.opinion[peo]:                   # this person has not yet opinion for this content
            new=1; opsum=0; wsum=0
            for prop in range(0,params.propertycount-1):    # all properties except the last one
                opsum = opsum + peop.propval[peo][prop]*peop.cpropval[cont][prop]   # summarize opinion pieces
                wsum = wsum + abs(peop.propval[peo][prop])    # sum of weights
            randomvalue = random()                          # random contribution to opinion (positive number)
            opsum = opsum + peop.propval[peo][prop+1]*randomvalue   # due to the weight this could be bidirectional or not
            wsum = wsum + abs(peop.propval[peo][prop+1])
            self.opinion[peo][cont] = opsum/wsum            # opinion scaled between -1 and 1
        return new                                          # indicate if new opinion was added

class Simulate:                                             # generate people and contents
    def __init__(self):
        self.progress = 0
        self.cprogress = 0
        self.propyes=[]                                     # propyes[x][y] x-th persons y-th property 1 (approve) or 0 (neutral or disapp)
        self.propno=[]                                      # 1 means disapprove (oppose)
        self.propval=[]                                     # random property value -1 ... +1; used for propyes and propno
# a property has 3 numbers: propval is the random value, based on it we get: propyes shows approval (support), propno shows disapproval
        self.cpropyes=[]                                    # propyes[x][y] x-th content y-th property 1 (approve) or 0 (neutral or disapp)
        self.cpropno=[]                                     # contet: 1 means disapprove (oppose)
        self.cpropval=[]                                    # content random property value -1 ... +1; used for propyes and propno
        self.mult=3                                         # multiplier used to make random weight more important

    def random_property(self):                              # set properties of a person (content)
        prop=0; props=[]                                    # props[prop] is the property approval vector for one person
        while prop<params.propertycount:                    # all properties
            yes=2*random()-1                                # number -1 ...+1
            props.append(yes)
            prop+=1
        return props[:]

    def get_best(self,diffvar):                             # get the smallest difference from targets
        sumdif=[]
        for seldi in diffvar:                               # over all properties
            if sumdif==[]: sumdif=seldi[:]                  # diff we have so far
            else:
                minix=0
                for i in range(len(seldi)):                 # over all variations
                    sumdif[i]=sumdif[i]+seldi[i]            # total difference for this variation
                    if sumdif[i]<sumdif[minix]: minix=i     # store the minimum
        return minix                                        # which variation has smallest total difference from targets

    def set_yes(self,props):                                # convert property values to approval values
        pyes=[]
        for pval in props:
            if pval>(0+params.neutral):                     # property value positive, over tolerance
                pyes.append(1)
            else:
                pyes.append(0)
        return pyes[:]

    def set_no(self,props):                                 # convert property values to disapproval values
        pyes=[]
        for pval in props:
            if pval<(0-params.neutral):                     # property value negative, over tolerance
                pyes.append(1)
            else:
                pyes.append(0)
        return pyes[:]
    
    def diff_approve(self,which,people,props):              # get difference from approve target
        pyes=self.set_yes(props)
        avgnew=(self.get_avg(which,self.progress,self.propyes,self.propno,1)*people+pyes[which])/float(people+1)
        diff=abs(avgnew-params.approve[which])              # difference from target value
        if (which==params.propertycount-1):                 # last property: randomness
            diff=self.mult*abs(avgnew-params.approve[which])   # difference multiplied so that it gets more weight
        return diff

    def diff_disapprove(self,which,people,props):           # get difference from disapprove target
        pno=self.set_no(props)
        avgnew=(self.get_avg(which,self.progress,self.propyes,self.propno,1)*people+pno[which])/float(people+1)
        diff=abs(avgnew-params.disapprove[which])           # difference from target value
        if (which==params.propertycount-1):                 # last property: randomness
            diff=self.mult*abs(avgnew-params.disapprove[which])   # difference multiplied so that it gets more weight
        return diff
    
    def diff_corr(self,which,props):                        # calculate correlation difference for property which
        diff = 0; towh = which+1
        while towh < params.propertycount:                  # correlations up to last property
            target=params.correl[which][towh]               # correlation target for the pair which,towh
            v0=[];v1=[]                                     # current pair of value vectors
            for peov in self.propval:                       # all people
                v0.append(peov[which])
                v1.append(peov[towh])
            v0.append(props[which])                         # current variation value
            v1.append(props[towh])
            corr = correlation(v0,v1)
            diff = diff + abs(target-corr)
            towh+=1
        return diff

    def select_pset(self,people,pvals):                     # select the property vector from variations in pvals
        diffvar=[]                                          # remember the difference for all variations, by property
        for which in range(params.propertycount):           # which property to consider
            seldiff=[]                                      # remember diffas from target
            for props in pvals:                             # take all variations
                diff1 = self.diff_approve(which,people,props)       # params.approve: calculate diff from target
                diff2 = self.diff_disapprove(which,people,props)    # params.disapprove: calculate diff from target
                diff3 = self.diff_corr(which,props)                 # difference sum from correlation targets
                seldiff.append(diff1+diff2+diff3)           # summed diff for thsi property, over variations
            diffvar.append(seldiff)                         # summed diff per property per variation
        minix = self.get_best(diffvar)                      # summarize diff over properties and get the smallest
        return pvals[minix]                                 # the selected property vector from the vafriations

    def generate_people(self):                              # generate people or contents with properties matching targets
        people=0;
        while people<params.population:                     # make all people
            pvals=[]                                        # variations vector for this person
            for _ in range(params.iteration):               # required number of variations
                props=self.random_property()                # a variation with random properties
                pvals.append(props)                         # add to list of variations
            selected = self.select_pset(people,pvals)       # select one from the variations
            self.propval.append(selected)                   # add selected values to list of people-properties
            self.propyes.append(self.set_yes(selected))     # convert property values to approval values
            self.propno.append(self.set_no(selected))       # convert property values to disapproval values
            self.progress=people                            # how many people are generated so far
            people+=1                                       # next person
        self.progress=people
        
    def generate_content(self):                             # generate content by replacing parameters and calling people generation
        self.cprogress=0
        s_progress=self.progress                    # save people variables
        s_propyes=self.propyes[:]
        s_propno=self.propno[:]
        s_propval=self.propval[:]
        s_population=params.population
        s_approve=params.approve[:]
        s_disapprove=params.disapprove[:]
        s_correl=params.correl[:]

        # change parameters for content generation
        self.progress=0;self.propyes=[];self.propno=[];self.propval=[]
        params.population=params.contentcount
        params.approve=params.capprove[:]        
        params.disapprove=params.cdisapprove[:]
        params.correl=params.ccorrel[:]
        self.generate_people()                      # perform content generation by calling people generation

        self.cprogress=self.progress                # contents done. set content variables.
        self.cpropyes=self.propyes[:]
        self.cpropno=self.propno[:]
        self.cpropval=self.propval[:]

        self.progress=s_progress                    # set back people variables to ssaved values
        self.propyes=s_propyes[:]
        self.propno=s_propno[:]
        self.propval=s_propval[:]
        params.population=s_population
        params.approve=s_approve[:]
        params.disapprove=s_disapprove[:]
        params.correl=s_correl[:]

    def get_avg(self,which,count,yesdata,nodata,yes):   # calculate average for the property which
        sum=0
        if yes==1 and self.progress>0:                  # yes==1 means approve, 0 means disapprove
            for personyes in yesdata:
                sum=sum+personyes[which]
            return sum/float(count)                     # average approve = yes values per number of people
        if yes==0 and self.progress>0:
            for personno in nodata:
                sum=sum+personno[which]
            return sum/float(count)
        return 0

    def get_corr(self,which,data,towh):                 # calculate correlation
        v0=[];v1=[]
        for peov in data:                               # over people
            v0.append(peov[which])                      # property which
            v1.append(peov[towh])                       # property towh
        return correlation(v0,v1)                       # correlation of which,towh pair

    def all_averages(self,avgyes,avgno,progress,propyes,propno):
        for which in range(params.propertycount):
            avgyes.append(self.get_avg(which,progress,propyes,propno,1))    # averages for approve
            avgno.append(self.get_avg(which,progress,propyes,propno,0))    # averages for disapprove

    def print_result(self,approve,avgyes,disapprove,avgno,propval,correl):
        for pro in range(params.propertycount):
            print ("property "+str(pro)+"  support target = "+str(approve[pro])+" support="+str(avgyes[pro]))
            print ("property "+str(pro)+"   oppose target = "+str(disapprove[pro])+"  oppose="+str(avgno[pro]))
            for towh in range(pro+1,params.propertycount):
                thiscorr = self.get_corr(pro,propval,towh)
                print("Correlation target for "+str(pro)+","+str(towh)+" = "+str(correl[pro][towh])+"  correlation="+str(int(100*thiscorr)/float(100)))

    def assess_simulation(self):                # assess results, differences between targets and actuals
        mess ="Assess "+params.name+" Target population:"+str(params.population)+" contents:"+str(params.contentcount)+" opinions:"+str(params.opinions)
        mess = mess+" iteration="+str(params.iteration)+" neutral="+str(params.neutral)
        print (mess)
        print ("PEOPLE actual: "+str(self.progress))
        avgyes=[]; avgno=[]
        self.all_averages(avgyes,avgno,self.progress,self.propyes,self.propno)
        self.print_result(params.approve,avgyes,params.disapprove,avgno,self.propval,params.correl)   # prrint people results
        print ("CONTENT actual: "+str(self.cprogress))
        avgyes=[]; avgno=[]
        self.all_averages(avgyes,avgno,self.cprogress,self.cpropyes,self.cpropno)
        self.print_result(params.capprove,avgyes,params.cdisapprove,avgno,self.cpropval,params.ccorrel)   # prrint content results
        print ("OPINION actual: "+str(opin.oprogress))
        samecon=0
        for pp in range(params.population):
            randomp = randint(1,params.population)-1
            vst=""
            for val in self.propval[pp]: vst=vst+str(int(100*val)/float(100))+" "
            print ("Person="+str(pp)+" values="+vst)       # print person properties
            for opc in opin.opinion[pp]:                    # this person's opinions
                if opc in opin.opinion[randomp]: samecon+=1     # random person has opinion on same content
                vst=""
                for val in self.cpropval[opc]: vst=vst+str(int(100*val)/float(100))+" "   # to be able to print content properties
                print ("     content= "+str(opc)+" "+vst+" opinion="+str(int(100*opin.opinion[pp][opc])/float(100)))
        print ("Opinion number on same content for one person: "+str(int(samecon/params.population)))

#seed(1)                        # to make random numbers repeating in each run
if len(sys.argv) == 2:
    pfile = sys.argv[1]
    params = Param(pfile)
    peop = Simulate()           # instance for simulated people and contents
    opin = Opinion()            # instance for opinions
    peop.generate_people()      # generate people
    peop.generate_content()     # generate contents
    opin.generate_opinion()     # generate opinions         
    peop.assess_simulation()    # print results
else: print("Parameter file name missing or too many arguments. 1 argument needed!!")
        