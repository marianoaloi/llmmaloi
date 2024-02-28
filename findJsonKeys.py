

class FindJsonKey:
    def __init__(self) -> None:
        pass
    verifykeys=set()

    def makeDecision(self,valitem,prefix:str=""):    
        if(type(valitem) == list):
            self.workList(valitem,prefix)
        elif(type(valitem) == dict):
            self.findKeys(valitem,prefix)

    def workList(self,val:list,prefix:str=""):
        for valitem in val:
            self.makeDecision(valitem,f"{prefix}$L$\"][\"")

    def findKeys(self,obj:dict,prefix:str=""):    
        for k in obj.keys():
            self.verifykeys.add(f"{prefix}{k}")
            val = obj[k]
            self.makeDecision(val,f"{prefix}{k}\"][\"")
    def keys(self):
        keys=list(self.verifykeys)
        keys.sort()
        return "\n".join([f"{key}\"]" for key in keys])
    
        