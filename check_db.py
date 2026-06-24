import psycopg2

conn = psycopg2.connect("dbname='My_database' user='odoo' password='odoo' host='localhost'")
cur = conn.cursor()

# Set report.url to localhost to prevent wkhtmltopdf timeout
cur.execute("INSERT INTO ir_config_parameter (key, value) VALUES ('report.url', 'http://127.0.0.1:8069') ON CONFLICT (key) DO UPDATE SET value='http://127.0.0.1:8069'")
conn.commit()

print("Successfully set report.url to http://127.0.0.1:8069")

cur.close()
conn.close()
