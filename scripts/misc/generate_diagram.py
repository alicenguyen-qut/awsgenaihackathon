"""Generate MealBuddy AWS architecture diagrams."""
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import ElasticBeanstalk, Fargate
from diagrams.aws.ml import Bedrock, SagemakerModel
from diagrams.aws.storage import S3
from diagrams.aws.management import Cloudformation, Cloudwatch
from diagrams.aws.database import Dynamodb
from diagrams.aws.network import CloudFront, ALB
from diagrams.aws.security import IAMRole
from diagrams.onprem.inmemory import Redis
from diagrams.aws.analytics import AmazonOpensearchService as Opensearch
from diagrams.onprem.client import User

GRAPH = {
    "fontsize": "13",
    "bgcolor": "#f8f9fa",
    "pad": "1.5",
    "splines": "ortho",
    "nodesep": "1.8",
    "ranksep": "2.8",
}
CLUSTER = {"bgcolor": "#e8f4fd", "fontsize": "12", "fontcolor": "#1a1a2e", "margin": "24"}

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
    direction="TB",
    graph_attr=GRAPH,
):
    user = User("User\n(Browser)")

    with Cluster("AWS Cloud (ap-southeast-2)", graph_attr=CLUSTER):
        cfn = Cloudformation("CloudFormation\nIaC · CI/CD")
        role = IAMRole("EC2 Instance Role\nBedrock + S3 access")

        with Cluster("Elastic Beanstalk  t3.micro", graph_attr=CLUSTER):
            app = ElasticBeanstalk("Flask App\n+ Strands Agent")

        with Cluster("Amazon Bedrock", graph_attr=CLUSTER):
            claude = Bedrock("Claude 3 Haiku\nChat · Reasoning")
            titan = SagemakerModel("Titan Embeddings V2")

        with Cluster("Amazon S3", graph_attr=CLUSTER):
            s3 = S3("mealbuddy-data\nrecipes/ embeddings/\nsessions/ uploads/")

    # main flow
    user >> e("chat message") >> app
    user >> e("upload PDF/doc") >> app
    app >> e("invoke LLM") >> claude
    app >> e("embed uploaded doc") >> titan
    app >> e("embed query & docs") >> titan
    app >> e("store uploads\n+ read/write sessions") >> s3
    titan >> e("store doc embeddings\n+ load recipe embeddings") >> s3

    # infra / iam
    role >> e("attached to instance", dashed=True) >> app
    cfn >> e("deploys app + role", dashed=True) >> app
    cfn >> e("provisions bucket", dashed=True) >> s3

# ── Future Production ───────────────────────────────────────────────────────
with Diagram(
    "MealBuddy — Future Production Architecture",
    filename="architecture_diagrams/architecture_future",
    outformat="png",
    show=False,
    direction="TB",
    graph_attr=GRAPH,
):
    user = User("Users")

    with Cluster("Edge Layer", graph_attr=CLUSTER):
        cdn = CloudFront("CloudFront + WAF\nCDN · DDoS protection\ngeo-restriction")

    with Cluster("AWS Cloud (ap-southeast-2)", graph_attr=CLUSTER):
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

        with Cluster("Bedrock AgentCore", graph_attr=CLUSTER):
            agentcore = Bedrock("AgentCore\nIdentity · Tools · Memory\nRuntime · GenAI Observability")

        with Cluster("Observability", graph_attr=CLUSTER):
            cw = Cloudwatch("CloudWatch\nLogging + Monitoring")

        redis = Redis("Redis Cache\nRAG + LLM response caching")

    user >> e("HTTPS") >> cdn >> e("cached / forwarded") >> alb >> e("route to container") >> fargate
    fargate >> e("agent orchestration\nIdentity · Memory · Tools") >> agentcore
    agentcore >> e("invoke LLM\nmulti-step planning") >> claude
    agentcore >> e("embed queries\n& documents") >> titan
    titan >> e("vector similarity search\npersistent index") >> opensearch
    fargate >> e("read/write\nprofiles · sessions") >> dynamo
    fargate >> e("store/retrieve\nuploads · assets") >> s3
    fargate >> e("RAG + LLM\nresponse cache") >> redis
    fargate >> e("logs · metrics") >> cw
