import re
import ftfy


def populate(obj:dict,result:dict):
    for fieldName in obj.keys():
        valitem=obj[fieldName]
        if(type(valitem) == str):
            result[fieldName] = cleanText(valitem)
            
        elif(type(valitem) == list):
            result[fieldName] = [populate(litem,litem) for litem in valitem]
        elif(type(valitem) == dict):
            result[fieldName] = populate(valitem,valitem)
        else:
            result[fieldName] = valitem
    return result
            
def cleanText(fieldText:str)->str:
    if(not fieldText):
        return ""
    
    fieldText=fieldText.replace("\n"," ")
    return ftfy.fix_text(fieldText)            
