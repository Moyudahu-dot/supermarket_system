import psycopg2

def get_connection():
    return psycopg2.connect(
        dbname="supermarket",
        user="gaussdb",
        password="Enmo@123",
        host="localhost",
        port="5432"
    )