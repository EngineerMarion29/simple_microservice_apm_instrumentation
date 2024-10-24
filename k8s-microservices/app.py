from flask import Flask, render_template, request, redirect, url_for
import requests
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.sampling import StaticSampler, Decision
from opentelemetry import trace
from coralogix_opentelemetry.trace.samplers import CoralogixTransactionSampler

# Authorization, CX-Application-Name and CX-Subsystem-Name are mandatory when calling the coralogix endpoint directly.
headers = ', '.join([
    f'Authorization=Bearer%20<apikey>',
    "CX-Application-Name=Instrumentation",
    "CX-Subsystem-Name=Instrumentation-APP",
])

# create a tracer provider
tracer_provider = TracerProvider(
    resource=Resource.create({
        SERVICE_NAME: 'Instrumentation-APP'
    }),
    sampler=CoralogixTransactionSampler(StaticSampler(Decision.RECORD_AND_SAMPLE))
)

# set up an OTLP exporter to send spans to coralogix directly
exporter = OTLPSpanExporter(
    endpoint='ingress.coralogix.com:443',
    headers=headers,
)

# set up a span processor to send spans to the exporter
span_processor = SimpleSpanProcessor(exporter)
tracer_provider.add_span_processor(span_processor)
trace.set_tracer_provider(tracer_provider)
instrumentor = FlaskInstrumentor()
tracer = trace.get_tracer_provider().get_tracer(__name__)

# initialise flask app
app = Flask(__name__)
instrumentor.instrument_app(app)  # Instrument the flask app

# Replace 'api-service' with the hostname or service name where the API is running
API_URL = 'http://api-service:5000/api/professionals'

@app.route('/')
def index():
    with tracer.start_as_current_span("index_request") as span:
        response = requests.get(API_URL)
        professionals = response.json()

        # Set trace attributes for monitoring
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.url", API_URL)
        span.set_attribute("http.status_code", response.status_code)

    return render_template('index.html', professionals=professionals)


@app.route('/add', methods=['POST'])
def add_professional():
    name = request.form['name']
    profession = request.form['profession']
    years_of_experience = request.form['years_of_experience']

    data = {
        'name': name,
        'profession': profession,
        'years_of_experience': years_of_experience
    }

    with tracer.start_as_current_span("add_professional_request") as span:
        response = requests.post(API_URL, json=data)

        # Set trace attributes for monitoring
        span.set_attribute("http.method", "POST")
        span.set_attribute("http.url", API_URL)
        span.set_attribute("http.status_code", response.status_code)

    return redirect(url_for('index'))


@app.route('/delete/<string:name>', methods=['POST'])
def delete_professional(name):
    delete_url = f'{API_URL}/{name}'

    with tracer.start_as_current_span("delete_professional_request") as span:
        response = requests.delete(delete_url)

        # Set trace attributes for monitoring
        span.set_attribute("http.method", "DELETE")
        span.set_attribute("http.url", delete_url)
        span.set_attribute("http.status_code", response.status_code)

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)

