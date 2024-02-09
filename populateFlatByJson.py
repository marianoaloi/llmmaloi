import ftfy


def populate(obj:dict,result:dict):
    for fieldName in obj.keys():
        if(type(obj[fieldName]) == str):
            result[fieldName] = ftfy.fix_text(obj[fieldName].replace("\n"," "))
        else:
            result[fieldName] = obj[fieldName]