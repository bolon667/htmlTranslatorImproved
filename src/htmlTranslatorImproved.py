import argostranslate.package, argostranslate.translate
from argostranslate.tags import Tag, translate_tags
import bs4
from bs4 import BeautifulSoup
from bs4.element import NavigableString
import re



class htmlTranslator:
    input_text = ""
    from_lang = ""
    to_lang = ""
    translated_soup = None
    translated_code = ""

    NON_TRANSLATEABLE_TAGS = [
        "address",
        "applet",
        "audio",
        "canvas",
        "code",
        "embed",
        "script",
        "style",
        "time",
        "video",
    ]

    STRIP_TEXT_TAGS = [
        "strong",
        "a"
    ]
    def __init__(self, model_path, from_lang, to_lang):
        self.from_lang = from_lang
        self.to_lang = to_lang
        argostranslate.package.install_from_path(model_path)
        installed_languages = argostranslate.translate.get_installed_languages()
        # En = English
        cur_ind = 0
        print("Installed langs")
        for lang in installed_languages:
            print(lang)
        from_lang_ind = 0
        
        cant_pass = True
        for p in argostranslate.package.get_installed_packages():
            
            if p.from_code == from_lang:
                cant_pass = False
                break
            from_lang_ind += 1

        to_lang_ind = 0
        for p in argostranslate.package.get_installed_packages():
            if p.to_code == to_lang:
                cant_pass = False
                break
            to_lang_ind += 1
        if(cant_pass):
            print("Can't find a translation model")
        self.underlying_translation = installed_languages[from_lang_ind].get_translation(installed_languages[0])
    def get_text(self, text):
        self.input_text = text
    def get_file(self, path):
        with open(path, "r", encoding="utf-8") as f:
            self.input_text = f.read()
    def fix_spaces(self):
        #Not very reliable fix, but better then nothing
        pass
        self.translated_code = re.sub(r"(>)([^\s-])", r"\1 \2", self.translated_code)
    def itag_of_soup(self, soup):
        """Returns an argostranslate.tags.ITag tree from a BeautifulSoup object.

        Args:
            soup (bs4.element.Navigablestring or bs4.element.Tag): Beautiful Soup object

        Returns:
            argostranslate.tags.ITag: Argos Translate ITag tree
        """
        
        #No translation for tags from NON_TRANSLATEABLE_TAGS
        translateable = soup.name not in self.NON_TRANSLATEABLE_TAGS
        #No translation for comments (useful for wordpress)
        if isinstance(soup, bs4.element.Comment):
            to_return = Tag(soup, False)
            to_return.soup = soup
            return to_return
        
        if isinstance(soup, bs4.element.NavigableString):
            return str(soup)
       
        
        # translateable = True
        # to_return = Tag([self.itag_of_soup(content) for content in soup.contents], translateable)

        temp_arr = []
        for content in soup.contents:
            temp_arr.append(self.itag_of_soup(content))

        to_return = Tag(temp_arr, translateable)
        to_return.soup = soup
        return to_return
    def soup_of_itag(self, itag):
        """Returns a BeautifulSoup object from an Argos Translate ITag.

        Args:
            itag (argostranslate.tags.ITag): ITag object to convert to Soup

        Returns:
            bs4.elements.BeautifulSoup: BeautifulSoup object
        """
        if type(itag) == str:
            return bs4.element.NavigableString(itag)
        soup = itag.soup
        temp_arr = []
        for child in itag.children:
            temp_arr.append(self.soup_of_itag(child))
        soup.contents = temp_arr
        return soup
    def is_html_wp_page(self):
        return self.input_text.find("<!-- wp:") != -1
    def strip_text_in_tags(self, soup):
        pass
    def translate(self):
        soup = BeautifulSoup(self.input_text, "lxml")
        # soup = self.strip_text_in_tags(soup)
        itag = self.itag_of_soup(soup)
        translated_tag = translate_tags(self.underlying_translation, itag)
        # print(self.text_of_itag(translated_tag))
        self.translated_soup = self.soup_of_itag(translated_tag)
    def test(self):
        print(self.input_text)
    def comment_wp_fixer(self, translated_code):
        #----------------------
        #This func is DEAD, because i found a better solution, i just dont want to delete this function, i wasted too much time on it.
        #----------------------

        #Really crappy implementation of comment fixer.
        #But, who cares if it works
        print("Fixing comments")
        # MANUAL_FIXES = ["<!--wp:quote-->", "<!--/wp:quote-->"]

        #Fixing queotes
        # translated_code = re.sub(r"\s\/wp: &amp;e\s", f"<!--/wp:quote-->", translated_code)
        # translated_code = re.sub(r"\swp: &amp;quot;e\s", f"<!--wp:quote-->", translated_code)
        

        pattern1 = re.compile(r"\swp:[A-Za-z]+\s")
        pattern2 = re.compile(r"\s\/wp:[A-Za-z]+\s")
        
        comments1 = pattern1.findall(translated_code)
        comments1 = list(set(comments1))

        print(comments1)

        comments2 = pattern2.findall(translated_code)
        comments2 = list(set(comments2))

        #Fixing others
        #First with /
        for comment in comments2:
            comment = comment.strip()
            # if comment in MANUAL_FIXES:
                # continue
            
            translated_code = re.sub(r"\s" + comment + r"\s", f"<!--{comment}-->", translated_code)

        #Second witout /
        for comment in comments1:
            comment = comment.strip()
            # if comment in MANUAL_FIXES:
                # continue

            translated_code = re.sub(r"\s" + comment + r"\s", f"<!--{comment}-->", translated_code)

        #Can't fix image comment  (because it's not exists), so at least i will clean garbage
        # translated_code = translated_code.replace("♪", "")

        #Adds more spaces
        # translated_code = re.sub(r">\S", r"> ", translated_code)
        return translated_code

    def saveFile(self, path):
        self.translated_code = str(self.translated_soup)
        self.fix_spaces()
        # if self.is_html_wp_page():
            # pass
            # translated_code = self.comment_wp_fixer(translated_code)
            
        with open(path, "w", encoding="utf-8") as file:
            file.write(self.translated_code)


    # print(p.from)argostranslate.package.AvailablePackage
