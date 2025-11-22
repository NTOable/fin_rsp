import psycopg2

connection = psycopg2.connect(
    dbname="",
    user="",
    password="",
    host="localhost"
)

query = connection.cursor()
query.execute("INSERT INTO logs (message) VALUES ('Hello from Python!')")
connection.commit()