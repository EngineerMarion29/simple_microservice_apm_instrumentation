from flask import Flask, jsonify, request
import mysql.connector
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.mysql import MySQLInstrumentor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.sampling import StaticSampler, Decision
from opentelemetry import trace
from coralogix_opentelemetry.trace.samplers import CoralogixTransactionSampler
from flask_cors import CORS

# Setup OpenTelemetry instrumentation
headers = ', '.join([
    f'Authorization=Bearer%20<apikey>',
    "CX-Application-Name=Instrumentation",
    "CX-Subsystem-Name=Instrumentation-API",
])

# Set up a tracer provider with Coralogix transaction sampler
tracer_provider = TracerProvider(
    resource=Resource.create({
        SERVICE_NAME: 'Instrumentation-API'
    }),
    sampler=CoralogixTransactionSampler(StaticSampler(Decision.RECORD_AND_SAMPLE))
)

# Set up an OTLP exporter to send spans to Coralogix directly
exporter = OTLPSpanExporter(
    endpoint='ingress.coralogix.com:443',
    headers=headers,
)

# Set up a span processor to send spans to the exporter
span_processor = SimpleSpanProcessor(exporter)
tracer_provider.add_span_processor(span_processor)
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer_provider().get_tracer(__name__)

# Initialize Flask app
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)  # Instrument the Flask app
MySQLInstrumentor().instrument()

# Enable CORS for all routes and origins
CORS(app)

def get_db_connection():
    return mysql.connector.connect(
        host='mysql',
        user='root',
        password='password',
        database='testdb'
    )

# API endpoint to retrieve professionals
@app.route('/api/professionals', methods=['GET'])
def get_professionals():
    with tracer.start_as_current_span("get_professionals_query", kind=trace.SpanKind.CLIENT) as span:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM professionals')
        professionals = cursor.fetchall()

        # Set span attributes for observability
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.connection_string", "mysql://root@mysql:3306/testdb")
        span.set_attribute("db.user", "root")
        span.set_attribute("db.name", "testdb")
        span.set_attribute("db.operation", "SELECT")
        span.set_attribute("db.statement", "SELECT * FROM professionals")
        span.set_attribute("net.peer.name", "mysql")
        span.set_attribute("net.peer.port", 3306)

        cursor.close()
        conn.close()

    return jsonify(professionals)

# API endpoint to add a new professional
@app.route('/api/professionals', methods=['POST'])
def add_professional():
    data = request.json
    name = data.get('name')
    profession = data.get('profession')
    years_of_experience = data.get('years_of_experience')

    with tracer.start_as_current_span("add_professional_query", kind=trace.SpanKind.CLIENT) as span:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO professionals (name, profession, years_of_experience) VALUES (%s, %s, %s)',
                       (name, profession, years_of_experience))
        conn.commit()

        # Set span attributes for observability
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.connection_string", "mysql://root@mysql:3306/testdb")
        span.set_attribute("db.user", "root")
        span.set_attribute("db.name", "testdb")
        span.set_attribute("db.operation", "INSERT")
        span.set_attribute("db.statement", "INSERT INTO professionals (name, profession, years_of_experience) VALUES (?, ?, ?)")
        span.set_attribute("net.peer.name", "mysql")
        span.set_attribute("net.peer.port", 3306)

        cursor.close()
        conn.close()

    return jsonify({'status': 'success'}), 201

# API endpoint to delete a professional
@app.route('/api/professionals/<string:name>', methods=['DELETE'])
def delete_professional(name):
    with tracer.start_as_current_span("delete_professional_query", kind=trace.SpanKind.CLIENT) as span:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM professionals WHERE name = %s', (name,))
        conn.commit()

        # Set span attributes for observability
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.connection_string", "mysql://root@mysql:3306/testdb")
        span.set_attribute("db.user", "root")
        span.set_attribute("db.name", "testdb")
        span.set_attribute("db.operation", "DELETE")
        span.set_attribute("db.statement", "DELETE FROM professionals WHERE name = ?")
        span.set_attribute("net.peer.name", "mysql")
        span.set_attribute("net.peer.port", 3306)

        cursor.close()
        conn.close()

    return jsonify({'status': 'success'}), 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

