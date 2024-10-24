from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

# opentelemetry imports
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.sampling import StaticSampler, Decision
from opentelemetry import trace
# coralogix sampler
from coralogix_opentelemetry.trace.samplers import CoralogixTransactionSampler
from opentelemetry.instrumentation.mysql import MySQLInstrumentor

# Authorization, CX-Application-Name and CX-Subsystem-Name are mandatory when calling the coralogix endpoint directly.
headers = ', '.join([
    f'Authorization=Bearer%20<apikey>',
    "CX-Application-Name=Instrumentation",
    "CX-Subsystem-Name=Instrumentation-App",
])

# create a tracer provider
tracer_provider = TracerProvider(
    resource=Resource.create({
        SERVICE_NAME: 'Instrumentation-App'
    }),
    sampler=CoralogixTransactionSampler(StaticSampler(Decision.RECORD_AND_SAMPLE)))

# set up an OTLP exporter to send spans to coralogix directly.
exporter = OTLPSpanExporter(
    endpoint='ingress.coralogix.com:443',
    headers=headers,
)

# set up a span processor to send spans to the exporter
span_processor = SimpleSpanProcessor(exporter)
# span_processor = ConsoleSpanExporter(exporter)

# add the span processor to the tracer provider
tracer_provider.add_span_processor(span_processor)
trace.set_tracer_provider(tracer_provider)
instrumentor = FlaskInstrumentor()
tracer = trace.get_tracer_provider().get_tracer(__name__)

# initialise flask app
app = Flask(__name__)
instrumentor.instrument_app(app)  # Instrument the flask app
MySQLInstrumentor().instrument()


def get_db_connection():
    return mysql.connector.connect(
        host='mysql',
        user='root',
        password='password',
        database='testdb'
    )

@app.route('/')
def index():
    with tracer.start_as_current_span("index_query", kind=trace.SpanKind.CLIENT) as span:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM professionals')
        professionals = cursor.fetchall()
        
        # Setting attributes
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
    return render_template('index.html', professionals=professionals)


@app.route('/add', methods=['POST'])
def add_professional():
    name = request.form['name']
    profession = request.form['profession']
    years_of_experience = request.form['years_of_experience']

    with tracer.start_as_current_span("insert_query", kind=trace.SpanKind.CLIENT) as span:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO professionals (name, profession, years_of_experience) VALUES (%s, %s, %s)',
                (name, profession, years_of_experience))
        conn.commit()

        # Setting attributes
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
    return redirect(url_for('index'))

@app.route('/delete/<string:name>', methods=['POST'])
def delete_professional(name):
    with tracer.start_as_current_span("delete_query", kind=trace.SpanKind.CLIENT) as span:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM professionals WHERE name = %s', (name,))
        conn.commit()

        # Setting attributes
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
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

