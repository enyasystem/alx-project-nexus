import sqlite3
con=sqlite3.connect('db.sqlite3')
cur=con.cursor()
cur.execute("PRAGMA table_info('catalog_product')")
rows=cur.fetchall()
print('columns:')
for r in rows:
    print(r)
con.close()
