from curses.ascii import HT
from requests_html import HTMLSession,HTML
from rich.console import Console

c = Console()
s = HTMLSession()
resp = s.get("http://carsandbids.com")
resp.html.render()
html = HTML(html=resp.text)
c.print(html.full_text)
# print(resp)