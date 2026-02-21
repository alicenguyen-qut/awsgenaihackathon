"""Generate MealBuddy AWS architecture diagrams."""
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import ElasticBeanstalk, Fargate
from diagrams.aws.ml import Bedrock, SagemakerModel
from diagrams.aws.storage import S3
from diagrams.aws.management import Cloudformation, Cloudwatch
from diagrams.aws.database import Dynamodb
from diagrams.aws.network import CloudFront, ALB
from diagrams.aws.security import Cognito
from diagrams.aws.analytics import AmazonOpensearchService as Opensearch
from diagrams.onprem.client import User

GRAPH = {
    "fontsize": "13",
    "bgcolor": "#f8f9fa",
    "pad": "1.0",
    "splines": "ortho",
    "nodesep": "0.9",
    "ranksep": "1.4",
}
CLUSTER = {"bgcolor": "#e8f4fd", "fontsize": "12", "fontcolor": "#1a1a2e"}

def e(label, dashed=False):
    """Edge with label close to the line."""
    return Edge(
        label=label,
        color="#aaaaaa" if dashed else "#4a90d9",
        style="dashed" if dashed else "solid",
        fontsize="9",
        fontcolor="#333333",
        labeldistance="0.5",
        labelangle="0",

    )

# ── Hackathon Demo ──────────────────────────────────────────────────────────
with Diagram(
    "MealBuddy — Hackathon Demo Architecture",
    filename="architecture_diagrams/architecture_hackathon",
    outformat="png",
    show=False,
    direction="LR",
    graph_attr=GRAPH,
):
    user = User("User\n(Browser)")

    with Cluster("AWS  ap-southeast-2", graph_attr=CLUSTER):
        cfn = Cloudformation("CloudFormation\nIaC · CI/CD")

        with Cluster("Elastic Beanstalk  t3.micro", graph_attr=CLUSTER):
            app = ElasticBeanstalk("Flask App\n+ Strands Agent\n(tool orchestration)")

        with Cluster("Amazon Bedrock", graph_attr=CLUSTER):
            claude = Bedrock("Claude 3 Haiku\nChat · Reasoning · Tools")
            titan = SagemakerModel("Titan Embeddings V2\nText → Vector")

        with Cluster("Amazon S3  (single bucket)", graph_attr=CLUSTER):
            s3 = S3("mealbuddy-data\nrecipes/  embeddings/\nsessions/  uploads/")

    user >> e("HTTPS request") >> app
    app >> e("invoke LLM\nchat + agentic tools") >> claude
    app >> Edge(xlabel="embed user query\n& uploaded docs", color="#4a90d9", fontsize="9", fontcolor="#333333") >> titan
    app >> e("read/write\nprofiles · meal plans\nchat history") >> s3
    titan >> e("load recipe embeddings\ncosine similarity (NumPy)") >> s3
    cfn >> e("provisions app\n+ IAM role", dashed=True) >> app
    cfn >> e("provisions bucket\n+ permissions", dashed=True) >> s3

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

    with Cluster("Edge Layer", graph_attr=CLUSTER):
        cdn = CloudFront("CloudFront + WAF\nCDN · DDoS protection\ngeo-restriction")

    with Cluster("AWS  ap-southeast-2", graph_attr=CLUSTER):
        alb = ALB("Application Load Balancer\nHTTPS termination")

        with Cluster("Compute", graph_attr=CLUSTER):
            fargate = Fargate("Fargate (ECS)\nAuto Scaling\nno server management")

        with Cluster("Amazon Bedrock", graph_attr=CLUSTER):
            claude = Bedrock("Claude 3 Sonnet/Opus\nupgraded reasoning")
            titan = SagemakerModel("Titan Embeddings V2\nText → Vector")

        with Cluster("Data Layer", graph_attr=CLUSTER):
            dynamo = Dynamodb("DynamoDB\nuser profiles · sessions\nTTL expiry")
            opensearch = Opensearch("OpenSearch Serverless\npersistent vector index\nscalable RAG")
            s3 = S3("S3\nuploads · recipe assets")

        with Cluster("Auth + Observability", graph_attr=CLUSTER):
            cognito = Cognito("Cognito\nMFA · JWT · social login")
            cw = Cloudwatch("CloudWatch + X-Ray\ndistributed tracing\nBedrock · tools · S3")

    user >> e("HTTPS") >> cdn >> e("cached / forwarded") >> alb >> e("route to container") >> fargate
    fargate >> e("invoke LLM\nmulti-day meal planning") >> claude
    fargate >> e("embed queries\n& documents") >> titan
    titan >> e("vector similarity search\npersistent index") >> opensearch
    fargate >> e("read/write\nprofiles · sessions") >> dynamo
    fargate >> e("store/retrieve\nuploads · assets") >> s3
    fargate >> e("authenticate\nJWT validation") >> cognito
    fargate >> e("logs · traces\nmetrics") >> cw
