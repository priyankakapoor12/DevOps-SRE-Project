import boto3
import logging
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class CloudWatchMetrics:
    """
    CloudWatch custom metrics client
    """

    def __init__(self):
        self.enabled = os.getenv("CLOUDWATCH_ENABLED", "false").lower() == "true"
        self.namespace = os.getenv("CLOUDWATCH_NAMESPACE", "TaskManager/Application")
        self.region = os.getenv("AWS_REGION", "us-east-1")

        if self.enabled:
            try:
                self.cloudwatch = boto3.client("cloudwatch", region_name=self.region)
                logger.info("CloudWatch metrics initialized")
            except Exception as e:
                logger.error(f"Failed to initialize CloudWatch client: {e}")
                self.enabled = False
        else:
            logger.info("CloudWatch metrics disabled")

    def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "Count",
        dimensions: Optional[dict] = None,
    ):
        """
        Send custom metric to CloudWatch
        """
        if not self.enabled:
            return

        try:
            metric_data = {
                "MetricName": metric_name,
                "Value": value,
                "Unit": unit,
                "Timestamp": datetime.utcnow(),
            }

            if dimensions:
                metric_data["Dimensions"] = [
                    {"Name": k, "Value": v} for k, v in dimensions.items()
                ]

            self.cloudwatch.put_metric_data(
                Namespace=self.namespace, MetricData=[metric_data]
            )

            logger.debug(f"CloudWatch metric sent: {metric_name}={value}")

        except Exception as e:
            logger.error(f"Failed to send CloudWatch metric: {e}")

    def increment_counter(self, metric_name: str, dimensions: Optional[dict] = None):
        """
        Increment a counter metric
        """
        self.put_metric(metric_name, 1.0, "Count", dimensions)


# Global metrics instance
metrics_client = CloudWatchMetrics()
