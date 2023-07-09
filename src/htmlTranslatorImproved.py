import argostranslate.package, argostranslate.translate
from argostranslate.tags import Tag, translate_tags
import bs4
from bs4 import BeautifulSoup
from bs4.element import NavigableString
import re
import xml.etree.ElementTree as ET
from lxml import etree

# from pyquery import PyQuery as pq



class htmlTranslator:
    input_text = ""
    from_lang_code = ""
    to_lang_code = ""
    from_lang_name = ""
    to_lang_name = ""
    translated_soup = None
    translated_code = ""
    cur_type = ""

    NON_TRANSLATEABLE_TAGS_HTML = [
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

    NON_TRANSLATEABLE_TAGS_XML_WP = [
        "link",
        "pubDate",
        "creator",
        "guid",
        "post_id",
        "post_id_gmt",
        "post_modified"
        "post_modified_gmt",
        "comment_status",
        "ping_status",
        "status",
        "category",
        "is_stiky",
        "post_parent",
        "menu_order",
        "post_password",
        "post_meta"
    ]

    STRIP_TEXT_TAGS = [
        "strong",
        "a"
    ]
    def __init__(self, model_path, from_lang, to_lang):
        self.from_lang_code = from_lang
        self.to_lang_code = to_lang
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
                self.from_lang_name = p.from_name
                cant_pass = False
                break
            from_lang_ind += 1

        to_lang_ind = 0
        for p in argostranslate.package.get_installed_packages():
            if p.to_code == to_lang:
                self.to_lang_name = p.to_name
                cant_pass = False
                break
            to_lang_ind += 1
        if(cant_pass):
            print("Can't find a translation model")
        self.underlying_translation = installed_languages[from_lang_ind].get_translation(installed_languages[0])
    def get_text(self, text):
        self.input_text = text
    def get_file(self, path, cur_type="html"):
        self.cur_type = cur_type
        with open(path, "r", encoding="utf-8") as f:
            self.input_text = f.read()
    def fix_spaces(self):
        #Not very reliable fix, but better then nothing
        pass
        self.translated_code = re.sub(r"(>)([^\s-])", r"\1 \2", self.translated_code)
    def fix_spaces_init(self):
        self.input_text = re.sub(r"(>)([^\s-])", r"\1 \2", self.input_text)
    def itag_of_soup_xml_wp(self, soup):
        translateable = soup.name not in self.NON_TRANSLATEABLE_TAGS_HTML
        
        if isinstance(soup, bs4.element.Comment):
            # print(type(soup))
            to_return = Tag(soup, False)
            to_return.soup = soup
            return to_return
        
        if isinstance(soup, bs4.element.NavigableString):
            
            # print(type(soup))
            # print(soup)
            return str(soup)
       
        temp_arr = []
        for content in soup.contents:
            temp_arr.append(self.itag_of_soup_xml_wp(content))
        # print(type(soup))
        # print(soup)
        to_return = Tag(temp_arr, translateable)
        to_return.soup = soup
        return to_return
    
    def itag_of_soup(self, soup):
        translateable = soup.name not in self.NON_TRANSLATEABLE_TAGS_HTML
        if isinstance(soup, bs4.element.Comment):
            to_return = Tag(soup, False)
            to_return.soup = soup
            return to_return
        
        if isinstance(soup, bs4.element.NavigableString):
            return str(soup)
       
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
        # self.fix_spaces_init()
        self.translated_soup = BeautifulSoup(self.input_text, "html.parser")

        # self.translated_soup.prettify()
        match(self.cur_type):
            case "html":
                self.tranlsate_html()
            case "xml_wp":
                pass
                self.convert_wp_cdata_for_polylang()
                self.translate_xml_wp()
                
    def fix_parser_errors(self):
        print("Fixing html parser bugs")
        self.translated_code = re.sub("<link\/>(.+\S)", r"<link>\1</link>", self.translated_code)
        # items = self.translated_soup.findAll("item")
        # for item in items:
        #     for cont in item.contents:
        #         if cont.name == "link":
        #             print(cont)
    def gen_cat_name(self, cat_name):
        result = ""
        if(cat_name.find("-") != -1):
            result = cat_name[:cat_name.rfind("-")+1] + self.to_lang_code
        else:
            result = cat_name + "-" + self.to_lang_code
        return result
    def convert_wp_cdata_for_polylang(self):
        print("Converting cdata for polylang")
        #Changing language category
        lang_cat_arr = self.translated_soup.find_all("category", attrs={"domain": "language"})
        for lang_cat in lang_cat_arr:
            # lang_cat = self.translated_soup.find("category", attrs={"domain": "language"})
            lang_cat.contents[0] = bs4.element.CData(self.to_lang_name) #Changing Cdata
            lang_cat.attrs["nicename"] = self.to_lang_code

        #And Catergory name
        cat_name_arr = self.translated_soup.find_all("wp:category_nicename")
        for cat_name in cat_name_arr:
            # cat_name = self.translated_soup.find("wp:category_nicename")
           
            cat_name.contents[0] = bs4.element.CData(self.gen_cat_name(cat_name.contents[0])) #Changing Cdata
            
            cat_name2_arr = self.translated_soup.find_all("category", attrs={"domain": "category"})
            for cat_name2 in cat_name2_arr:
                cat_name2.attrs["nicename"] = self.gen_cat_name(cat_name2.attrs["nicename"])
        # self.translated_soup = soup

        item_arr = self.translated_soup.find_all("item")
        for item in item_arr:
            #Translating title
            title_elem = item.find("title")
            title_tr_text = argostranslate.translate.translate(str(title_elem.contents[0]), self.from_lang_code, self.to_lang_code)
            title_elem.contents[0] = bs4.element.CData(title_tr_text) #Changing Cdata

            #stripping wp_passw, to fix bug with " " (space symbol) password
            wp_passw = item.find("wp:post_password")
            wp_passw.contents[0] = bs4.element.CData(str(wp_passw.contents[0]).strip())

            
    def translate_xml_wp(self):
        print("Translating xml wp")
        items = self.translated_soup.findAll("item")
        amount_of_posts = len(items)
        print(f"{str(amount_of_posts)} posts in query")
        for item in items:
            elem = item.find("content:encoded")
            soup_html = BeautifulSoup(str(elem), "html5lib").body.findChild()
            itag = self.itag_of_soup(soup_html)
            # itag_of_soup_xml_wp
            translated_tag = translate_tags(self.underlying_translation, itag)
            temp_soup = self.soup_of_itag(translated_tag)

            elem.string.replace_with(temp_soup)
            elem.unwrap()
            amount_of_posts -= 1
            print(f"{str(amount_of_posts)} posts remained")


    def tranlsate_html(self):
        print("Translating html")
        soup = BeautifulSoup(self.input_text, "lxml")
        itag = self.itag_of_soup(soup)
        translated_tag = translate_tags(self.underlying_translation, itag)
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
        match(self.cur_type):
            case "html":
                self.translated_code = str(self.translated_soup)
                self.fix_spaces()
            case "xml_wp":
                self.translated_code = str(self.translated_soup)
                self.fix_parser_errors()
        # if self.is_html_wp_page():
            # pass
            # translated_code = self.comment_wp_fixer(translated_code)
            
        with open(path, "w", encoding="utf-8") as file:
            file.write(self.translated_code)
