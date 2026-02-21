"""Generate MealBuddy AWS architecture diagrams."""
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import ElasticBeanstalk, Fargate
from diagrams.aws.ml import Bedrock, SagemakerModel
from diagrams.aws.storage import S3
from diagrams.aws.management import Cloudformation
from diagrams.aws.database import Dynamodb
from diagrams.aws.network import CloudFront, ALB
from diagrams.aws.security import Cognito
from diagrams.aws.integration import SF
from diagrams.aws.management import Cloudwatch
from diagrams.aws.analytics import Opensearch
from diagrams.onprem.client import User

GRAPH = {
    "fontsize": "13",
    "bgcolor": "#f8f9fa",
    "pad": "1.0",
    "splines": "ortho",
    "nodesep": "0.8",
    "ranksep": "1.2",
}
CLUSTER = {"bgcolor": "#e8f4fd", "fontsize": "12", "fontcolor": "#1a1a2e"}
EDGE_STYLE = {"color": "#4a90d9", "fontsize": "10", "fontcolor": "#555555"}
DASHED = {"style": "dashed", "color": "#aaaaaa", "fontsize": "10"}

# ── Hackathon Demo ──────────────────────────────────────────────────────────
with Diagram(
    "MealBuddy — Hackathon Demo Architecture",
    filename="architecture_diagrams/architecture_hackathon",
    outformat="png",
    show=False,
    direction="LR",
    graph_attr=GRAPH,
):
    user = User("User")

    with Cluster("AWS  ap-southeast-2", graph_attr=CLUSTER):
        cfn = Cloudformation("CloudFormation")

        with Cluster("Elastic Beanstalk  t3.micro", graph_attr=CLUSTER):
            app = ElasticBeanstalk("Flask App\n+ Strands Agent")

        with Cluster("Amazon Bedrock", graph_attr=CLUSTER):
            claude = Bedrock("Claude 3 Haiku\nConversational AI")
            titan = SagemakerModel("Titan Embeddings V2\nSemantic Search")

        with Cluster("Amazon S3", graph_attr=CLUSTER):
            s3 = S3("mealbuddy-data\nrecipes · sessions\nembeddings · uploads")

    user >> Edge(label="HTTPS", **EDGE_STYLE) >> app
    app >> Edge(label="chat + tools", **EDGE_STYLE) >> claude
    app >> Edge(label="embed query", **EDGE_STYLE) >> titan
    app >> Edge(label="read / write", **EDGE_STYLE) >> s3
    titan >> Edge(label="cosine similarity\n(NumPy in-memory)", **EDGE_STYLE) >> s3
    cfn >> Edge(label="provisions", **DASHED) >> app
    cfn >> Edge(**DASHED) >> s3

# ── Future Production ───────────────────────────────────────────────────────
with Diagram(
    "MealBuddy — Future Production Architecture",
    filename="architecture_diagrams/architecture_future",
    outformat="png",
    show=False,
    direction="LR",
    graph_attr=GRAPH,
):
    user = User("Users")

    with Cluster("Edge", graph_attr=CLUSTER):
        cdn = CloudFront("CloudFront\n+ WAF")

    with Cluster("AWS  ap-southeast-2", graph_attr=CLUSTER):
        alb = ALB("Load Balancer")

        with Cluster("Compute", graph_attr=CLUSTER):
            fargate = Fargate("Fargate (ECS)\nAuto Scaling")

        with Cluster("Amazon Bedrock", graph_attr=CLUSTER):
            claude = Bedrock("Claude 3 Sonnet/Opus")
            titan = SagemakerModel("Titan Embeddings V2")

        with Cluster("Data", graph_attr=CLUSTER):
            dynamo = Dynamodb("DynamoDB\nprofiles · sessions")
            opensearch = Opensearch("OpenSearch Serverless\nvector store")
            s3 = S3("S3\nuploads · assets")

        with Cluster("Auth + Observability", graph_attr=CLUSTER):
            cognito = Cognito("Cognito")
            cw = Cloudwatch("CloudWatch\n+ X-Ray")

    user >> Edge(**EDGE_STYLE) >> cdn >> Edge(**EDGE_STYLE) >> alb >> Edge(**EDGE_STYLE) >> fargate
    fargate >> Edge(label="LLM", **EDGE_STYLE) >> claude
    fargate >> Edge(label="embed", **EDGE_STYLE) >> titan
    titan >> Edge(**EDGE_STYLE) >> opensearch
    fargate >> Edge(**EDGE_STYLE) >> dynamo
    fargate >> Edge(**EDGE_STYLE) >> s3
    fargate >> Edge(**EDGE_STYLE) >> cognito
    fargate >> Edge(**EDGE_STYLE) >> cw
