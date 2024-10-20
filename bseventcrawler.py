import os
import requests
from lxml import html
import math
import datetime


TARGET_FILE = os.path.join(os.path.dirname(__file__), 'events.html')

# Header
with open(TARGET_FILE, 'w', encoding='utf-8') as file:
    file.write("""<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
  body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #121212;
    color: #e0e0e0;
  }
  .collapsible {
    background-color: #000;
    color: #ff4081;
    cursor: pointer;
    padding: 10px;
    width: 100%;
    border: none;
    text-align: left;
    outline: none;
    font-size: 18px;
  }
  .active, .collapsible:hover {
    background-color: #444;
  }
  .content {
    padding: 0 15px;
    display: block;
    overflow: hidden;
    background-color: #1e1e1e;
  }
  table {
    width: 100%;
    max-width: 800px;
    margin: 20px auto;
    border-collapse: collapse;
    background-color: #1e1e1e;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.7);
    table-layout: fixed;  /* Ermöglicht flexiblere Darstellung der Spalten */
  }
  th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #444;
    white-space: normal;  /* Normaler Textumbruch */
    overflow-wrap: break-word; /* Umbruch innerhalb der Zellen */
  }
  th {
    background-color: #000;
    color: #ff4081;
  }
  td:nth-child(4) { /* Preis-Spalte */
    width: 20%; /* Feste Breite für die Preisspalte, um Platz sicherzustellen */
    white-space: nowrap; /* Verhindert das Abschneiden des Preises */
  }
  tr:hover {
    background-color: #333;
  }
  a {
    color: #82b1ff;
    text-decoration: none;
  }
  a:hover {
    text-decoration: underline;
  }
</style>

  <script>
    document.addEventListener("DOMContentLoaded", function() {
      var coll = document.getElementsByClassName("collapsible");
      for (var i = 0; i < coll.length; i++) {
        coll[i].addEventListener("click", function() {
          this.classList.toggle("active");
          var content = this.nextElementSibling;
          if (content.style.display === "block") {
            content.style.display = "none";
          } else {
            content.style.display = "block";
          }
        });
      }
    });
  </script>
</head>
<body>
  <div class="container">
    <h1 style="text-align: center; color: #ff4081;">Backstage Events</h1>
""")

response = requests.get("https://backstage.eu/veranstaltungen/live.html")
response.raise_for_status()
tree = html.fromstring(response.content)

# Gesamtanzahl Elemente
total_items = tree.xpath("//div[contains(@class, 'amount-wrap')]/span[@class='toolbar-number'][3]/text()")

total_items = int(total_items[0]) if total_items else 1
items_per_page = 25  # Optionen: 5,10,15,20,25 

max_page = math.ceil(total_items / items_per_page)
#max_page = 1
months = {
    "Januar": "01", "Februar": "02", "März": "03", "April": "04", "Mai": "05", "Juni": "06",
    "Juli": "07", "August": "08", "September": "09", "Oktober": "10", "November": "11", "Dezember": "12"
}

grouped_data = {}
for page in range(1, max_page + 1):
    print(f"Getting page number {page}")

    try:
        response = requests.get(f"https://backstage.eu/veranstaltungen/live.html?product_list_limit={items_per_page}&p={page}")
        response.raise_for_status()
        tree = html.fromstring(response.content)
    except Exception as e:
        print(f"Error fetching page {page}: {e}")
        continue

    for i in range(1, items_per_page + 1):  
        try:
            print(f"Parsing item {i} on page {page}")
            title = tree.xpath(f"//ol/li[{i}]//a[@class='product-item-link']/text()")
            link = tree.xpath(f"//ol/li[{i}]//a[@class='product-item-link']/@href")
            
            print(f"Title for item {i}: {title}")
            print(f"Link for item {i}: {link}")
            day = tree.xpath(f"//ol/li[{i}]//strong[@class='product name product-item-name eventdate']/span[@class='day']/text()")
            month = tree.xpath(f"//ol/li[{i}]//strong[@class='product name product-item-name eventdate']/span[@class='month']/text()")
            year = tree.xpath(f"//ol/li[{i}]//strong[@class='product name product-item-name eventdate']/span[@class='year']/text()")
            genre = tree.xpath(f"//ol/li[{i}]//div[@class='product description product-item-description']/text()")

            # Alle Elemente aus List-Comprehension zamschreiben da Ergebnisse in mehreren Elementen vorliegen können
            title = "".join([t.strip() for t in title if t.strip()]).strip() if title else ""

            link = link[0].strip() if link else ""
            if day and month and year:
                day = day[0].strip().replace('.', '')
                month = months.get(month[0].strip(), "")
                year = year[0].strip()[-2:]
                datum = f"{day}.{month}.{year}"
                year_month_key = f"{year}-{month}"
            else:
                datum = ""
                year_month_key = "Unknown"
            genre = genre[0].replace("Learn More", "").strip() if genre else ""

            if link:
                try:
                    print(f"Fetching details for item {i} on page {page}")
                    detail_response = requests.get(link)
                    detail_response.raise_for_status()
                    detail_tree = html.fromstring(detail_response.content)
                    price = detail_tree.xpath("//span[@class='price']/text()")
                    price = price[0] if price else ""
                except Exception as e:
                    print(f"Error fetching details for item {i} on page {page}: {e}")
                    price = ""
            else:
                price = ""

            if title or datum or genre or price:
                if year_month_key not in grouped_data:
                    grouped_data[year_month_key] = []
                grouped_data[year_month_key].append(f"<tr><td>{datum}</td><td><a href='{link}'>{title}</a></td><td>{genre}</td><td>{price}</td></tr>")

        except Exception as e:
            print(f"Error processing item {i} on page {page}: {e}")

# Gruppierung schreiben
with open(TARGET_FILE, 'a', encoding='utf-8') as file:
    for year_month, rows in grouped_data.items():
        file.write(f"<button class='collapsible'>{list(months.keys())[list(months.values()).index(year_month.split('-')[1])]} {year_month.split('-')[0]}</button>")
        file.write("<div class='content'><table>")
        file.write("""
        <tr>
          <th>Datum</th>
          <th>Band</th>
          <th>Genre</th>
          <th>Preis</th>
        </tr>
        """)
        file.write("\n".join(rows))
        file.write("</table></div>")
    file.write("""  </div>
</body>
</html>""")
