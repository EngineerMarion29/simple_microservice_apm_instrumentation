from flask import Flask, render_template
import mysql.connector
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.mysql import MySQLInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
import os

# Initialize Flask app
app = Flask(__name__)

# Initialize OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Instrument Flask
FlaskInstrumentor().instrument_app(app)

# Instrument MySQL
MySQLInstrumentor().instrument()

# Set up the OTLP exporter
otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
    headers={"Authorization": os.getenv("OTEL_EXPORTER_OTLP_HEADERS")}
)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

def get_db_connection():
    return mysql.connector.connect(
        host='mysql',
        user='root',
        password='password',
        database='testdb'
    )

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM professionals')
    professionals = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', professionals=professionals)

if __name__ == '__main__':
    app.run(debug=True)

