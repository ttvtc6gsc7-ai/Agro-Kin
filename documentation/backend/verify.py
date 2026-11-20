"""Contrôles statiques du livrable, sans navigateur ni mutation du backend."""
from html.parser import HTMLParser
from pathlib import Path
from collections import Counter

class Inspect(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=[]
        self.anchors=[]
        self.assets=[]
    def handle_starttag(self, tag, attrs):
        values=dict(attrs)
        if 'id' in values: self.ids.append(values['id'])
        href=values.get('href','')
        if href.startswith('#'): self.anchors.append(href[1:])
        if tag=='script' and 'src' in values: self.assets.append(values['src'])
        if tag=='link' and values.get('rel')=='stylesheet': self.assets.append(href)

folder=Path(__file__).resolve().parent
content=(folder/'index.html').read_text(encoding='utf-8')
parser=Inspect()
parser.feed(content)
assert not (set(parser.anchors)-set(parser.ids)), 'Ancre manquante'
assert not [id for id,count in Counter(parser.ids).items() if count>1], 'Identifiant duplique'
assert all((folder/name).is_file() for name in parser.assets), 'Ressource absente'
assert 'TEST_STATUS_PLACEHOLDER' not in content
assert '33 tests' in content
assert 'django-insecure-' not in content
print('OK :',len(parser.ids),'identifiants uniques,',len(parser.anchors),'liens internes valides, ressources presentes, bilan integre, cle Django masquee.')
