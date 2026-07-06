import psycopg2
conn = psycopg2.connect('dbname=My_database user=openpg password=openpgpwd')
cur = conn.cursor()
cur.execute("SELECT key, value FROM ir_config_parameter WHERE key LIKE 'license.%'")
for row in cur.fetchall(): print(row)
