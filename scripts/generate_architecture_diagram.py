"""Generate MealBuddy AWS architecture diagram."""
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import ElasticBeanstalk
from diagrams.aws.ml import Bedrock, SagemakerModel
from diagrams.aws.storage import S3
from diagrams.aws.management import Cloudformation
from diagrams.onprem.client import User
from diagrams.onprem.network import Internet

with Diagram(
    "MealBuddy Architecture",
    filename="architecture",
    outformat="png",
    show=False,
    direction="LR",
    graph_attr={"fontsize": "14", "bgcolor": "white", "pad": "0.5"},
):
    user = User("User\n(Browser)")

    with Cluster("AWS (ap-southeast-2)"):
        cfn = Cloudformation("CloudFormation\n(IaC)")

        with Cluster("Elastic Beanstalk\n(t3.micro EC2)"):
            app = ElasticBeanstalk("Flask App\n+ Strands Agent")

        with Cluster("Amazon Bedrock"):
            claude = Bedrock("Claude 3 Haiku\nConversational AI")
            titan = SagemakerModel("Titan Embeddings V2\nSemantic Search")

        with Cluster("Amazon S3"):
            s3 = S3("mealbuddy-bucket")

    user >> Edge(label="HTTPS") >> app
    app >> Edge(label="chat / tools") >> claude
    app >> Edge(label="embed query") >> titan
    app >> Edge(label="read/write\nsessions, uploads") >> s3
    titan >> Edge(label="compare embeddings") >> s3
    cfn >> Edge(style="dashed", label="provisions") >> app
    cfn >> Edge(style="dashed") >> s3
