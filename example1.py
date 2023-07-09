from src.htmlTranslatorImproved import htmlTranslator

#Put translation model (translate-ru_en-1_0.argosmodel) in folder with example
#Download model: https://www.argosopentech.com/argospm/index/

#Put model path, from_lang_code, to_lang_code
translator = htmlTranslator("translate-ru_en-1_0.argosmodel", "ru", "en")
#Open xml
translator.get_file("testDump.xml", "xml_wp")
#Translate
translator.translate()
#Save
translator.saveFile("testOut.xml")
